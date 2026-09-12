import io
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from app.modules.invoices.models import Invoice

def generate_invoice_pdf_bytes(invoice: Invoice, organisation, customer) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{organisation.name}")
    c.setFont("Helvetica", 10)
    if hasattr(organisation, 'address') and organisation.address:
        c.drawString(50, height - 65, organisation.address)
    
    # Invoice Title
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - 50, height - 50, "INVOICE")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 70, f"Invoice Number: {invoice.invoice_number}")
    c.drawRightString(width - 50, height - 85, f"Date: {invoice.invoice_date.strftime('%Y-%m-%d')}")
    c.drawRightString(width - 50, height - 100, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}")

    # Billed To
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "Bill To:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 135, f"{customer.name}")
    if hasattr(customer, 'address') and customer.address:
        c.drawString(50, height - 150, customer.address)

    # Line Items Header
    y = height - 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawRightString(width - 150, y, "Qty")
    c.drawRightString(width - 100, y, "Rate")
    c.drawRightString(width - 50, y, "Amount")
    c.line(50, y - 5, width - 50, y - 5)
    
    y -= 20
    c.setFont("Helvetica", 10)
    for line in invoice.lines:
        c.drawString(50, y, line.description[:40])
        c.drawRightString(width - 150, y, str(line.quantity))
        c.drawRightString(width - 100, y, f"{line.unit_rate:.2f}")
        c.drawRightString(width - 50, y, f"{line.amount:.2f}")
        y -= 20

    c.line(50, y, width - 50, y)
    y -= 15
    
    # Tax and Totals
    c.drawRightString(width - 100, y, "Subtotal:")
    c.drawRightString(width - 50, y, f"{invoice.subtotal:.2f}")
    y -= 15
    
    for tax in invoice.tax_lines:
        c.drawRightString(width - 100, y, f"{tax.tax_name} ({tax.tax_rate}%):")
        c.drawRightString(width - 50, y, f"{tax.tax_amount:.2f}")
        y -= 15
        
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 100, y - 5, "Grand Total:")
    c.drawRightString(width - 50, y - 5, f"{invoice.currency} {invoice.grand_total:.2f}")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def generate_vendor_payable_pdf_bytes(payable, organisation, vendor) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{organisation.name}")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - 50, height - 50, "SETTLEMENT STATEMENT")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 70, f"Ref: {payable.reference_number}")
    c.drawRightString(width - 50, height - 85, f"Date: {payable.created_at.strftime('%Y-%m-%d')}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "Vendor:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 135, f"{vendor.name if vendor else 'Unknown'}")

    y = height - 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawRightString(width - 50, y, "Amount")
    c.line(50, y - 5, width - 50, y - 5)
    
    y -= 20
    c.setFont("Helvetica", 10)
    for line in getattr(payable, 'lines', []):
        c.drawString(50, y, line.description[:40])
        amt = f"-{line.amount:.2f}" if line.is_deduction else f"{line.amount:.2f}"
        c.drawRightString(width - 50, y, amt)
        y -= 20

    c.line(50, y, width - 50, y)
    y -= 15
    
    c.drawRightString(width - 150, y, "Subtotal:")
    c.drawRightString(width - 50, y, f"{payable.subtotal:.2f}")
    y -= 15
    c.drawRightString(width - 150, y, "Deductions:")
    c.drawRightString(width - 50, y, f"-{payable.deductions:.2f}")
    y -= 15
        
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 150, y - 5, "Net Payable:")
    c.drawRightString(width - 50, y - 5, f"{payable.currency} {payable.grand_total:.2f}")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
