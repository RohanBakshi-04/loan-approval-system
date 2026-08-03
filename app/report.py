import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(app) -> io.BytesIO:
    """
    Generates an audit-ready, beautifully styled PDF Credit Risk Memo
    for a specific loan application, returned as a BytesIO stream.
    """
    buffer = io.BytesIO()
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36
    )
    
    # 2. Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F172A'), # Slate-900
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#38BDF8'), # Cyan-400
        spaceBefore=14,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'), # Slate-700
        leading=14
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=body_style,
        fontSize=9,
        leading=11
    )
    
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=body_style,
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        leading=11
    )

    story = []
    
    # 3. Header Section (Title & Metadata)
    story.append(Paragraph("🏦 LOAN DECISION & CREDIT RISK MEMO", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  System: AI-Approval Engine v0.5", body_style))
    story.append(Spacer(1, 15))
    
    # Decisional Highlight Box (Table)
    decision_color = "#34D399" if app.approval_status == "Approved" else "#EF4444" # Green vs Red
    decision_text = f"<b>SYSTEM DECISION: {app.approval_status.upper()}</b>"
    risk_text = f"<b>RISK ASSESSMENT SCORE: {app.risk_score:.1f}%</b>"
    
    summary_data = [
        [Paragraph(decision_text, ParagraphStyle('Dec', parent=body_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0F172A'))),
         Paragraph(risk_text, ParagraphStyle('Risk', parent=body_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0F172A')))]
    ]
    
    summary_table = Table(summary_data, colWidths=[270, 270])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(decision_color)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # 4. Applicant Profile Table
    story.append(Paragraph("1. APPLICANT GENERAL PROFILE", h2_style))
    
    profile_data = [
        [Paragraph("Parameter", table_hdr_style), Paragraph("Value Captured", table_hdr_style),
         Paragraph("Parameter", table_hdr_style), Paragraph("Value Captured", table_hdr_style)],
         
        [Paragraph("Full Name", table_cell_style), Paragraph(str(app.name), table_cell_style),
         Paragraph("Age", table_cell_style), Paragraph(f"{app.age} Years", table_cell_style)],
         
        [Paragraph("Dependents", table_cell_style), Paragraph(str(app.dependents), table_cell_style),
         Paragraph("Housing Status", table_cell_style), Paragraph(str(app.housing), table_cell_style)],
         
        [Paragraph("Employment Status", table_cell_style), Paragraph(str(app.employment), table_cell_style),
         Paragraph("Annual Gross Income", table_cell_style), Paragraph(f"${app.income:,.2f}", table_cell_style)]
    ]
    
    profile_table = Table(profile_data, colWidths=[120, 150, 120, 150])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#1E293B')), # Dark slate header column
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#1E293B')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')), # Darker top header row
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 15))
    
    # 5. Loan Request & Risk Metrics
    story.append(Paragraph("2. FINANCIAL RISK METRICS", h2_style))
    
    metrics_data = [
        [Paragraph("Metric", table_hdr_style), Paragraph("Value", table_hdr_style),
         Paragraph("Acceptable Range / Benchmark", table_hdr_style)],
         
        [Paragraph("Requested Loan Amount", table_cell_style), Paragraph(f"${app.loan_amount:,.2f}", table_cell_style),
         Paragraph("Subject to debt constraints", table_cell_style)],
         
        [Paragraph("Loan Term", table_cell_style), Paragraph(f"{app.term_months} Months", table_cell_style),
         Paragraph("Standard terms (12-60m)", table_cell_style)],
         
        [Paragraph("FICO Credit Score", table_cell_style), Paragraph(str(app.credit_score), table_cell_style),
         Paragraph("Minimum 500 threshold for automatic checks", table_cell_style)],
         
        [Paragraph("Debt-to-Income (DTI) Ratio", table_cell_style), Paragraph(f"{app.dti_ratio:.1f}%", table_cell_style),
         Paragraph("Below 50% preferred", table_cell_style)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[180, 160, 200])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 15))
    
    # 6. Explanation Notes
    story.append(Paragraph("3. UNDERWRITER EXPLANATION & AUDIT COMPLIANCE", h2_style))
    
    if app.approval_status == "Approved":
        risk_evaluation = (
            "The applicant is evaluated as a low-to-medium risk profile. The credit score matches baseline limits "
            "and the estimated Debt-to-Income (DTI) ratio is within healthy operational tolerances. The automated "
            "classification model recommends immediate processing of the loan contract, subject to standard identity confirmation."
        )
    else:
        risk_evaluation = (
            "The applicant is flagged as a high-default risk profile. This decision is driven primarily by a low "
            "FICO credit score (<500) and/or an elevated Debt-to-Income (DTI) ratio exceeding 50%. The model does not recommend "
            "approval at this time. Standard regulatory adverse action notice must be issued within 30 days."
        )
        
    story.append(Paragraph(risk_evaluation, body_style))
    
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer
