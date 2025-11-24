from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

def make_pdf(payload, response):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    W, H = A4
    margin = 20 * mm
    y = H - margin

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "AccessOps — Manager Review Report")
    y -= 25

    c.setFont("Helvetica", 11)

    for k, v in payload.items():
        c.drawString(margin, y, f"{k}: {v}")
        y -= 14
        if y <= 40*mm:
            c.showPage()
            y = H - margin

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Decision & Risk")
    y -= 16

    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Decision: {response.get('decision')}")
    y -= 14
    c.drawString(margin, y, f"Severity: {response['risk_score'].get('severity_level')}")
    y -= 14
    c.drawString(margin, y, f"Risk Score: {response['risk_score'].get('net_risk_score')}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
