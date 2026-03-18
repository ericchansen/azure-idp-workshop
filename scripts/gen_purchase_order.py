"""Generate purchase order PDF sample for Module 2 table extraction demo."""

import os

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Header
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "PURCHASE ORDER", ln=True, align="C")
pdf.ln(4)

# PO details
pdf.set_font("Helvetica", "B", 10)
pdf.cell(95, 7, "Contoso Ltd.", ln=False)
pdf.cell(95, 7, "PO Number: PO-2025-0042", ln=True, align="R")

pdf.set_font("Helvetica", "", 9)
pdf.cell(95, 5, "123 Main Street, Redmond, WA 98052", ln=False)
pdf.cell(95, 5, "Date: March 1, 2025", ln=True, align="R")
pdf.cell(95, 5, "Phone: (425) 555-0100", ln=False)
pdf.cell(95, 5, "Payment Terms: Net 30", ln=True, align="R")
pdf.ln(4)

# Vendor
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Vendor: Fabrikam Inc.", ln=True)
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 5, "456 Commerce Ave, Suite 200, Seattle, WA 98101", ln=True)
pdf.cell(0, 5, "Contact: Maria Garcia | maria.garcia@fabrikam.com", ln=True)
pdf.ln(6)

# Ship To
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Ship To: Contoso Data Center, 789 Cloud Way, Quincy, WA 98848", ln=True)
pdf.ln(4)

# Line items table
pdf.set_font("Helvetica", "B", 9)
col_widths = [12, 72, 18, 30, 28, 30]
headers = ["Item", "Description", "Qty", "Unit Price", "Discount", "Total"]
for i, h in enumerate(headers):
    pdf.cell(col_widths[i], 8, h, border=1, align="C")
pdf.ln()

items = [
    ("1", "Azure Stack HCI Node - 64 Core", "4", "$12,500.00", "10%", "$45,000.00"),
    ("2", "NVMe SSD 3.84TB Enterprise", "16", "$890.00", "5%", "$13,528.00"),
    ("3", "DDR5 ECC RAM 128GB Module", "32", "$425.00", "5%", "$12,920.00"),
    ("4", "25GbE Network Adapter Dual-Port", "8", "$650.00", "0%", "$5,200.00"),
    ("5", "Rack Mount Kit 2U", "4", "$175.00", "0%", "$700.00"),
    ("6", "Power Supply 1600W Redundant", "8", "$320.00", "0%", "$2,560.00"),
    ("7", "Cable Management Kit", "4", "$85.00", "0%", "$340.00"),
    ("8", "Installation & Configuration Service", "1", "$4,500.00", "0%", "$4,500.00"),
]

pdf.set_font("Helvetica", "", 8)
for item in items:
    for i, val in enumerate(item):
        align = "C" if i in (0, 2) else "R" if i in (3, 4, 5) else "L"
        pdf.cell(col_widths[i], 7, val, border=1, align=align)
    pdf.ln()

pdf.ln(2)

# Totals
pdf.set_font("Helvetica", "", 9)
pdf.cell(130, 6, "", border=0)
pdf.cell(30, 6, "Subtotal:", border=0, align="R")
pdf.cell(30, 6, "$84,748.00", border=0, align="R")
pdf.ln()
pdf.cell(130, 6, "", border=0)
pdf.cell(30, 6, "Tax (10.1%):", border=0, align="R")
pdf.cell(30, 6, "$8,559.55", border=0, align="R")
pdf.ln()

pdf.set_font("Helvetica", "B", 10)
pdf.cell(130, 7, "", border=0)
pdf.cell(30, 7, "Total:", border="T", align="R")
pdf.cell(30, 7, "$93,307.55", border="T", align="R")
pdf.ln(6)

# Notes
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Notes:", ln=True)
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(
    0,
    5,
    "All hardware must be compatible with Azure Stack HCI 23H2. "
    "Vendor to provide 3-year warranty on all components. "
    "Installation to be completed within 10 business days of delivery. "
    "Delivery expected by March 31, 2025.",
)
pdf.ln(4)

# Authorization
pdf.set_font("Helvetica", "B", 10)
pdf.cell(95, 7, "Authorized By:", ln=False)
pdf.cell(95, 7, "Approved By:", ln=True)
pdf.set_font("Helvetica", "", 9)
pdf.cell(95, 12, "James Wilson, IT Procurement Manager", ln=False)
pdf.cell(95, 12, "Sarah Chen, VP of Infrastructure", ln=True)

pdf.output("samples/purchase-order.pdf")

size = os.path.getsize("samples/purchase-order.pdf")
print(f"Created samples/purchase-order.pdf ({size} bytes)")
