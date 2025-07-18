

import os
import re
import time
import json
from io import BytesIO
from pathlib import Path

import pdfplumber
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

# CONFIG
BASE = Path(__file__).parent
UPLOAD_DIR = BASE / "uploads";      UPLOAD_DIR.mkdir(exist_ok=True)
FILLED_DIR = BASE / "filled_forms"; FILLED_DIR.mkdir(exist_ok=True)
TEMPLATE   = BASE / "form_templates" / "f1040.pdf"
ALLOWED    = {"pdf"}

STD_DED = {
    "single": 13850, "married_joint": 27700,
    "married_separate": 13850, "head_of_household": 20800
}

BRACKETS = {
    "single": [
        (0, .10), (11950, .12), (48575, .22), (109525, .24),
        (195850, .32), (243725, .35), (609350, .37)
    ],
    "married_joint": [
        (0, .10), (23900, .12), (97150, .22), (182800, .24),
        (195850, .32), (243725, .35), (609350, .37)
    ],
    "married_separate": [
        (0, .10), (11950, .12), (48575, .22), (91400, .24),
        (97825, .32), (121862, .35), (304675, .37)
    ],
    "head_of_household": [
        (0, .10), (17050, .12), (68600, .22), (110650, .24),
        (190800, .32), (231250, .35), (609350, .37)
    ]
}

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

# --- VALIDATION ---
def validate_personal_info(form):
    errors = []

    def is_name(val): return bool(val and re.match(r"^[A-Za-z .'-]+$", val))
    def is_ssn(val):  return bool(val and re.match(r"^\d{9}$", val))
    def is_state(val): return bool(val and re.match(r"^[A-Z]{2}$", val.upper()))
    def is_zip(val): return bool(val and re.match(r"^\d{5}$", val))
    
    # Basic fields
    if not is_name(form.get("first_name")): errors.append("First Name")
    if not is_name(form.get("last_name")): errors.append("Last Name")
    if not is_ssn(form.get("ssn", "").replace("-", "")): errors.append("SSN")
    if not form.get("address_line1"): errors.append("Street Address")
    if not is_name(form.get("city")): errors.append("City")
    if not is_state(form.get("state", "")): errors.append("State (2 letters)")
    if not is_zip(form.get("zip_code", "")): errors.append("ZIP (5 digits)")
    if not form.get("taxpayer_signature"): errors.append("Signature Name")
    if not form.get("signature_date"): errors.append("Signature Date")
    
    # Spouse (required if married_joint)
    if form.get("filing_status") == "married_joint":
        if not is_name(form.get("spouse_first_name")): errors.append("Spouse First Name")
        if not is_name(form.get("spouse_last_name")): errors.append("Spouse Last Name")
        if not is_ssn(form.get("spouse_ssn", "").replace("-", "")): errors.append("Spouse SSN")
    
    # Dependents (must be a list if present)
    dependents = form.get("dependents", "[]")
    try:
        dep_list = json.loads(dependents)
        if not isinstance(dep_list, list): errors.append("Dependents (not a list)")
    except Exception:
        errors.append("Dependents (invalid JSON)")
    return errors

# --- HELPERS ---
def allowed_file(fn):
    return "." in fn and fn.rsplit(".",1)[1].lower() in ALLOWED

def group_lines(words, tol=3):
    lines = []
    for w in sorted(words, key=lambda x: x['top']):
        for L in lines:
            if abs(w['top'] - L[0]['top']) <= tol:
                L.append(w)
                break
        else:
            lines.append([w])
    return [sorted(L, key=lambda x: x['x0']) for L in lines]

def find_w2_vals(path):
    with pdfplumber.open(path) as pdf:
        lines = group_lines(pdf.pages[0].extract_words(use_text_flow=True))
        for i, ln in enumerate(lines):
            txt = " ".join(w['text'].lower() for w in ln)
            if "wages" in txt and "other compensation" in txt:
                nxt = lines[i+1] if i+1<len(lines) else []
                nums = [w for w in nxt if re.match(r"^[\d,]+\.\d{2}$",w['text'])]
                if len(nums) >= 2:
                    return (
                        float(nums[0]['text'].replace(",","")),
                        float(nums[1]['text'].replace(",",""))
                    )
    return 0.0, 0.0

def find_1099int(path):
    with pdfplumber.open(path) as pdf:
        lines = group_lines(pdf.pages[0].extract_words(use_text_flow=True))
        for i, ln in enumerate(lines):
            combined = " ".join(w['text'].lower() for w in ln)
            if re.search(r'\b1\b.*interest\s+income', combined):
                for j in range(i, i+3):
                    cands = [w for w in lines[j] if re.match(r'^[\$]?[\d,]+\.\d{2}$', w['text'])]
                    if cands:
                        tok = max(cands, key=lambda w: w['x0'])
                        return float(tok['text'].lstrip('$').replace(",",""))
    return 0.0

def find_1099nec(path):
    with pdfplumber.open(path) as pdf:
        lines = group_lines(pdf.pages[0].extract_words(use_text_flow=True))
        for i, ln in enumerate(lines):
            combined = " ".join(w['text'].lower() for w in ln)
            if "nonemployee compensation" in combined:
                for j in range(i, i+3):
                    cands = [w for w in lines[j] if re.match(r'^[\$]?[\d,]+\.\d{2}$', w['text'])]
                    if cands:
                        tok = max(cands, key=lambda w: w['x0'])
                        return float(tok['text'].lstrip('$').replace(",",""))
    return 0.0

def parse_form(path):
    hdr = (pdfplumber.open(path).pages[0].extract_text() or "").lower()
    if '1099-int' in hdr:
        return {'type': '1099-int', 'interest': find_1099int(path)}
    if '1099-nec' in hdr:
        return {'type': '1099-nec', 'nonemployee_comp': find_1099nec(path)}
    w, wt = find_w2_vals(path)
    return {'type': 'w2', 'wages': w, 'withheld': wt}

def calc_tax(ti, status):
    tax = 0.0
    for i, (thr, rate) in enumerate(BRACKETS[status]):
        nxt = BRACKETS[status][i+1][0] if i+1 < len(BRACKETS[status]) else None
        if nxt is None or ti < nxt:
            tax += (ti-thr)*rate
            break
        tax += (nxt-thr)*rate
    return tax

# --- PDF FILLING (OVERLAY EXAMPLE, USE YOUR COORDINATES) ---
def make_overlay_page1(s):
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=letter)

    # Row 1: You
    c.drawString(40,  690, f"{s['first_name']} {s.get('middle_initial','')}")
    c.drawString(245, 690, s['last_name'])
    c.drawString(480, 690, s['ssn'])

    # Row 2: Spouse
    c.drawString(40,  667, f"{s.get('spouse_first_name','')} {s.get('spouse_middle_initial','')}")
    c.drawString(245, 667, s.get('spouse_last_name',''))
    c.drawString(480, 668, s.get('spouse_ssn',''))

    # Row 3: Street & Apt
    c.drawString(40,  645, s['address_line1'])
    c.drawString(420, 645, s.get('address_apt',''))

    # Row 4: City / State / ZIP
    c.drawString(40,  620, s['city'])
    c.drawString(355, 620, s['state'])
    c.drawString(405, 620, s['zip_code'])

    # Filing status box
    boxes = {
        'single':                   (103, 583),
        'married_joint':            (103, 571),
        'married_separate':         (103, 559),
        'head_of_household':        (369, 583),
        'qualifying_surviving_spouse':(369, 559),
    }
    fs = s['filing_status']
    if fs in boxes:
        c.drawString(*boxes[fs],"X")

    # Dependents
    y=403
    for d in s.get('dependents',[]):
        c.drawString(100,y,f"{d['first_name']} {d.get('middle_initial','')}")
        c.drawString(175,y,d['last_name'])
        c.drawString(274,y,d['ssn'])
        c.drawString(353,y,d['relationship'])
        if d.get('child_tax_credit'):       c.drawString(453,y,"X")
        if d.get('other_dependent_credit'): c.drawString(532,y,"X")
        y-=12

    # Income lines
    c.drawString(505,354,f"{s['total_wages']:.2f}")
    c.drawString(505,343,f"{s['total_interest']:.2f}")
    c.drawString(505,138,f"{s['gross_income']:.2f}")
    c.drawString(505,102,f"{s['standard_deduction']:.2f}")
    c.drawString(505,66, f"{s['taxable_income']:.2f}")

    c.save(); buf.seek(0)
    return buf

def make_overlay_page2(s):
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=letter)
    c.drawString(505,650,f"{s['tax_liability']:.2f}")
    c.drawString(505,605,f"{s['total_withheld']:.2f}")
    c.drawString(505,480,f"{s['refund']:.2f}")
    c.drawString(171,459,s.get('routing_number',''))
    c.drawString(171,445,s.get('account_number',''))
    c.drawString(100,300,s.get('taxpayer_signature',''))
    c.setFont("Helvetica",8)
    c.drawString(277,300,s.get('signature_date',''))
    c.save(); buf.seek(0)
    return buf

def fill_pdf(s):
    tpl = PdfReader(str(TEMPLATE)); w = PdfWriter()
    ov1 = PdfReader(make_overlay_page1(s)); pg1 = tpl.pages[0]; pg1.merge_page(ov1.pages[0]); w.add_page(pg1)
    if len(tpl.pages) > 1:
        ov2 = PdfReader(make_overlay_page2(s)); pg2 = tpl.pages[1]; pg2.merge_page(ov2.pages[0]); w.add_page(pg2)
    fn = f"filled_1040_{int(time.time())}.pdf"; out = FILLED_DIR / fn
    with open(out, "wb") as f: w.write(f)
    return fn

# --- FLASK ROUTES ---
@app.route('/process', methods=['POST'])
def process():
    form_data = dict(request.form)
    validation_errors = validate_personal_info(form_data)
    if validation_errors:
        return jsonify(error="Invalid input", fields=validation_errors), 400

    # Prepare summary dict from user form data
    summary = {
        'first_name':       form_data.get('first_name',''),
        'middle_initial':   form_data.get('middle_initial',''),
        'last_name':        form_data.get('last_name',''),
        'ssn':              form_data.get('ssn',''),
        'spouse_first_name':form_data.get('spouse_first_name',''),
        'spouse_middle_initial':form_data.get('spouse_middle_initial',''),
        'spouse_last_name': form_data.get('spouse_last_name',''),
        'spouse_ssn':       form_data.get('spouse_ssn',''),
        'address_line1':    form_data.get('address_line1',''),
        'address_apt':      form_data.get('address_apt',''),
        'city':             form_data.get('city',''),
        'state':            form_data.get('state',''),
        'zip_code':         form_data.get('zip_code',''),
        'filing_status':    form_data.get('filing_status','single'),
        'dependents':       form_data.get('dependents','[]'),
        'routing_number':   form_data.get('routing_number',''),
        'account_number':   form_data.get('account_number',''),
        'taxpayer_signature':form_data.get('taxpayer_signature',''),
        'signature_date':   form_data.get('signature_date','')
    }
    try:
        summary['dependents'] = json.loads(summary['dependents'])
    except:
        summary['dependents'] = []

    forms = []
    for f in request.files.getlist('files'):
        if not f or not allowed_file(f.filename): continue
        fn = secure_filename(f.filename)
        dst = UPLOAD_DIR / fn; f.save(dst)
        forms.append(parse_form(str(dst)))

    w2w = sum(x.get('wages',0) for x in forms if x['type']=='w2')
    w2t = sum(x.get('withheld',0) for x in forms if x['type']=='w2')
    iamt = sum(x.get('interest',0) for x in forms if x['type']=='1099-int')
    namt = sum(x.get('nonemployee_comp',0) for x in forms if x['type']=='1099-nec')

    gross = w2w + iamt + namt
    std = STD_DED[summary['filing_status']]
    ti = max(0, gross - std)
    tax = calc_tax(ti, summary['filing_status'])
    refund = w2t - tax

    summary.update({
        'total_wages': w2w,
        'total_interest': iamt,
        'total_nonemployee_comp': namt,
        'gross_income': gross,
        'standard_deduction': std,
        'taxable_income': ti,
        'tax_liability': round(tax,2),
        'total_withheld': w2t,
        'refund': round(refund,2),
        'amount_due': round(-refund,2) if refund<0 else 0
    })

    fn = fill_pdf(summary)
    return jsonify(summary=summary, download_url=f"/download/{fn}"), 200

@app.route('/download/<fn>')
def download(fn):
    p = FILLED_DIR / fn
    if not p.exists(): return jsonify(error="Not found"), 404
    return send_file(str(p), as_attachment=True, download_name=fn)

@app.route('/health')
def health(): return jsonify(status="ok"), 200

if __name__ == '__main__':
    app.run(debug=True)
