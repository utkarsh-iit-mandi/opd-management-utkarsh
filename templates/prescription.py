"""
prescription.py  —  Aggarwal Clinic
────────────────────────────────────
Drop next to app.py. Add to app.py:

    from prescription import prescription_bp
    app.register_blueprint(prescription_bp)

Add this button in history.html inside the visits loop:

    <a href="/prescription/{{ v.id }}" class="btn btn-sm" target="_blank">
        🖨️ Prescription
    </a>
"""

import datetime, sqlite3, os
from io import BytesIO

from flask import Blueprint, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, HRFlowable
)

prescription_bp = Blueprint("prescription", __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# ── Edit clinic details here ──────────────────────────────────────
CLINIC_NAME    = "Aggarwal Clinic"
DOCTOR_NAME    = "Dr. Vikas Aggarwal"
DOCTOR_QUAL    = "MBBS, MD"
DOCTOR_SPEC    = "General Physician"
DOCTOR_REG     = "Reg. No. MCI-12345678"
CLINIC_ADDRESS = "Village Road, Palwal, Haryana"
CLINIC_PHONE   = "9876543210"
OPD_HOURS      = "Mon\u2013Sat: 10AM\u20132PM"
# ─────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A5
CONTENT_W      = PAGE_W - 28*mm

FOREST     = colors.HexColor("#1a3a2a")
SAGE       = colors.HexColor("#4a7c59")
GOLD       = colors.HexColor("#b8962e")
MUTED      = colors.HexColor("#8a9e8e")
LIGHT_LINE = colors.HexColor("#ddeee1")
BG_HEADER  = colors.HexColor("#f7fbf8")
WHITE      = colors.white
BLACK      = colors.HexColor("#111111")


@prescription_bp.route("/prescription/<int:visit_id>")
def prescription(visit_id):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""
        SELECT v.id, v.symptoms, v.diagnosis, v.advice,
               v.fee, v.paid, v.credit, v.payment_mode, v.date,
               p.id, p.name, p.age, p.gender, p.address, co.mobile
        FROM visits v
        JOIN patients p  ON v.patient_id = p.id
        JOIN contacts co ON p.contact_id = co.id
        WHERE v.id = ?
    """, (visit_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "Visit not found", 404

    data = dict(
        visit_id=row[0],       symptoms=row[1],        diagnosis=row[2],
        advice=row[3] or "",   fee=row[4],             paid=row[5],
        credit=row[6],         payment_mode=row[7],    date=row[8],
        patient_id=row[9],     patient_name=row[10],   patient_age=row[11],
        patient_gender=row[12],patient_address=row[13] or "",
        patient_mobile=row[14] or "",
    )
    return send_file(
        BytesIO(_build_pdf(data)),
        mimetype="application/pdf",
        download_name=f"prescription_{visit_id}.pdf",
        as_attachment=False,
    )


def _build_pdf(d):
    buf = BytesIO()

    def S(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=BLACK, leading=14)
        base.update(kw)
        return ParagraphStyle(name, **base)

    def draw_page(canvas, doc):
        canvas.saveState()

        # Double border
        canvas.setStrokeColor(FOREST)
        canvas.setLineWidth(1.6)
        canvas.rect(8*mm, 8*mm, PAGE_W-16*mm, PAGE_H-16*mm)
        canvas.setLineWidth(0.4)
        canvas.rect(10.5*mm, 10.5*mm, PAGE_W-21*mm, PAGE_H-21*mm)

        # Dark header bar
        canvas.setFillColor(FOREST)
        canvas.rect(8*mm, PAGE_H-34*mm, PAGE_W-16*mm, 26*mm, fill=1, stroke=0)

        # Gold accent stripe
        canvas.setFillColor(GOLD)
        canvas.rect(8*mm, PAGE_H-34*mm-3, PAGE_W-16*mm, 3, fill=1, stroke=0)

        # Clinic name
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(PAGE_W/2, PAGE_H-22*mm, CLINIC_NAME)

        # Doctor line
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#b8d4bb"))
        canvas.drawCentredString(
            PAGE_W/2, PAGE_H-28.5*mm,
            f"{DOCTOR_NAME}  \u00b7  {DOCTOR_QUAL}  \u00b7  {DOCTOR_SPEC}"
        )

        # Rx watermark
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 100)
        canvas.setFillColor(colors.HexColor("#e8f5e9"))
        canvas.setFillAlpha(0.16)
        canvas.translate(PAGE_W/2, PAGE_H/2 - 15*mm)
        canvas.rotate(12)
        canvas.drawCentredString(0, 0, "Rx")
        canvas.restoreState()

        # Footer
        canvas.setStrokeColor(LIGHT_LINE)
        canvas.setLineWidth(0.6)
        canvas.line(14*mm, 21*mm, PAGE_W-14*mm, 21*mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 6.2)
        canvas.drawCentredString(PAGE_W/2, 16*mm,
            f"Computer-generated prescription  \u2022  {CLINIC_ADDRESS}")
        canvas.drawCentredString(PAGE_W/2, 12.5*mm,
            f"Valid 30 days  \u2022  Not valid if tampered  \u2022  Ph: {CLINIC_PHONE}")
        canvas.restoreState()

    frame = Frame(14*mm, 26*mm, CONTENT_W, PAGE_H-26*mm-38*mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=38*mm, bottomMargin=30*mm)
    doc.addPageTemplates([PageTemplate(id="rx", frames=[frame], onPage=draw_page)])

    s_f  = S("f",  fontSize=6.8, textColor=MUTED,  fontName="Helvetica-Bold", leading=10)
    s_v  = S("v",  fontSize=9,   textColor=BLACK,  fontName="Helvetica-Bold", leading=13)
    s_v2 = S("v2", fontSize=8.5, textColor=FOREST, leading=13)
    s_v3 = S("v3", fontSize=8,   textColor=MUTED,  leading=12)
    s_sc = S("sc", fontSize=7,   textColor=GOLD,   fontName="Helvetica-Bold",
             spaceAfter=2, leading=10)
    s_tx = S("tx", fontSize=9,   textColor=BLACK,  leading=14)
    s_dx = S("dx", fontSize=9.5, textColor=FOREST, fontName="Helvetica-Bold", leading=14)
    s_rx = S("rx", fontSize=22,  textColor=GOLD,   fontName="Helvetica-BoldOblique", leading=26)
    s_mn = S("mn", fontSize=9,   textColor=FOREST, fontName="Helvetica-Bold", leading=14)
    s_md = S("md", fontSize=8.5, textColor=SAGE,   leading=13)
    s_nb = S("nb", fontSize=8.5, textColor=MUTED,  fontName="Helvetica-Oblique", leading=13)
    s_nu = S("nu", fontSize=9,   textColor=GOLD,   fontName="Helvetica-Bold", leading=14)
    s_sg = S("sg", fontSize=9,   textColor=FOREST, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_sq = S("sq", fontSize=7.5, textColor=MUTED,  alignment=TA_RIGHT)

    story = [Spacer(1, 3*mm)]

    # Doctor sub-header
    dr_t = Table([
        [Paragraph("CONSULTING PHYSICIAN", s_f),
         Paragraph("OPD HOURS", s_f),
         Paragraph("CONTACT", s_f)],
        [Paragraph(DOCTOR_NAME, s_v),
         Paragraph(OPD_HOURS, s_v2),
         Paragraph(CLINIC_PHONE, s_v2)],
        [Paragraph(f"{DOCTOR_QUAL}  |  {DOCTOR_REG}", s_v3),
         Paragraph("", s_v3), Paragraph("", s_v3)],
    ], colWidths=[60*mm, 35*mm, 25*mm])
    dr_t.setStyle(TableStyle([
        ("ROWPADDING",    (0,0),(-1,-1), 3),
        ("TOPPADDING",    (0,0),(-1,0),  4),
        ("BOTTOMPADDING", (0,-1),(-1,-1),5),
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("BACKGROUND",    (0,0),(-1,-1), BG_HEADER),
        ("LINEBELOW",     (0,0),(-1,-1), 0.7, LIGHT_LINE),
    ]))
    story += [dr_t, Spacer(1, 5*mm)]

    # Patient info
    gm   = {"M":"Male","F":"Female","O":"Other"}
    gend = gm.get(d["patient_gender"], d["patient_gender"])
    ds   = d["date"]
    try:
        dt = datetime.datetime.strptime(ds[:19], "%Y-%m-%d %H:%M:%S")
        ds = dt.strftime("%d %B %Y")
    except Exception:
        pass

    pat_t = Table([
        [Paragraph("PATIENT", s_f), Paragraph("AGE / SEX", s_f),
         Paragraph("DATE", s_f),    Paragraph("REF. NO.", s_f)],
        [Paragraph(d["patient_name"].title(), s_v),
         Paragraph(f"{d['patient_age']} yrs / {gend}", s_v2),
         Paragraph(ds, s_v2),
         Paragraph(f"V-{d['visit_id']}", s_v2)],
    ], colWidths=[47*mm, 27*mm, 28*mm, 18*mm])
    pat_t.setStyle(TableStyle([
        ("ROWPADDING",    (0,0),(-1,-1), 4),
        ("TOPPADDING",    (0,0),(-1,0),  5),
        ("BOTTOMPADDING", (0,-1),(-1,-1),6),
        ("BACKGROUND",    (0,0),(-1,-1), BG_HEADER),
        ("BOX",           (0,0),(-1,-1), 0.8, LIGHT_LINE),
        ("LINEAFTER",     (0,0),(0,-1),  0.5, LIGHT_LINE),
        ("LINEAFTER",     (1,0),(1,-1),  0.5, LIGHT_LINE),
        ("LINEAFTER",     (2,0),(2,-1),  0.5, LIGHT_LINE),
    ]))
    story += [pat_t, Spacer(1, 6*mm)]

    # Complaints + Diagnosis
    story += [
        Paragraph("PRESENTING COMPLAINTS", s_sc),
        Paragraph(d["symptoms"] or "\u2014", s_tx),
        Spacer(1, 4*mm),
        Paragraph("DIAGNOSIS", s_sc),
        Paragraph(d["diagnosis"] or "\u2014", s_dx),
        Spacer(1, 4*mm),
        HRFlowable(width="100%", thickness=0.7, color=LIGHT_LINE),
        Spacer(1, 3*mm),
        Paragraph("Rx", s_rx),
        Spacer(1, 2*mm),
    ]

    # Medicine rows
    lines = [l.strip() for l in
             d["advice"].replace("\r\n", "\n").split("\n") if l.strip()]
    med_i = 0
    for line in lines:
        sep = None
        if " \u2014 " in line:   sep = " \u2014 "
        elif " - " in line and len(line) > 15: sep = " - "

        if sep:
            name, detail = line.split(sep, 1)
            med_i += 1
            row = Table([[
                Paragraph(str(med_i), s_nu),
                Paragraph(name.strip(), s_mn),
                Paragraph(detail.strip(), s_md),
            ]], colWidths=[7*mm, 57*mm, 56*mm])
            row.setStyle(TableStyle([
                ("ROWPADDING", (0,0),(-1,-1), 6),
                ("VALIGN",     (0,0),(-1,-1),"MIDDLE"),
                ("LINEBELOW",  (0,0),(-1,-1), 0.35, LIGHT_LINE),
            ]))
        else:
            row = Table([[
                Paragraph("", s_nu),
                Paragraph(f"<i>{line}</i>", s_nb),
                Paragraph("", s_md),
            ]], colWidths=[7*mm, 57*mm, 56*mm])
            row.setStyle(TableStyle([
                ("ROWPADDING", (0,0),(-1,-1), 5),
                ("LINEBELOW",  (0,0),(-1,-1), 0.35, LIGHT_LINE),
            ]))
        story.append(row)

    story.append(Spacer(1, 8*mm))

    # Signature
    sig_t = Table([
        [Paragraph("", s_f),  Paragraph(DOCTOR_NAME, s_sg)],
        [Paragraph("", s_f),  Paragraph(f"{DOCTOR_QUAL}  |  {DOCTOR_SPEC}", s_sq)],
    ], colWidths=[70*mm, 50*mm])
    sig_t.setStyle(TableStyle([
        ("ROWPADDING", (0,0),(-1,-1), 2),
        ("LINEABOVE",  (1,0),(1,0),   0.8, FOREST),
        ("TOPPADDING", (0,0),(-1,0),  5),
    ]))
    story.append(sig_t)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
