import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return send_file(os.path.join(os.path.dirname(__file__), '../public/index.html'))

BRAND_RED = colors.HexColor("#EA1B3D")
BRAND_SLATE = colors.HexColor("#2F2F39")
BRAND_LIGHT = colors.HexColor("#F8F9FA")
BRAND_BORDER = colors.HexColor("#E5E7EB")

def generate_individual_pdf(student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=BRAND_RED, leading=22)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=BRAND_SLATE, leading=14)
    cell_b = ParagraphStyle('CB', fontName='Helvetica-Bold', fontSize=9, textColor=BRAND_SLATE)
    cell_r = ParagraphStyle('CR', fontName='Helvetica', fontSize=9, textColor=BRAND_SLATE)
    
    elements = []
    
    header_table = Table([
        [Paragraph("<b>INFOBEANS FOUNDATION</b>", title_style),
         Paragraph(f"<b>Session:</b> 2026<br/><b>Month:</b> {student.get('ReportMonth', 'Monthly Evaluation')}", subtitle_style)]
    ], colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10)
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    attendance_str = f"{student.get('AttendedClasses', 0)} / {student.get('TotalClasses', 0)} ({student.get('AttendancePct', 0)}%)"

    meta_data = [
        [Paragraph("<b>Student Name:</b>", cell_b), Paragraph(str(student.get('StudentName', 'N/A')), cell_r),
         Paragraph("<b>Batch:</b>", cell_b), Paragraph(str(student.get('Batch', 'N/A')), cell_r)],
        [Paragraph("<b>Roll Number:</b>", cell_b), Paragraph(str(student.get('RollNo', 'N/A')), cell_r),
         Paragraph("<b>Academic Year:</b>", cell_b), Paragraph(str(student.get('Year', 'N/A')), cell_r)],
        [Paragraph("<b>College Name:</b>", cell_b), Paragraph(str(student.get('CollegeName', 'N/A')), cell_r),
         Paragraph("<b>Overall Score:</b>", cell_b), Paragraph(f"<b>{student.get('OverallScore', 0)}%</b>", cell_b)],
        [Paragraph("<b>Attendance:</b>", cell_b), Paragraph(f"<b>{attendance_str}</b>", cell_b),
         Paragraph("<b>Parent Mobile:</b>", cell_b), Paragraph(str(student.get('ParentMobile', 'N/A')), cell_r)],
    ]
    meta_table = Table(meta_data, colWidths=[95, 175, 95, 175])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BRAND_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BRAND_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BRAND_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    score_rows = [
        [Paragraph("<b>Module</b>", cell_b), Paragraph("<b>Max Marks</b>", cell_b), Paragraph("<b>Scored</b>", cell_b), Paragraph("<b>Percentage</b>", cell_b)],
        [Paragraph("Technical Assessment", cell_r), Paragraph("100", cell_r), Paragraph(str(student.get('TechnicalMarks', 0)), cell_r), Paragraph(f"{student.get('TechnicalPct', 0)}%", cell_b)],
        [Paragraph("Soft Skills Assessment", cell_r), Paragraph("100", cell_r), Paragraph(str(student.get('SoftSkillsMarks', 0)), cell_r), Paragraph(f"{student.get('SoftSkillsPct', 0)}%", cell_b)]
    ]
    score_table = Table(score_rows, colWidths=[200, 110, 110, 120])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND_SLATE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BRAND_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<i>This is an official computer-generated student report by InfoBeans Foundation.</i>", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_college_summary_pdf(college_name, students):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=BRAND_RED)
    sub_style = ParagraphStyle('CSub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=BRAND_SLATE)
    th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white)
    tb_style = ParagraphStyle('TB', fontName='Helvetica', fontSize=8, textColor=BRAND_SLATE)
    
    elements = []
    
    total = len(students)
    third_yr = len([s for s in students if '3' in str(s.get('Year', ''))])
    fourth_yr = len([s for s in students if '4' in str(s.get('Year', ''))])
    avg_att = round(sum(s.get('AttendancePct', 0) for s in students) / (total or 1), 1)
    avg_tech = round(sum(s.get('TechnicalPct', 0) for s in students) / (total or 1), 1)
    avg_soft = round(sum(s.get('SoftSkillsPct', 0) for s in students) / (total or 1), 1)

    elements.append(Paragraph(f"<b>INFOBEANS FOUNDATION - COLLEGE CONSOLIDATED REPORT</b>", title_style))
    elements.append(Paragraph(f"<b>Institution:</b> {college_name} | <b>Total Enrolled:</b> {total} (3rd Year: {third_yr}, 4th Year: {fourth_yr}) | <b>Avg Attendance:</b> {avg_att}% | <b>Avg Tech:</b> {avg_tech}% | <b>Avg Soft Skills:</b> {avg_soft}%", sub_style))
    elements.append(Spacer(1, 10))

    table_data = [[
        Paragraph("Roll No", th_style),
        Paragraph("Student Name", th_style),
        Paragraph("Batch", th_style),
        Paragraph("Year", th_style),
        Paragraph("Attendance", th_style),
        Paragraph("Tech Marks", th_style),
        Paragraph("Soft Skills", th_style),
        Paragraph("Overall %", th_style)
    ]]

    for s in students:
        table_data.append([
            Paragraph(str(s.get('RollNo', '')), tb_style),
            Paragraph(str(s.get('StudentName', '')), tb_style),
            Paragraph(str(s.get('Batch', '')), tb_style),
            Paragraph(str(s.get('Year', '')), tb_style),
            Paragraph(f"{s.get('AttendedClasses')}/{s.get('TotalClasses')} ({s.get('AttendancePct')}%)", tb_style),
            Paragraph(f"{s.get('TechnicalMarks')} ({s.get('TechnicalPct')}%)", tb_style),
            Paragraph(f"{s.get('SoftSkillsMarks')} ({s.get('SoftSkillsPct')}%)", tb_style),
            Paragraph(f"{s.get('OverallScore')}%", tb_style)
        ])

    col_table = Table(table_data, colWidths=[70, 160, 65, 55, 120, 90, 100, 70])
    col_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND_SLATE),
        ('GRID', (0,0), (-1,-1), 0.5, BRAND_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BRAND_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(col_table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/api/parse', methods=['POST'])
def parse_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    try:
        xls = pd.ExcelFile(file)
        students = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet).fillna('')
            for idx, row in df.iterrows():
                row_dict = {str(k).strip(): v for k, v in row.to_dict().items()}
                
                name = str(row_dict.get('Student Name') or row_dict.get('Name') or f"Student {idx+1}")
                email = str(row_dict.get('Parent Email') or row_dict.get('Email') or 'pavanipandit64@gmail.com')
                mobile = str(row_dict.get('Parent Mobile') or row_dict.get('Mobile') or row_dict.get('Phone') or '7999143958')
                college = str(row_dict.get('College Name') or row_dict.get('College') or 'Unassigned College')
                college_email = str(row_dict.get('College Email') or row_dict.get('TPO Email') or 'pavanipandit64@gmail.com')
                roll = str(row_dict.get('Roll No') or row_dict.get('Roll') or f"IB-{1000+idx}")
                
                year_raw = str(row_dict.get('Year') or row_dict.get('Academic Year') or '3rd Year')
                year = '3rd Year' if '3' in year_raw else ('4th Year' if '4' in year_raw else year_raw)
                
                total_classes = float(str(row_dict.get('Total Classes', 0)).replace('%', '') or 0)
                attended_classes = float(str(row_dict.get('Attended Classes', 0)).replace('%', '') or 0)
                att_pct = round((attended_classes / total_classes) * 100, 1) if total_classes > 0 else float(str(row_dict.get('Attendance %', 0)).replace('%', '') or 0.0)

                tech_marks = float(str(row_dict.get('Technical Marks (100)', 0)).replace('%', '') or 0.0)
                tech_pct = float(str(row_dict.get('Technical %', tech_marks)).replace('%', '') or tech_marks)

                soft_marks = float(str(row_dict.get('Soft Skills Marks (100)', 0)).replace('%', '') or 0.0)
                soft_pct = float(str(row_dict.get('Soft Skills %', soft_marks)).replace('%', '') or soft_marks)

                overall_score = float(str(row_dict.get('Overall Score %', round((tech_marks * 0.6) + (soft_marks * 0.4), 1))).replace('%', '') or 0.0)

                students.append({
                    "id": f"{sheet}_{idx}",
                    "StudentName": name,
                    "RollNo": roll,
                    "ParentEmail": email,
                    "ParentMobile": mobile,
                    "CollegeName": college,
                    "CollegeEmail": college_email,
                    "Year": year,
                    "Batch": sheet,
                    "TotalClasses": int(total_classes),
                    "AttendedClasses": int(attended_classes),
                    "AttendancePct": att_pct,
                    "TechnicalMarks": tech_marks,
                    "TechnicalPct": tech_pct,
                    "SoftSkillsMarks": soft_marks,
                    "SoftSkillsPct": soft_pct,
                    "OverallScore": overall_score
                })
        return jsonify({"success": True, "total": len(students), "students": students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    student_data = request.json or {}
    pdf_buf = generate_individual_pdf(student_data)
    return send_file(pdf_buf, as_attachment=True, download_name=f"{student_data.get('RollNo', 'Student')}_Report.pdf", mimetype='application/pdf')

@app.route('/api/download-college-pdf', methods=['POST'])
def download_college_pdf():
    payload = request.json or {}
    college = payload.get('college', 'College')
    students = payload.get('students', [])
    pdf_buf = generate_college_summary_pdf(college, students)
    return send_file(pdf_buf, as_attachment=True, download_name=f"{college.replace(' ', '_')}_Consolidated_Report.pdf", mimetype='application/pdf')

@app.route('/api/download-college-excel', methods=['POST'])
def download_college_excel():
    payload = request.json or {}
    students = payload.get('students', [])
    college = payload.get('college', 'College')
    
    df = pd.DataFrame(students)
    cols = ['RollNo', 'StudentName', 'CollegeName', 'Year', 'Batch', 'AttendedClasses', 'TotalClasses', 'AttendancePct', 'TechnicalMarks', 'TechnicalPct', 'SoftSkillsMarks', 'SoftSkillsPct', 'OverallScore', 'ParentMobile', 'ParentEmail', 'CollegeEmail']
    export_df = df[[c for c in cols if c in df.columns]]
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name="College Report")
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{college.replace(' ', '_')}_Records.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/api/send-email', methods=['POST'])
def send_email():
    payload = request.json or {}
    student = payload.get('student', {})
    config = payload.get('config', {})
    sender_email = (config.get('sender_email') or '').strip()
    app_pwd = (config.get('app_password') or '').replace(" ", "").strip()
    target_email = (student.get('ParentEmail') or 'pavanipandit64@gmail.com').strip()

    if not sender_email or not app_pwd:
        return jsonify({'error': 'Please enter Sender Gmail and 16-character App Password in the sidebar.'}), 400

    try:
        pdf_buf = generate_individual_pdf(student)
        msg = MIMEMultipart()
        msg['From'] = f"InfoBeans Foundation <{sender_email}>"
        msg['To'] = target_email
        msg['Subject'] = f"Student Progress Report - {student.get('StudentName')} ({student.get('RollNo')})"

        body = f"""Dear Parent,\n\nPlease find attached the official monthly academic progress report of {student.get('StudentName')} ({student.get('RollNo')}), {student.get('CollegeName')}.\n\nBatch: {student.get('Batch')} | Academic Year: {student.get('Year')}\nAttendance: {student.get('AttendedClasses')}/{student.get('TotalClasses')} ({student.get('AttendancePct')}%)\nTechnical Score: {student.get('TechnicalMarks')}/100 ({student.get('TechnicalPct')}%)\nSoft Skills Score: {student.get('SoftSkillsMarks')}/100 ({student.get('SoftSkillsPct')}%)\nOverall Score: {student.get('OverallScore')}%\n\nWarm regards,\nInfoBeans Foundation Team"""
        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_buf.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{student.get("RollNo")}_Report.pdf"')
        msg.attach(part)

        # Port 465 SSL connection for Vercel stability
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20)
        server.login(sender_email, app_pwd)
        server.send_message(msg)
        server.quit()
        return jsonify({'success': True, 'to': target_email})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'error': 'Gmail Authentication Failed! Check your 16-digit App Password & 2-Step Verification.'}), 401
    except Exception as e:
        return jsonify({'error': f"SMTP Error: {str(e)}"}), 500

@app.route('/api/send-college-email', methods=['POST'])
def send_college_email():
    payload = request.json or {}
    college = payload.get('college', 'College')
    college_email = (payload.get('college_email') or 'pavanipandit64@gmail.com').strip()
    students = payload.get('students', [])
    config = payload.get('config', {})
    
    sender_email = (config.get('sender_email') or '').strip()
    app_pwd = (config.get('app_password') or '').replace(" ", "").strip()

    if not sender_email or not app_pwd:
        return jsonify({'error': 'Sender Gmail or 16-character App Password missing in sidebar.'}), 400

    try:
        pdf_buf = generate_college_summary_pdf(college, students)
        
        df = pd.DataFrame(students)
        cols = ['RollNo', 'StudentName', 'CollegeName', 'Year', 'Batch', 'AttendedClasses', 'TotalClasses', 'AttendancePct', 'TechnicalMarks', 'TechnicalPct', 'SoftSkillsMarks', 'SoftSkillsPct', 'OverallScore', 'ParentMobile', 'ParentEmail', 'CollegeEmail']
        export_df = df[[c for c in cols if c in df.columns]]
        xls_buf = io.BytesIO()
        with pd.ExcelWriter(xls_buf, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name="Batch Summary")
        xls_buf.seek(0)

        msg = MIMEMultipart()
        msg['From'] = f"InfoBeans Foundation <{sender_email}>"
        msg['To'] = college_email
        msg['Subject'] = f"Consolidated Student Performance & Attendance Report - {college}"

        body = f"""Respected Training & Placement Officer / College Authority,\n\nPlease find attached the consolidated student performance report and Excel records sheet for students enrolled at InfoBeans Foundation from {college}.\n\nTotal Enrolled Students: {len(students)}\nAttached:\n1. PDF Performance Summary Report\n2. Detailed Student Attendance & Marks Excel Sheet\n\nWarm regards,\nInfoBeans Foundation Team"""
        msg.attach(MIMEText(body, 'plain'))

        part1 = MIMEBase('application', 'octet-stream')
        part1.set_payload(pdf_buf.read())
        encoders.encode_base64(part1)
        part1.add_header('Content-Disposition', f'attachment; filename="{college.replace(" ", "_")}_Consolidated_Report.pdf"')
        msg.attach(part1)

        part2 = MIMEBase('application', 'octet-stream')
        part2.set_payload(xls_buf.read())
        encoders.encode_base64(part2)
        part2.add_header('Content-Disposition', f'attachment; filename="{college.replace(" ", "_")}_Student_Records.xlsx"')
        msg.attach(part2)

        # Port 465 SSL connection
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=25)
        server.login(sender_email, app_pwd)
        server.send_message(msg)
        server.quit()
        return jsonify({'success': True, 'to': college_email})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'error': 'Gmail Authentication Failed! Check your 16-digit App Password.'}), 401
    except Exception as e:
        return jsonify({'error': f"SMTP Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
