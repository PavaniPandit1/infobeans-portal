import os
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)
CORS(app)

# Serve Frontend HTML
@app.route('/')
def home():
    return send_file(os.path.join(os.path.dirname(__file__), '../public/index.html'))

BRAND_RED = colors.HexColor("#EA1B3D")
BRAND_SLATE = colors.HexColor("#2F2F39")
BRAND_LIGHT = colors.HexColor("#F8F9FA")
BRAND_BORDER = colors.HexColor("#E5E7EB")

def generate_pdf_buffer(student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('HeaderTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=BRAND_RED, leading=22)
    subtitle_style = ParagraphStyle('HeaderSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=BRAND_SLATE, leading=14)
    cell_bold = ParagraphStyle('CellB', fontName='Helvetica-Bold', fontSize=9, textColor=BRAND_SLATE)
    cell_regular = ParagraphStyle('CellR', fontName='Helvetica', fontSize=9, textColor=BRAND_SLATE)
    
    elements = []

    header_table = Table([
        [
            Paragraph("<b>INFOBEANS FOUNDATION</b>", title_style),
            Paragraph(f"<b>Session:</b> 2026<br/><b>Month:</b> {student.get('ReportMonth', 'September 2026')}", subtitle_style)
        ]
    ], colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    attendance_str = f"{student.get('AttendedClasses', 0)} / {student.get('TotalClasses', 0)} ({student.get('AttendancePct', 0)}%)"

    meta_data = [
        [Paragraph("<b>Student Name:</b>", cell_bold), Paragraph(str(student.get('StudentName', 'N/A')), cell_regular),
         Paragraph("<b>Batch:</b>", cell_bold), Paragraph(str(student.get('Batch', 'N/A')), cell_regular)],
        [Paragraph("<b>Roll Number:</b>", cell_bold), Paragraph(str(student.get('RollNo', 'N/A')), cell_regular),
         Paragraph("<b>College:</b>", cell_bold), Paragraph(str(student.get('CollegeName', 'N/A')), cell_regular)],
        [Paragraph("<b>Attendance:</b>", cell_bold), Paragraph(f"<b>{attendance_str}</b>", cell_bold),
         Paragraph("<b>Overall Score:</b>", cell_bold), Paragraph(f"<b>{student.get('OverallScore', 0)}%</b>", cell_bold)],
    ]
    meta_table = Table(meta_data, colWidths=[95, 175, 95, 175])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BRAND_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    assessments = student.get('Assessments', [])
    score_rows = [[
        Paragraph("<b>Assessment Module</b>", cell_bold),
        Paragraph("<b>Max Marks</b>", cell_bold),
        Paragraph("<b>Marks Scored</b>", cell_bold),
        Paragraph("<b>Percentage</b>", cell_bold)
    ]]
    
    for item in assessments:
        score_rows.append([
            Paragraph(str(item.get('name', 'Module')), cell_regular),
            Paragraph(str(item.get('max', 100)), cell_regular),
            Paragraph(str(item.get('scored', 0)), cell_regular),
            Paragraph(f"{item.get('pct', 0)}%", cell_bold)
        ])

    score_table = Table(score_rows, colWidths=[200, 110, 110, 120])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_SLATE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 25))

    elements.append(Paragraph("<i>This is an official computer-generated progress document by InfoBeans Foundation.</i>", subtitle_style))
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
                email = str(row_dict.get('Parent Email') or row_dict.get('Email') or '')
                college = str(row_dict.get('College Name') or row_dict.get('College') or 'N/A')
                college_email = str(row_dict.get('College Email') or row_dict.get('TPO Email') or '')
                roll = str(row_dict.get('Roll No') or row_dict.get('Roll') or f"IB-{1000+idx}")
                
                total_classes = float(str(row_dict.get('Total Classes', 0)).replace('%', '') or 0)
                attended_classes = float(str(row_dict.get('Attended Classes', 0)).replace('%', '') or 0)
                if total_classes > 0:
                    att_pct = round((attended_classes / total_classes) * 100, 1)
                else:
                    att_pct = float(str(row_dict.get('Attendance %', 0)).replace('%', '') or 0.0)

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
                    "CollegeName": college,
                    "CollegeEmail": college_email,
                    "Batch": sheet,
                    "TotalClasses": int(total_classes),
                    "AttendedClasses": int(attended_classes),
                    "AttendancePct": att_pct,
                    "TechnicalMarks": tech_marks,
                    "TechnicalPct": tech_pct,
                    "SoftSkillsMarks": soft_marks,
                    "SoftSkillsPct": soft_pct,
                    "OverallScore": overall_score,
                    "Assessments": [
                        {"name": "Technical Assessment", "max": 100, "scored": tech_marks, "pct": tech_pct},
                        {"name": "Soft Skills Assessment", "max": 100, "scored": soft_marks, "pct": soft_pct}
                    ]
                })
        return jsonify({"success": True, "total": len(students), "students": students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    student_data = request.json or {}
    pdf_buffer = generate_pdf_buffer(student_data)
    filename = f"{student_data.get('RollNo', 'Report')}_Progress_Report.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/api/send-email', methods=['POST'])
def send_email():
    payload = request.json or {}
    student = payload.get('student', {})
    config = payload.get('config', {})
    
    sender_email = config.get('sender_email')
    app_pwd = config.get('app_password')
    parent_email = student.get('ParentEmail')

    if not sender_email or not app_pwd or not parent_email:
        return jsonify({'error': 'Sender credentials or Parent Email missing'}), 400

    try:
        pdf_buffer = generate_pdf_buffer(student)
        msg = MIMEMultipart()
        msg['From'] = f"InfoBeans Foundation <{sender_email}>"
        msg['To'] = parent_email
        msg['Subject'] = f"Monthly Student Progress Report - {student.get('StudentName')}"

        body = f"""Dear Parent,\n\nPlease find attached the official monthly academic progress report of {student.get('StudentName')} ({student.get('RollNo')}).\n\nAttendance: {student.get('AttendedClasses')} / {student.get('TotalClasses')} ({student.get('AttendancePct')}%)\nTechnical Score: {student.get('TechnicalMarks')}/100 ({student.get('TechnicalPct')}%)\nSoft Skills Score: {student.get('SoftSkillsMarks')}/100 ({student.get('SoftSkillsPct')}%)\n\nWarm regards,\nInfoBeans Foundation Team"""
        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_buffer.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{student.get("RollNo")}_Report.pdf"')
        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_pwd.replace(" ", ""))
        server.send_message(msg)
        server.quit()

        return jsonify({'success': True, 'message': f'Report sent to {parent_email}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)