from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import io
import datetime
import re


# -----------------------------------------------------
# CLEAN HTML → TEXT (basic markdown/HTML stripper)
# -----------------------------------------------------
def clean_html(html_text):
    if not html_text:
        return ""

    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_text.replace("•", "- ")
    html_text = "\n".join([ln.strip() for ln in html_text.split("\n") if ln.strip()])
    return html_text


# -----------------------------------------------------
# DRAW HEADER BAR
# -----------------------------------------------------
def draw_header(c, W, H, title="AccessOps — Evaluation Report"):
    c.setFillColorRGB(0.13, 0.39, 0.80)  # Blue header bar
    c.rect(0, H - 40, W, 40, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, H - 28, title)


# -----------------------------------------------------
# DRAW SECTION TITLE
# -----------------------------------------------------
def draw_section_title(c, x, y, text):
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(x, y, text)
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(0.6)
    c.line(x, y - 3, x + 160 * mm, y - 3)


# -----------------------------------------------------
# DRAW WATERMARK
# -----------------------------------------------------
def draw_watermark(c, W, H):
    c.saveState()
    c.setFillColorRGB(0.85, 0.85, 0.85, alpha=0.15)
    c.setFont("Helvetica-Bold", 60)
    c.translate(W / 2, H / 2)
    c.rotate(30)
    c.drawCentredString(0, 0, "CONFIDENTIAL")
    c.restoreState()


# -----------------------------------------------------
# DRAW FOOTER
# -----------------------------------------------------
def draw_footer(c, W, page_num):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.3, 0.3)

    c.drawString(20 * mm, 10 * mm, f"Generated: {now}")
    c.drawRightString(W - 20 * mm, 10 * mm, f"Page {page_num}")


# -----------------------------------------------------
# DRAW KEY:VALUE TABLE
# -----------------------------------------------------
def draw_table(c, x, y, data_dict):
    c.setFont("Helvetica", 11)
    for k, v in data_dict.items():
        line = f"{k}: {v}"
        c.drawString(x, y, line)
        y -= 12
        if y < 40 * mm:
            c.showPage()
            return None, True
    return y, False


# -----------------------------------------------------
# SEVERITY COLOR BADGES
# -----------------------------------------------------
def severity_color(sev):
    if sev == "LOW":
        return colors.green
    if sev == "MEDIUM":
        return colors.orange
    return colors.red


# -----------------------------------------------------
# MAIN PDF BUILDER
# -----------------------------------------------------
def make_pdf(payload, response, gauge_fig=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    W, H = A4
    margin = 20 * mm
    y = H - margin
    page_num = 1

    # Draw header + watermark
    draw_header(c, W, H)
    draw_watermark(c, W, H)

    # -------------------------------
    # 1. REQUEST DETAILS
    # -------------------------------
    y -= 50
    draw_section_title(c, margin, y, "1. Access Request Details")
    y -= 25

    table_data = {k: v for k, v in payload.items() if k != "timestamp"}
    new_y, page_break = draw_table(c, margin, y, table_data)

    if page_break:
        c.showPage()
        page_num += 1
        draw_header(c, W, H)
        draw_watermark(c, W, H)
        y = H - margin

    else:
        y = new_y - 10

    # -------------------------------
    # 2. DECISION + RISK
    # -------------------------------
    draw_section_title(c, margin, y, "2. Decision & Risk")
    y -= 25

    decision = response.get("decision")
    sev = response["risk_score"].get("severity_level")
    score = response["risk_score"].get("net_risk_score")

    # Severity badge
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, f"Decision: {decision}")
    y -= 16

    c.setFillColor(severity_color(sev))
    c.rect(margin, y - 12, 60, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(margin + 4, y - 10, sev.upper())
    c.setFillColor(colors.black)
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Net Risk Score: {score}")
    y -= 20

    # Gauge embedded
    if gauge_fig:
        img_buf = io.BytesIO()
        gauge_fig.savefig(img_buf, format="png", dpi=150)
        img_buf.seek(0)
        img = ImageReader(img_buf)
        c.drawImage(img, margin, y - 90, width=120, height=80)
        y -= 110

    if y < 60 * mm:
        c.showPage()
        page_num += 1
        draw_header(c, W, H)
        draw_watermark(c, W, H)
        y = H - margin

    # -------------------------------
    # 3. EXECUTIVE BOARD REPORT
    # -------------------------------
    draw_section_title(c, margin, y, "3. Executive Board Report")
    y -= 25

    c.setFont("Helvetica", 11)
    report_text = clean_html(response.get("board_report", ""))

    for line in report_text.split("\n"):
        c.drawString(margin, y, line)
        y -= 12

        if y < 40 * mm:
            c.showPage()
            page_num += 1
            draw_header(c, W, H)
            draw_watermark(c, W, H)
            y = H - margin

    # -------------------------------
    # 4. MANAGER SIGNATURE BLOCK
    # -------------------------------
    y -= 30
    draw_section_title(c, margin, y, "4. Manager Review & Approval")
    y -= 35

    c.setFont("Helvetica", 11)
    c.drawString(margin, y, "Manager Name: _______________________________")
    y -= 20
    c.drawString(margin, y, "Signature: ____________________________________")
    y -= 20
    c.drawString(margin, y, "Date: _________________________________________")

    # Footer
    draw_footer(c, W, page_num)

    c.showPage()
    c.save()

    buf.seek(0)
    return buf.getvalue()
