import io
from typing import List
from datetime import datetime
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.audit import Audit, AuditResponse

def generate_excel_report(audits: List[Audit]) -> bytes:
    """Generates an Excel spreadsheet containing a summary checklist of audits."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Audit Report")
    
    # Styles
    title_format = workbook.add_format({
        'bold': True, 'size': 16, 'font_color': '#005F73', 'align': 'center'
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#005F73', 'font_color': 'white', 'border': 1, 'align': 'center'
    })
    cell_format = workbook.add_format({'border': 1, 'align': 'left'})
    number_format = workbook.add_format({'border': 1, 'num_format': '0.00', 'align': 'right'})
    date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd hh:mm', 'align': 'center'})
    
    # Title
    worksheet.merge_range('A1:G1', 'Hospital Infection Control - Audit Summary Report', title_format)
    worksheet.write('A2', '')
    
    # Table Headers
    headers = ["Audit ID", "Template Name", "Department", "Auditor Name", "Audited At", "Compliance %", "Risk Level"]
    for col_idx, header in enumerate(headers):
        worksheet.write(2, col_idx, header, header_format)
        
    # Table Rows
    for row_idx, audit in enumerate(audits):
        real_row = row_idx + 3
        worksheet.write(real_row, 0, str(audit.id), cell_format)
        worksheet.write(real_row, 1, audit.template.title, cell_format)
        worksheet.write(real_row, 2, audit.department.name, cell_format)
        worksheet.write(real_row, 3, audit.auditor.full_name, cell_format)
        worksheet.write(real_row, 4, audit.audited_at.strftime('%Y-%m-%d %H:%M'), date_format)
        worksheet.write(real_row, 5, float(audit.compliance_percentage), number_format)
        worksheet.write(real_row, 6, audit.risk_level.value, cell_format)
        
    # Auto-adjust column widths
    for col_idx in range(len(headers)):
        worksheet.set_column(col_idx, col_idx, 20)
        
    workbook.close()
    return output.getvalue()

def generate_pdf_audit_report(audit: Audit) -> bytes:
    """Generates a professional-grade PDF summary sheet for a single audit execution."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor('#005F73')
    c_secondary = colors.HexColor('#0A9396')
    c_text = colors.HexColor('#1E293B')
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=c_primary,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=c_text,
        leading=14
    )
    
    body_bold_style = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Header Title
    story.append(Paragraph("Hospital Infection Control Audit Summary", title_style))
    story.append(Spacer(1, 10))
    
    # Audit Metadata Table
    meta_data = [
        [Paragraph("Audit Template:", body_bold_style), Paragraph(audit.template.title, body_style),
         Paragraph("Department Name:", body_bold_style), Paragraph(audit.department.name, body_style)],
        [Paragraph("Infection Auditor:", body_bold_style), Paragraph(audit.auditor.full_name, body_style),
         Paragraph("Execution Date:", body_bold_style), Paragraph(audit.audited_at.strftime('%Y-%m-%d %H:%M'), body_style)],
        [Paragraph("Compliance Score:", body_bold_style), Paragraph(f"{audit.compliance_percentage}%", body_bold_style),
         Paragraph("Risk Classification:", body_bold_style), Paragraph(audit.risk_level.value, body_bold_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Detailed Question Reponses
    story.append(Paragraph("Detailed Question Assessment", section_title_style))
    
    resp_headers = [
        Paragraph("<b>Question</b>", body_bold_style),
        Paragraph("<b>Answer</b>", body_bold_style),
        Paragraph("<b>Score</b>", body_bold_style),
        Paragraph("<b>Auditor Remarks</b>", body_bold_style)
    ]
    
    resp_table_data = [resp_headers]
    for resp in audit.responses:
        # Style answer based on compliance
        ans_color = '#1E293B'
        if resp.answer.upper() in ["YES", "Y", "TRUE"]:
            ans_color = '#16A34A'
        elif resp.answer.upper() in ["NO", "N", "FALSE"]:
            ans_color = '#DC2626'
            
        ans_style = ParagraphStyle('Ans', parent=body_style, textColor=colors.HexColor(ans_color), fontName='Helvetica-Bold')
        
        resp_table_data.append([
            Paragraph(resp.question.text, body_style),
            Paragraph(resp.answer, ans_style),
            Paragraph(str(resp.score), body_style),
            Paragraph(resp.remarks or "-", body_style)
        ])
        
    resp_table = Table(resp_table_data, colWidths=[200, 80, 60, 200])
    resp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
    ]))
    
    story.append(resp_table)
    
    # Build Document
    doc.build(story)
    return buffer.getvalue()

def generate_daily_rounds_excel(rounds) -> bytes:
    """Generates an Excel spreadsheet containing a summary checklist of daily rounds and their observations."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Daily Rounds Report")
    
    # Styles
    title_format = workbook.add_format({
        'bold': True, 'size': 16, 'font_color': '#005F73', 'align': 'center'
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#005F73', 'font_color': 'white', 'border': 1, 'align': 'center'
    })
    cell_format = workbook.add_format({'border': 1, 'align': 'left'})
    number_format = workbook.add_format({'border': 1, 'num_format': '0', 'align': 'right'})
    date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd hh:mm', 'align': 'center'})
    
    # Title
    worksheet.merge_range('A1:G1', 'Hospital Infection Control - Daily Rounds Walk Summary', title_format)
    worksheet.write('A2', '')
    
    # Table Headers
    headers = ["Round ID", "Hospital", "Building", "Shift / Session", "Started At", "Status", "Gaps Found"]
    for col_idx, header in enumerate(headers):
        worksheet.write(2, col_idx, header, header_format)
        
    # Table Rows
    for row_idx, r in enumerate(rounds):
        real_row = row_idx + 3
        worksheet.write(real_row, 0, str(r.id), cell_format)
        worksheet.write(real_row, 1, r.hospital, cell_format)
        worksheet.write(real_row, 2, r.building, cell_format)
        worksheet.write(real_row, 3, r.round_type, cell_format)
        worksheet.write(real_row, 4, r.started_at.strftime('%Y-%m-%d %H:%M'), date_format)
        worksheet.write(real_row, 5, r.status.value if hasattr(r.status, "value") else str(r.status), cell_format)
        worksheet.write(real_row, 6, len(r.observations), number_format)
        
    # Auto-adjust column widths
    for col_idx in range(len(headers)):
        worksheet.set_column(col_idx, col_idx, 20)
        
    workbook.close()
    return output.getvalue()

def generate_pdf_capa_report(capa, assignee_name: str = "Unknown", creator_name: str = "System") -> bytes:
    """Generates a professional-grade PDF summary sheet for a CAPA corrective action plan."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor('#005F73')
    c_secondary = colors.HexColor('#0A9396')
    c_text = colors.HexColor('#1E293B')
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=c_primary,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=c_text,
        leading=14
    )
    
    body_bold_style = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Corrective & Preventive Action (CAPA) Plan", title_style))
    story.append(Spacer(1, 10))
    
    # CAPA Details Table
    meta_data = [
        [Paragraph("CAPA Title:", body_bold_style), Paragraph(capa.title, body_style),
         Paragraph("Department:", body_bold_style), Paragraph(capa.department.name, body_style)],
        [Paragraph("Assigned Person:", body_bold_style), Paragraph(assignee_name, body_style),
         Paragraph("Target Deadline:", body_bold_style), Paragraph(capa.deadline.strftime('%Y-%m-%d'), body_style)],
        [Paragraph("Priority Level:", body_bold_style), Paragraph(capa.priority.value, body_bold_style),
         Paragraph("Current Status:", body_bold_style), Paragraph(capa.status.value, body_bold_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Description
    story.append(Paragraph("Non-Conformance Description", section_title_style))
    story.append(Paragraph(capa.description, body_style))
    story.append(Spacer(1, 15))
    
    # CAPA Actions
    story.append(Paragraph("Action Resolution Plan", section_title_style))
    
    plan_data = [
        [Paragraph("<b>Root Cause Analysis (RCA)</b>", body_bold_style)],
        [Paragraph(capa.root_cause_analysis or "Pending analysis.", body_style)],
        [Spacer(1, 5)],
        [Paragraph("<b>Corrective Action (Immediate Fix)</b>", body_bold_style)],
        [Paragraph(capa.corrective_action or "Pending implementation.", body_style)],
        [Spacer(1, 5)],
        [Paragraph("<b>Preventive Action (Long-Term Prevention)</b>", body_bold_style)],
        [Paragraph(capa.preventive_action or "Pending configuration.", body_style)]
    ]
    
    plan_table = Table(plan_data, colWidths=[530])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0,3), (0,3), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0,6), (0,6), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
    ]))
    story.append(plan_table)
    story.append(Spacer(1, 15))
    
    # Signatures block
    story.append(Paragraph("Documentation & Signatures", section_title_style))
    sig_data = [
        [Paragraph(f"Created By: {creator_name}", body_style), Paragraph("Approved By: ___________________", body_style)],
        [Paragraph(f"Date: {capa.created_at.strftime('%Y-%m-%d')}", body_style), Paragraph(f"Date: {capa.closed_at.strftime('%Y-%m-%d') if capa.closed_at else '___________'}", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[265, 265])
    sig_table.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer.getvalue()
