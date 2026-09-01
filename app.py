import streamlit as st
import pandas as pd
import io
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="InfoBeans Foundation - Progress Portal",
    page_icon="https://infobeansfoundation.org/wp-content/uploads/2022/07/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- CLEAN CORPORATE UI STYLING -----------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0F172A !important;
    }
    
    /* Background force clean */
    .stApp {
        background-color: #F8FAFC !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    /* Header Container */
    .header-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .portal-heading {
        font-size: 24px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin: 0;
    }
    
    .portal-desc {
        font-size: 13px;
        color: #64748B;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        padding: 16px 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Primary Red Button */
    .stButton > button[kind="primary"] {
        background-color: #EA1B3D !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(234, 27, 61, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #D01433 !important;
        transform: translateY(-1px) !important;
    }

    /* WhatsApp direct anchor button */
    .wa-link-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        background-color: #25D366;
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 12px;
        padding: 8px 12px;
        border-radius: 8px;
        text-decoration: none !important;
        box-shadow: 0 2px 6px rgba(37, 211, 102, 0.25);
        transition: all 0.2s;
    }
    .wa-link-btn:hover {
        background-color: #1EBE5D;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    /* Card Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    </style>
""", unsafe_allow_html=True)

BRAND_RED = colors.HexColor("#EA1B3D")
BRAND_SLATE = colors.HexColor("#1E293B")
BRAND_LIGHT = colors.HexColor("#F8FAFC")
BRAND_BORDER = colors.HexColor("#E2E8F0")

# ----------------- PDF GENERATORS -----------------
def generate_student_pdf(student, report_month):
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
         Paragraph(f"<b>Session:</b> 2026<br/><b>Month:</b> {report_month}", subtitle_style)]
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

def generate_college_pdf(college_name, students):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=BRAND_RED)
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

    elements.append(Paragraph(f"<b>INFOBEANS FOUNDATION - CONSOLIDATED INSTITUTION REPORT</b>", title_style))
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

def generate_college_excel(students):
    df = pd.DataFrame(students)
    cols = ['RollNo', 'StudentName', 'CollegeName', 'Year', 'Batch', 'AttendedClasses', 'TotalClasses', 'AttendancePct', 'TechnicalMarks', 'TechnicalPct', 'SoftSkillsMarks', 'SoftSkillsPct', 'OverallScore', 'ParentMobile', 'ParentEmail', 'CollegeEmail']
    export_df = df[[c for c in cols if c in df.columns]]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name="Student Records")
    buf.seek(0)
    return buf

# ----------------- EMAIL DISPATCHER -----------------
def send_parent_email(student, report_month, sender_email, app_pwd):
    pdf_buf = generate_student_pdf(student, report_month)
    target_email = student.get('ParentEmail') or 'pavanipandit64@gmail.com'

    msg = MIMEMultipart()
    msg['From'] = f"InfoBeans Foundation <{sender_email}>"
    msg['To'] = target_email
    msg['Subject'] = f"Student Progress Report - {student.get('StudentName')} ({student.get('RollNo')})"

    body = f"""Dear Parent,\n\nPlease find attached the monthly progress report of {student.get('StudentName')} ({student.get('RollNo')}), {student.get('CollegeName')}.\n\nBatch: {student.get('Batch')} | Academic Year: {student.get('Year')}\nAttendance: {student.get('AttendedClasses')}/{student.get('TotalClasses')} ({student.get('AttendancePct')}%)\nTechnical Score: {student.get('TechnicalMarks')}/100 ({student.get('TechnicalPct')}%)\nSoft Skills Score: {student.get('SoftSkillsMarks')}/100 ({student.get('SoftSkillsPct')}%)\nOverall Score: {student.get('OverallScore')}%\n\nWarm regards,\nInfoBeans Foundation Team"""
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_buf.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{student.get("RollNo")}_Report.pdf"')
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20) as server:
        server.login(sender_email.strip(), app_pwd.strip().replace(" ", ""))
        server.send_message(msg)

def send_college_email(college_name, college_email, students, report_month, sender_email, app_pwd):
    pdf_buf = generate_college_pdf(college_name, students)
    xls_buf = generate_college_excel(students)

    msg = MIMEMultipart()
    msg['From'] = f"InfoBeans Foundation <{sender_email}>"
    msg['To'] = college_email
    msg['Subject'] = f"Consolidated Student Performance & Attendance Report - {college_name}"

    body = f"""Respected Training & Placement Officer / College Authority,\n\nPlease find attached the consolidated student performance report and Excel sheet for students enrolled at InfoBeans Foundation from {college_name}.\n\nTotal Enrolled Students: {len(students)}\nEvaluation Month: {report_month}\n\nAttached:\n1. PDF Performance Summary Report\n2. Detailed Student Attendance & Marks Excel Sheet\n\nWarm regards,\nInfoBeans Foundation Team"""
    msg.attach(MIMEText(body, 'plain'))

    part1 = MIMEBase('application', 'octet-stream')
    part1.set_payload(pdf_buf.read())
    encoders.encode_base64(part1)
    part1.add_header('Content-Disposition', f'attachment; filename="{college_name.replace(" ", "_")}_Consolidated_Report.pdf"')
    msg.attach(part1)

    part2 = MIMEBase('application', 'octet-stream')
    part2.set_payload(xls_buf.read())
    encoders.encode_base64(part2)
    part2.add_header('Content-Disposition', f'attachment; filename="{college_name.replace(" ", "_")}_Student_Records.xlsx"')
    msg.attach(part2)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=25) as server:
        server.login(sender_email.strip(), app_pwd.strip().replace(" ", ""))
        server.send_message(msg)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://infobeansfoundation.org/wp-content/uploads/2022/07/logo.png", width=190)
    st.markdown("<p style='font-size:12px;color:#64748B;font-weight:600;margin-top:-6px;'>Progress & Dispatch Portal</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Multi-Batch Excel File", type=["xlsx", "xls"])
    
    st.markdown("---")
    st.markdown("<p style='font-size:11px;font-weight:800;color:#94A3B8;text-transform:uppercase;'>⚙️ Credentials & Context</p>", unsafe_allow_html=True)
    report_month = st.text_input("Evaluation Month", value="September 2026")
    sender_email = st.text_input("Sender Gmail Address", value="pavanipandit64@gmail.com")
    app_password = st.text_input("16-Digit Gmail App Password", type="password", help="Generate from: Google Account > Security > App Passwords")

# ----------------- MAIN HEADER BOX -----------------
st.markdown("""
    <div class="header-box">
        <div>
            <h1 class="portal-heading">Student & College Evaluation Hub</h1>
            <p class="portal-desc">Multi-batch consolidation, 3rd/4th year segregation, WhatsApp direct parent updates & TPO reports.</p>
        </div>
        <img src="https://infobeansfoundation.org/wp-content/uploads/2022/07/logo.png" style="height: 48px; object-fit: contain;" />
    </div>
""", unsafe_allow_html=True)

if uploaded_file is None:
    st.info("📌 Please upload the multi-batch Excel workbook from the sidebar to activate the reporting engine.")
    st.stop()

# ----------------- DATA PROCESSING -----------------
try:
    xls = pd.ExcelFile(uploaded_file)
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
except Exception as e:
    st.error(f"Error parsing workbook: {e}")
    st.stop()

# ----------------- FILTERS BAR -----------------
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 2.6])

    with col_f1:
        batch_list = ["ALL"] + sorted(list(set(s['Batch'] for s in students)))
        selected_batch = st.selectbox("Select Batch", batch_list)

    with col_f2:
        selected_year = st.selectbox("Academic Year", ["ALL", "3rd Year", "4th Year"])

    filtered_temp = [s for s in students if (selected_batch == "ALL" or s['Batch'] == selected_batch) and (selected_year == "ALL" or s['Year'] == selected_year)]
    all_colleges = sorted(list(set(s['CollegeName'] for s in filtered_temp)))

    with col_f3:
        selected_colleges = st.multiselect("Filter Colleges (Add/Subtract)", all_colleges, default=all_colleges)

filtered_students = [s for s in filtered_temp if s['CollegeName'] in selected_colleges]

# ----------------- METRIC CARDS -----------------
m1, m2, m3, m4, m5 = st.columns(5)
total_count = len(filtered_students)
y3_count = len([s for s in filtered_students if '3' in s['Year']])
y4_count = len([s for s in filtered_students if '4' in s['Year']])
avg_att = round(sum(s['AttendancePct'] for s in filtered_students) / (total_count or 1), 1)
avg_tech = round(sum(s['TechnicalPct'] for s in filtered_students) / (total_count or 1), 1)
avg_soft = round(sum(s['SoftSkillsPct'] for s in filtered_students) / (total_count or 1), 1)

m1.metric("Total Enrolled", total_count)
m2.metric("3rd / 4th Year", f"{y3_count} / {y4_count}")
m3.metric("Avg Attendance", f"{avg_att}%")
m4.metric("Avg Technical", f"{avg_tech}%")
m5.metric("Avg Soft Skills", f"{avg_soft}%")

# ----------------- TOP MASTER DISPATCH BUTTONS -----------------
st.markdown("<br/>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("<p style='font-size:13px;font-weight:800;color:#0F172A;margin-bottom:10px;'>⚡ MASTER DISPATCH ACTIONS (FILTERED RECORDS)</p>", unsafe_allow_html=True)
    act_c1, act_c2 = st.columns(2)

    with act_c1:
        if st.button("✉️ Send Individual Progress Reports to All Filtered Parents", use_container_width=True, type="primary"):
            if not app_password:
                st.warning("⚠️ Enter your 16-Digit Gmail App Password in the sidebar.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                for i, st_data in enumerate(filtered_students):
                    status_text.text(f"Sending ({i+1}/{total_count}): {st_data['StudentName']} to {st_data['ParentEmail']}...")
                    try:
                        send_parent_email(st_data, report_month, sender_email, app_password)
                        success_count += 1
                    except Exception as e:
                        st.error(f"Failed on {st_data['StudentName']}: {e}")
                        break
                    progress_bar.progress((i + 1) / total_count)
                status_text.success(f"✅ Dispatched {success_count} parent reports successfully via Email!")

    with act_c2:
        if st.button("🏛️ Send Consolidated PDF + Excel to All Selected Colleges", use_container_width=True):
            if not app_password:
                st.warning("⚠️ Enter your 16-Digit Gmail App Password in the sidebar.")
            else:
                col_list = sorted(list(set(s['CollegeName'] for s in filtered_students)))
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_col_count = 0
                for i, col_name in enumerate(col_list):
                    c_students = [s for s in filtered_students if s['CollegeName'] == col_name]
                    c_email = c_students[0].get('CollegeEmail') or 'pavanipandit64@gmail.com'
                    status_text.text(f"Sending ({i+1}/{len(col_list)}): {col_name} to {c_email}...")
                    try:
                        send_college_email(col_name, c_email, c_students, report_month, sender_email, app_password)
                        success_col_count += 1
                    except Exception as e:
                        st.error(f"Failed on {col_name}: {e}")
                        break
                    progress_bar.progress((i + 1) / len(col_list))
                status_text.success(f"✅ Dispatched consolidated packets to {success_col_count} institutions!")

# ----------------- SECTION 1: COLLEGE CARDS -----------------
st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size:16px;font-weight:800;color:#0F172A;'>🏛️ Institution / TPO Performance Packets</h3>", unsafe_allow_html=True)
col_cards = sorted(list(set(s['CollegeName'] for s in filtered_students)))

if not col_cards:
    st.info("No institutions in current filter.")
else:
    grid_cols = st.columns(2)
    for idx, c_name in enumerate(col_cards):
        c_students = [s for s in filtered_students if s['CollegeName'] == c_name]
        c_y3 = len([s for s in c_students if '3' in s['Year']])
        c_y4 = len([s for s in c_students if '4' in s['Year']])
        c_email = c_students[0].get('CollegeEmail') or 'pavanipandit64@gmail.com'
        
        with grid_cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"<p style='font-size:14px;font-weight:800;color:#0F172A;margin:0;'>{c_name} <span style='font-size:11px;background:#EEF2FF;color:#4F46E5;padding:2px 8px;border-radius:6px;font-weight:700;margin-left:6px;'>{len(c_students)} Enrolled</span></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:12px;color:#64748B;margin-top:2px;'>3rd Year: <b>{c_y3}</b> &nbsp;|&nbsp; 4th Year: <b>{c_y4}</b> &nbsp;|&nbsp; TPO: <span style='font-family:monospace;color:#334155;'>{c_email}</span></p>", unsafe_allow_html=True)
                
                b1, b2, b3 = st.columns(3)
                c_pdf = generate_college_pdf(c_name, c_students)
                b1.download_button("📄 PDF Summary", data=c_pdf, file_name=f"{c_name}_Report.pdf", mime="application/pdf", key=f"cpdf_{idx}", use_container_width=True)
                
                c_xls = generate_college_excel(c_students)
                b2.download_button("📊 Excel Sheet", data=c_xls, file_name=f"{c_name}_Records.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"cxls_{idx}", use_container_width=True)
                
                if b3.button("✉️ Send TPO", key=f"cmail_{idx}", use_container_width=True):
                    if not app_password:
                        st.warning("Enter App Password.")
                    else:
                        with st.spinner("Dispatching..."):
                            try:
                                send_college_email(c_name, c_email, c_students, report_month, sender_email, app_password)
                                st.success("Delivered!")
                            except Exception as e:
                                st.error(f"Error: {e}")

# ----------------- SECTION 2: INDIVIDUAL STUDENTS TABLE & WHATSAPP -----------------
st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size:16px;font-weight:800;color:#0F172A;'>👨‍🎓 Student Evaluation & Parent Direct Dispatch Matrix</h3>", unsafe_allow_html=True)

for idx, s in enumerate(filtered_students):
    with st.container(border=True):
        row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([2.5, 2.2, 2.5, 1.3, 2.5])
        
        with row_c1:
            st.markdown(f"<p style='font-size:13px;font-weight:800;color:#0F172A;margin:0;'>{s['StudentName']} <span style='font-size:11px;font-family:monospace;color:#64748B;'>({s['RollNo']})</span></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:11px;color:#64748B;font-family:monospace;margin-top:2px;'>📱 {s['ParentMobile']} &nbsp;|&nbsp; ✉️ {s['ParentEmail']}</p>", unsafe_allow_html=True)
            
        with row_c2:
            st.markdown(f"<p style='font-size:12px;font-weight:700;color:#334155;margin:0;'>{s['CollegeName']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:11px;color:#64748B;margin-top:2px;'>Batch: <b>{s['Batch']}</b> ({s['Year']})</p>", unsafe_allow_html=True)
            
        with row_c3:
            st.markdown(f"<p style='font-size:12px;color:#0F172A;margin:0;'>Attendance: <b>{s['AttendedClasses']}/{s['TotalClasses']} ({s['AttendancePct']}%)</b></p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:11px;color:#64748B;margin-top:2px;'>Tech: <b style='color:#EA1B3D;'>{s['TechnicalPct']}%</b> &nbsp;|&nbsp; Soft Skills: <b style='color:#059669;'>{s['SoftSkillsPct']}%</b></p>", unsafe_allow_html=True)
            
        with row_c4:
            st.markdown(f"<p style='font-size:16px;font-weight:800;color:#EA1B3D;font-family:monospace;margin:0;'>{s['OverallScore']}%</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:10px;color:#94A3B8;text-transform:uppercase;font-weight:700;'>Overall</p>", unsafe_allow_html=True)
            
        with row_c5:
            wa_text = f"*INFOBEANS FOUNDATION - Progress Report*\n\nDear Parent,\nProgress Report for *{s['StudentName']}* ({s['RollNo']}), *{s['CollegeName']}* for {report_month}:\n- Batch: {s['Batch']} ({s['Year']})\n- Attendance: {s['AttendedClasses']}/{s['TotalClasses']} ({s['AttendancePct']}%)\n- Technical: {s['TechnicalPct']}%\n- Soft Skills: {s['SoftSkillsPct']}%\n- Overall: {s['OverallScore']}%\n\nWarm regards,\n*InfoBeans Foundation Team*"
            wa_url = f"https://wa.me/91{s['ParentMobile']}?text={urllib.parse.quote(wa_text)}"
            
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">💬 Send WhatsApp</a>', unsafe_allow_html=True)
            
            wb_col1, wb_col2 = st.columns(2)
            pdf_data = generate_student_pdf(s, report_month)
            wb_col1.download_button("📄 PDF", data=pdf_data, file_name=f"{s['RollNo']}_Report.pdf", mime="application/pdf", key=f"spdf_{idx}", use_container_width=True)
            
            if wb_col2.button("✉️ Email", key=f"smail_{idx}", use_container_width=True):
                if not app_password:
                    st.warning("Enter App Password.")
                else:
                    with st.spinner("Sending..."):
                        try:
                            send_parent_email(s, report_month, sender_email, app_password)
                            st.success("Sent!")
                        except Exception as e:
                            st.error(f"Error: {e}")
