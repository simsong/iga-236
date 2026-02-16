import json
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT

NOTES = 'notes'
ATTENDANCE = 'attendance'
ROLES = 'roles'

def generate_handout(*, roles, output_pdf="Student_Handout.pdf", sheet=None):
    def add_header_footer(canvas, doc):
        """Adds a title header and page numbers."""
        match sheet:
            case 'attendance':
                title = "Policy Coordination Council Sign-In Sheet"
            case 'notes':
                title = "Policy Coordination Council Notes"
            case 'roles':
                title = "Scenario Role Overview: Policy Coordination Council"

        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawCentredString(4.25 * inch, 10.5 * inch, title)

        canvas.setFont('Helvetica', 9)
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {page_num}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=LETTER,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Text styles for table content
    role_style = ParagraphStyle('RoleStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    pos_style = ParagraphStyle('PosStyle', parent=styles['Normal'], fontSize=9, leading=11)

    # Table Header
    match sheet:
        case 'attendance':
            data = [['Home Country', 'Role', 'Name']]
        case 'notes':
            data = [['Home Country', 'Role', 'Notes']]
        case 'roles':
            data = [['Home Country', 'Role', 'Position & Backstory']]

    # Populate Table Rows
    for r in roles:
        row = [
            Paragraph(r['Home Country'], pos_style),
            Paragraph(r['Role'], role_style),
            Paragraph(r['Position'] if sheet=='roles' else '', pos_style)
        ]
        data.append(row)

    # Define Table layout and style
    # Column widths: Country (1.2"), Role (1.5"), Position (4.8")
    rowHeights = None if sheet=='roles' else [.35*inch]*len(data)

    if sheet:
        colWidths = [1.2*inch, 2*inch,4.2*inch]
    else:
        colWidths = [1.2*inch, 1.5*inch, 4.8*inch]

    t = Table(data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)

    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]) # Alternating row colors
    ]))

    elements = [t]

    # Build PDF with Header/Footer
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"Successfully generated: {output_pdf}")

def generate_cards(roles, output_pdf="Role_Cards.pdf"):
    # Set page size to 3x5 inches
    card_size = (5*inch, 3*inch)  # Landscape orientation
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=card_size,
        rightMargin=14,
        leftMargin=14,
        topMargin=14,
        bottomMargin=14
    )

    styles = getSampleStyleSheet()

    # Custom Pretty Style for the Backstory/Position
    custom_style = ParagraphStyle(
        'PrettyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=14,
        alignment=TA_LEFT
    )

    elements = []

    for role in roles:
        # Header Information
        elements.append(Paragraph(f"<b>Name:</b> ______________________", custom_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Home Country:</b> {role['Home Country']}", custom_style))
        elements.append(Paragraph(f"<b>Role:</b> {role['Role']}", custom_style))
        elements.append(Spacer(1, 10))

        # Position Title
        elements.append(Paragraph("<b>Position & Backstory:</b>", custom_style))

        # Word-wrapped Body Text
        elements.append(Paragraph(role['Position'], custom_style))

        # Move to the next card (next page)
        elements.append(PageBreak())

    # Build the PDF
    doc.build(elements)
    print(f"Successfully generated {output_pdf}")

if __name__ == "__main__":
    with open("roles.json","r") as f:
        roles = json.load(f)
    generate_cards(roles=roles, output_pdf='Handout_Cards.pdf')
    generate_handout(roles=roles, output_pdf='Handout_Attendance.pdf',sheet=ATTENDANCE)
    generate_handout(roles=roles, output_pdf='Handout_Notes.pdf',sheet=NOTES)
    generate_handout(roles=roles, output_pdf='Handout_End.pdf',sheet=ROLES)
