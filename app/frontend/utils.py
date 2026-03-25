import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_bytes(plan: dict) -> bytes:
    """Generate a PDF summary of the project plan and return it as bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(plan.get("project_title", "Plan de Proyecto"), styles["Title"]))
    story.append(Spacer(1, 4*mm))

    # Key metrics
    story.append(Paragraph(f"Presupuesto estimado: {plan.get('total_budget', 0):,.0f} €", styles["Normal"]))
    story.append(Paragraph(f"Fecha de entrega: {plan.get('estimated_completion_date', '-')}", styles["Normal"]))
    story.append(Paragraph(f"Líder: {plan.get('project_leader', '-')}", styles["Normal"]))
    story.append(Spacer(1, 6*mm))

    # Objectives
    objetivos = plan.get("objetivos", [])
    if objetivos:
        story.append(Paragraph("Objetivos", styles["Heading2"]))
        for obj in objetivos:
            story.append(Paragraph(f"• {obj}", styles["Normal"]))
        story.append(Spacer(1, 4*mm))

    # Tasks
    assignments = plan.get("assignments", [])
    if assignments:
        story.append(Paragraph("Tareas", styles["Heading2"]))
        header = ["Tarea", "Responsable(s)", "Horas", "Prioridad"]
        rows = [header]
        for a in assignments:
            assignees = a.get("assigned_to", "")
            if isinstance(assignees, list):
                assignees = ", ".join(assignees)
            rows.append([
                a.get("task_name", ""),
                assignees,
                str(a.get("hours", "-")),
                a.get("priority", "-"),
            ])
        t = Table(rows, colWidths=[70*mm, 60*mm, 20*mm, 25*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#333333")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 4*mm))

    # Team
    team = plan.get("team_members", [])
    if team:
        story.append(Paragraph("Equipo", styles["Heading2"]))
        header2 = ["Nombre", "Rol", "Horas totales"]
        rows2 = [header2]
        for m in team:
            rows2.append([m.get("name", ""), m.get("role", ""), str(m.get("total_hours", "-"))])
        t2 = Table(rows2, colWidths=[55*mm, 80*mm, 40*mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#333333")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t2)

    doc.build(story)
    return buf.getvalue()
