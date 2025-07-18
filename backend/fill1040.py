#for filling only page 1
# #!/usr/bin/env python3
# import time
# from io import BytesIO
# from pathlib import Path

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from PyPDF2 import PdfReader, PdfWriter

# # 1) Path to your blank IRS form template:
# TEMPLATE_PATH = Path(r"C:\Agent Tax\backend\form_templates\f1040.pdf")

# # 2) Output directory for your filled forms:
# OUT_DIR = Path("./filled_test")
# OUT_DIR.mkdir(exist_ok=True)

# def make_overlay(summary: dict) -> BytesIO:
#     """
#     Draws the numbers onto a blank PDF overlay.
#     You'll tweak the x,y coords to line up with your form.
#     """
#     packet = BytesIO()
#     c = canvas.Canvas(packet, pagesize=letter)

#     # === sample positions (you MUST adjust these!) ===
#     # Line 1a: total wages
#     c.drawString(505, 354, f"{summary['total_wages']:.2f}")#done
#     # Line 2b: taxable interest
#     c.drawString(505, 343, f"{summary['total_interest']:.2f}")#done
#     # Line 9: total income
#     c.drawString(505, 138, f"{summary['gross_income']:.2f}")#done
#     # Line 12: standard deduction
#     c.drawString(505, 102, f"{summary['standard_deduction']:.2f}")#done
#     # Line 15: taxable income
#     c.drawString(505, 66, f"{summary['taxable_income']:.2f}")#done 
#     # Line 24: total tax
#     c.drawString(450, 570, f"{summary['tax_liability']:.2f}")
#     # Line 25d: total withholding
#     c.drawString(450, 550, f"{summary['total_withheld']:.2f}")
#     # Line 35a: refund
#     c.drawString(450, 530, f"{summary['refund']:.2f}")
#     # Line 37: amount you owe (if any)
#     if summary['amount_due'] > 0:
#         c.drawString(450, 510, f"{summary['amount_due']:.2f}")

#     c.save()
#     packet.seek(0)
#     return packet

# def fill_form1040(summary: dict, out_path: Path):
#     """Merge overlay onto page 1 of the blank template and write a filled PDF."""
#     template = PdfReader(str(TEMPLATE_PATH))
#     overlay  = PdfReader(make_overlay(summary))
#     writer   = PdfWriter()

#     # merge only page 1 (index 0)
#     page = template.pages[0]
#     page.merge_page(overlay.pages[0])
#     writer.add_page(page)

#     # if you want page 2, replicate above for template.pages[1]

#     with open(out_path, "wb") as f:
#         writer.write(f)

# if __name__ == "__main__":
#     # === Example summary; replace these with real test numbers ===
#     example_summary = {
#         "total_wages":           85000.00,
#         "total_interest":        120.50,
#         "gross_income":          85120.50,
#         "standard_deduction":    13850.00,
#         "taxable_income":        71270.50,
#         "tax_liability":         10500.75,
#         "total_withheld":        9500.00,
#         "refund":                -1000.75,   # negative means you owe
#         "amount_due":            1000.75
#     }

#     ts = int(time.time())
#     out_file = OUT_DIR / f"filled_1040_{ts}.pdf"

#     fill_form1040(example_summary, out_file)
#     print(f"Filled form saved to: {out_file.resolve()}")

#for filling both page 1 and 2 without names or anything just the numbers
# #!/usr/bin/env python3
# import time
# from io import BytesIO
# from pathlib import Path

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from PyPDF2 import PdfReader, PdfWriter

# # 1) Path to your blank IRS form template:
# TEMPLATE_PATH = Path(r"C:\Agent Tax\backend\form_templates\f1040.pdf")

# # 2) Output directory for your filled forms:
# OUT_DIR = Path("./filled_test")
# OUT_DIR.mkdir(exist_ok=True)

# def make_overlay_page1(summary: dict) -> BytesIO:
#     """
#     Draw the numbers onto a blank PDF overlay for page 1.
#     """
#     packet = BytesIO()
#     c = canvas.Canvas(packet, pagesize=letter)

#     # — page 1 (you’ve already got these coords) —
#     c.drawString(505, 354, f"{summary['total_wages']:.2f}")        # Line 1a
#     c.drawString(505, 343, f"{summary['total_interest']:.2f}")     # Line 2b
#     c.drawString(505, 138, f"{summary['gross_income']:.2f}")       # Line 9
#     c.drawString(505, 102, f"{summary['standard_deduction']:.2f}") # Line 12
#     c.drawString(505,  66, f"{summary['taxable_income']:.2f}")     # Line 15


#     c.save()
#     packet.seek(0)
#     return packet

# def make_overlay_page2(summary: dict) -> BytesIO:
#     """
#     Draw the fields for page 2.
#     You must replace these placeholder coords with your measured ones.
#     """
#     packet = BytesIO()
#     c = canvas.Canvas(packet, pagesize=letter)

#     # === TAX & CREDITS ===
#     # Total tax (L24 from p1): goes in box 24
#     c.drawString(505, 650, f"{summary['tax_liability']:.2f}")      # Line 24 #done
#     # Other lines 16–23 if needed…

#     # === PAYMENTS ===
#     c.drawString(505, 605, f"{summary['total_withheld']:.2f}")     # Line 25d #done
#     # Lines 26–33 if you want to fill them…

#     # === REFUND ===
#     c.drawString(505, 480, f"{summary['refund']:.2f}")             # Line 34 #done
#     c.drawString(171, 459, summary.get('routing_number', ''))      # Line 35b #done
#     c.drawString(171, 445, summary.get('account_number', ''))      # Line 35d

#     # === AMOUNT YOU OWE ===
#     if summary['amount_due'] > 0:
#         c.drawString(100, 580, f"{summary['amount_due']:.2f}")     # Line 37

#     # === THIRD PARTY DESIGNEE ===
#     # c.drawString(X, Y, summary.get('designee_name',''))

#     # === SIGN HERE ===
#     c.drawString(100, 300, summary.get('taxpayer_signature', ''))   # Signature #done
#     c.drawString(265, 300, summary.get('signature_date', ''))       # Date #done

#     # === PAID PREPARER ===
#     # c.drawString(X, Y, summary.get('preparer_name',''))

#     c.save()
#     packet.seek(0)
#     return packet

# def fill_form1040(summary: dict, out_path: Path):
#     """
#     Merge overlays for pages 1 & 2 onto your blank template.
#     """
#     template = PdfReader(str(TEMPLATE_PATH))
#     writer   = PdfWriter()

#     # — Page 1 —
#     overlay1 = PdfReader(make_overlay_page1(summary))
#     page1    = template.pages[0]
#     page1.merge_page(overlay1.pages[0])
#     writer.add_page(page1)

#     # — Page 2 —
#     if len(template.pages) > 1:
#         overlay2 = PdfReader(make_overlay_page2(summary))
#         page2    = template.pages[1]
#         page2.merge_page(overlay2.pages[0])
#         writer.add_page(page2)

#     # (repeat for more pages if needed)

#     with open(out_path, "wb") as f:
#         writer.write(f)

# if __name__ == "__main__":
#     example_summary = {
#         "total_wages":        85000.00,
#         "total_interest":     120.50,
#         "gross_income":       85120.50,
#         "standard_deduction": 13850.00,
#         "taxable_income":     71270.50,
#         "tax_liability":      10500.75,
#         "total_withheld":     9500.00,
#         "refund":             1500.25,
#         "amount_due":         0.00,
#         # extras for page 2:
#         "routing_number":     "123456789",
#         "account_number":     "987654321",
#         "taxpayer_signature": "Spandana Potti",
#         "signature_date":     "04/15/2025",
#     }

#     ts = int(time.time())
#     out_file = OUT_DIR / f"filled_1040_{ts}.pdf"
#     fill_form1040(example_summary, out_file)
#     print(f"Filled form saved to: {out_file.resolve()}")
#!/usr/bin/env python3
# filling all the columns in Form 1040

import time
from io import BytesIO
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

TEMPLATE_PATH = Path(r"C:\Agent Tax\backend\form_templates\f1040.pdf")
OUT_DIR      = Path("./filled_test")
OUT_DIR.mkdir(exist_ok=True)

def make_overlay_page1(summary: dict) -> BytesIO:
    """
    Draw personal info + income fields onto page 1.
    You must adjust all X/Y coords to match your template exactly.
    """
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)

    # --- PERSONAL INFO ---
    # First name + MI
    c.drawString(40, 690, f"{summary['first_name']} {summary.get('middle_initial','')}") #done
    # Last name
    c.drawString(245, 690, summary['last_name']) #done
    # SSN (XXX‑XX‑XXXX)
    c.drawString(480, 690, summary['ssn']) #done

    # Spouse first/last
    c.drawString(40, 667, f"{summary.get('spouse_first_name','')} {summary.get('spouse_middle_initial','')}")
    c.drawString(245, 667, summary.get('spouse_last_name',''))
    # Spouse SSN
    c.drawString(480, 668, summary.get('spouse_ssn',''))

    # Address line 1
    c.drawString(40, 645, summary['address_line1']) #done
    # Apt / unit
    c.drawString(420, 645, summary.get('address_apt','')) #done
    # City
    c.drawString(40, 620, summary['city']) #done
    # State
    c.drawString(355, 620, summary['state']) #done
    # ZIP
    c.drawString(405, 620, summary['zip_code']) #done

    # Filing Status: draw an "X" in the correct box
    fs = summary.get('filing_status','single')
    if fs == 'single':
        c.drawString( 103, 583, "X") #done
    elif fs == 'married_joint':
        c.drawString(103, 571, "X")#done
    elif fs == 'married_separate':
        c.drawString( 103, 559, "X") #done
    elif fs == 'head_of_household':
        c.drawString(369, 583, "X") #done
    elif fs == 'qualifying_surviving_spouse':
        c.drawString(369, 559, "X") #done 

    # Dependents (up to four); loop through list
    y_start = 403
    for dep in summary.get('dependents', []):
        # First + last
        c.drawString(100, y_start, f"{dep['first_name']} {dep.get('middle_initial','')}")
        c.drawString(175, y_start, dep['last_name'])
        # SSN
        c.drawString(274, y_start, dep['ssn'])
        # Relationship
        c.drawString(353, y_start, dep['relationship'])
        # Child tax credit?
        if dep.get('child_tax_credit'):
            c.drawString(453, y_start, "X")
        # Credit for other dependents?
        if dep.get('other_dependent_credit'):
            c.drawString(532, y_start, "X")
        y_start -= 12  # move down for next dependent

    # --- INCOME FIELDS (your existing coords) ---
    c.drawString(505, 354, f"{summary['total_wages']:.2f}")        # Line 1a
    c.drawString(505, 343, f"{summary['total_interest']:.2f}")     # Line 2b
    c.drawString(505, 138, f"{summary['gross_income']:.2f}")       # Line 9
    c.drawString(505, 102, f"{summary['standard_deduction']:.2f}") # Line 12
    c.drawString(505,  66, f"{summary['taxable_income']:.2f}")     # Line 15

    c.save()
    packet.seek(0)
    return packet

def make_overlay_page2(summary: dict) -> BytesIO:
    """
    (As before) fill page 2: tax, payments, refund, signature.
    """
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)

    # Line 24: total tax
    c.drawString(505, 650, f"{summary['tax_liability']:.2f}")
    # Line 25d: total withholding
    c.drawString(505, 605, f"{summary['total_withheld']:.2f}")
    # Line 34: refund
    c.drawString(505, 480, f"{summary['refund']:.2f}")
    # Line 35b: routing
    c.drawString(171, 459, summary.get('routing_number',''))
    # Line 35d: account
    c.drawString(171, 445, summary.get('account_number',''))

    # Signature block
    c.drawString(100, 300, summary.get('taxpayer_signature',''))
    c.setFont("Helvetica", 8)                     # ← smaller font size
    c.drawString(277, 300, summary.get('signature_date',''))

    c.save()
    packet.seek(0)
    return packet

def fill_form1040(summary: dict, out_path: Path):
    template = PdfReader(str(TEMPLATE_PATH))
    writer   = PdfWriter()

    # Merge page 1
    ov1 = PdfReader(make_overlay_page1(summary))
    p1  = template.pages[0]; p1.merge_page(ov1.pages[0]); writer.add_page(p1)

    # Merge page 2
    if len(template.pages) > 1:
        ov2 = PdfReader(make_overlay_page2(summary))
        p2  = template.pages[1]; p2.merge_page(ov2.pages[0]); writer.add_page(p2)

    with open(out_path, "wb") as f:
        writer.write(f)

if __name__ == "__main__":
    example = {
        # personal
        "first_name": "Taylor",
        "middle_initial": "K",
        "last_name": "Swift",
        "ssn": "123-45-6789",
        "spouse_first_name": "Bradd",
        "spouse_middle_initial": "",
        "spouse_last_name": "Pitt",
        "spouse_ssn": "408640948",
        "address_line1": "123 Main St",
        "address_apt": "Apt 4B",
        "city": "Columbus",
        "state": "OH",
        "zip_code": "43085",
        "filing_status": "qualifying_surviving_spouse",  # single / married_joint / married_separate / head_of_household / qualifying_surviving_spouse
        "dependents": [
            {"first_name":"Alice","last_name":"Potti","ssn":"111-22-3333","relationship":"Daughter","child_tax_credit":False,"other_dependent_credit":True},
            {"first_name":"Alice","last_name":"Potti","ssn":"111-22-3333","relationship":"Daughter","child_tax_credit":False,"other_dependent_credit":True},
            # add up to 4 entries...
        ],

        # income & tax
        "total_wages":        85000.00,
        "total_interest":     120.50,
        "gross_income":       85120.50,
        "standard_deduction": 13850.00,
        "taxable_income":     71270.50,
        "tax_liability":      10500.75,
        "total_withheld":     9500.00,
        "refund":             1500.25,

        # page 2 extras
        "routing_number":     "123456789",
        "account_number":     "987654321",
        "taxpayer_signature": "Spandana Potti",
        "signature_date":     "04/15/2025",
    }

    ts = int(time.time())
    out_file = OUT_DIR / f"filled_1040_{ts}.pdf"
    fill_form1040(example, out_file)
    print(f"Filled form saved to: {out_file.resolve()}")
