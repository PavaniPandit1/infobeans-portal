import streamlit as st
import pandas as pd
import io
import smtplib
import re
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(
    page_title="InfoBeans Foundation Portal",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    elements.append(Paragraph("<i>This is an official computer-generated evaluation report by InfoBeans Foundation.</i>", subtitle_style))

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

# ----------------- EMAIL DISPATCHER (SAFE FALLBACK) -----------------
def execute_smtp_send(to_email, subject, body_text, attachments, sender_email, app_pwd, is_simulated=False):
    if is_simulated:
        return True
    
    clean_sender = str(sender_email).strip()
    clean_pwd = re.sub(r'[^a-zA-Z0-9]', '', str(app_pwd)).strip()
    clean_to = str(to_email).strip()

    msg = MIMEMultipart()
    msg['From'] = f"InfoBeans Foundation <{clean_sender}>"
    msg['To'] = clean_to
    msg['Subject'] = subject
    msg.attach(MIMEText(body_text, 'plain'))

    for filename, file_buffer in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file_buffer.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20) as server:
        server.login(clean_sender, clean_pwd)
        server.send_message(msg)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
        <div style="background-color:#EA1B3D; padding:12px; border-radius:8px; text-align:center; margin-bottom:12px;">
            <span style="color:white; font-size:18px; font-weight:900; letter-spacing:1px;">InfoBeans</span>
            <span style="color:white; font-size:13px; font-weight:400; display:block;">FOUNDATION</span>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Multi-Batch Excel File", type=["xlsx", "xls"])
    
    st.divider()
    st.markdown("### ⚙️ Dispatch Settings")
    report_month = st.text_input("Evaluation Month", value="September 2026")
    sender_email = st.text_input("Sender Gmail", value="xyz12097@gmail.com")
    app_password = st.text_input("App Password (Optional)", type="password")
    
    demo_mode = st.toggle("⚡ Fast Presentation Demo Mode", value=True, help="Turn ON during presentations for 100% instant 0-error dispatch without cloud SMTP blocks.")

# ----------------- MAIN TITLE -----------------
st.markdown("""
    <div style="border-left: 5px solid #EA1B3D; padding-left: 15px; margin-bottom: 20px;">
        <h1 style="margin:0; font-size: 26px; font-weight:800; color:#EA1B3D;">InfoBeans Foundation</h1>
        <p style="margin:2px 0 0 0; font-size: 14px; opacity: 0.8;">Student Progress & Multi-College Reporting Portal</p>
    </div>
""", unsafe_allow_html=True)

if uploaded_file is None:
    st.info("👆 Please upload the Excel file (`InfoBeans_Shuffled_Testing_MultiBatch.xlsx`) from the sidebar to activate.")
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
    st.error(f"Error reading file: {e}")
    st.stop()

# ----------------- FILTERS BAR -----------------
with st.container():
    col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 2.6])

    with col_f1:
        batch_list = ["ALL"] + sorted(list(set(s['Batch'] for s in students)))
        selected_batch = st.selectbox("Batch Filter", batch_list)

    with col_f2:
        selected_year = st.selectbox("Academic Year", ["ALL", "3rd Year", "4th Year"])

    filtered_temp = [s for s in students if (selected_batch == "ALL" or s['Batch'] == selected_batch) and (selected_year == "ALL" or s['Year'] == selected_year)]
    all_colleges = sorted(list(set(s['CollegeName'] for s in filtered_temp)))

    with col_f3:
        selected_colleges = st.multiselect("Colleges Filter", all_colleges, default=all_colleges)

filtered_students = [s for s in filtered_temp if s['CollegeName'] in selected_colleges]

# ----------------- METRIC CARDS -----------------
m1, m2, m3, m4, m5 = st.columns(5)
total_count = len(filtered_students)
y3_count = len([s for s in filtered_students if '3' in s['Year']])
y4_count = len([s for s in filtered_students if '4' in s['Year']])
avg_att = round(sum(s['AttendancePct'] for s in filtered_students) / (total_count or 1), 1)
avg_tech = round(sum(s['TechnicalPct'] for s in filtered_students) / (total_count or 1), 1)
avg_soft = round(sum(s['SoftSkillsPct'] for s in filtered_students) / (total_count or 1), 1)

m1.metric("Total Students", total_count)
m2.metric("3rd / 4th Year", f"{y3_count} / {y4_count}")
m3.metric("Avg Attendance", f"{avg_att}%")
m4.metric("Avg Tech Score", f"{avg_tech}%")
m5.metric("Avg Soft Skills", f"{avg_soft}%")

st.divider()

# ----------------- BULK DISPATCH BUTTONS -----------------
st.subheader("⚡ Bulk Dispatch Operations")
act_c1, act_c2 = st.columns(2)

with act_c1:
    if st.button("📧 Send Individual Email to All Filtered Parents", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        success_count = 0
        for i, st_data in enumerate(filtered_students):
            status_text.text(f"Dispatching ({i+1}/{total_count}): {st_data['StudentName']} -> {st_data['ParentEmail']}...")
            try:
                execute_smtp_send(
                    st_data['ParentEmail'],
                    f"Student Progress Report - {st_data['StudentName']}",
                    f"Dear Parent,\n\nPlease find attached the monthly progress report for {st_data['StudentName']}.",
                    [(f"{st_data['RollNo']}_Report.pdf", generate_student_pdf(st_data, report_month))],
                    sender_email, app_password, is_simulated=demo_mode
                )
                success_count += 1
            except Exception as e:
                st.error(f"Error on {st_data['StudentName']}: {e}")
                break
            progress_bar.progress((i + 1) / total_count)
        if success_count == total_count:
            status_text.success(f"✅ Successfully dispatched all {success_count} parent progress reports!")

with act_c2:
    if st.button("🏛️ Send Consolidated PDF + Excel to All Colleges", use_container_width=True):
        col_list = sorted(list(set(s['CollegeName'] for s in filtered_students)))
        progress_bar = st.progress(0)
        status_text = st.empty()
        success_col_count = 0
        for i, col_name in enumerate(col_list):
            c_students = [s for s in filtered_students if s['CollegeName'] == col_name]
            c_email = c_students[0].get('CollegeEmail') or 'pavanipandit64@gmail.com'
            status_text.text(f"Dispatching ({i+1}/{len(col_list)}): {col_name} -> {c_email}...")
            try:
                execute_smtp_send(
                    c_email,
                    f"Consolidated Report - {col_name}",
                    f"Respected TPO,\n\nPlease find attached the monthly consolidated student report.",
                    [
                        (f"{col_name}_Report.pdf", generate_college_pdf(col_name, c_students)),
                        (f"{col_name}_Records.xlsx", generate_college_excel(c_students))
                    ],
                    sender_email, app_password, is_simulated=demo_mode
                )
                success_col_count += 1
            except Exception as e:
                st.error(f"Error on {col_name}: {e}")
                break
            progress_bar.progress((i + 1) / len(col_list))
        if success_col_count == len(col_list):
            status_text.success(f"✅ Successfully dispatched dossiers to all {success_col_count} institutions!")

st.divider()

# ----------------- SECTION 1: COLLEGE CARDS -----------------
st.subheader("🏛️ Institution / TPO Reports")
col_cards = sorted(list(set(s['CollegeName'] for s in filtered_students)))

if not col_cards:
    st.info("No colleges matching filter.")
else:
    grid_cols = st.columns(2)
    for idx, c_name in enumerate(col_cards):
        c_students = [s for s in filtered_students if s['CollegeName'] == c_name]
        c_y3 = len([s for s in c_students if '3' in s['Year']])
        c_y4 = len([s for s in c_students if '4' in s['Year']])
        c_email = c_students[0].get('CollegeEmail') or 'pavanipandit64@gmail.com'
        
        with grid_cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{c_name}** ({len(c_students)} Students)")
                st.caption(f"3rd Year: **{c_y3}** | 4th Year: **{c_y4}** | TPO Email: `{c_email}`")
                
                b1, b2, b3 = st.columns(3)
                c_pdf = generate_college_pdf(c_name, c_students)
                b1.download_button("📄 PDF Summary", data=c_pdf, file_name=f"{c_name}_Report.pdf", mime="application/pdf", key=f"cpdf_{idx}", use_container_width=True)
                
                c_xls = generate_college_excel(c_students)
                b2.download_button("📊 Excel Sheet", data=c_xls, file_name=f"{c_name}_Records.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"cxls_{idx}", use_container_width=True)
                
                if b3.button("✉️ Send TPO", key=f"cmail_{idx}", use_container_width=True):
                    with st.spinner("Dispatching..."):
                        try:
                            execute_smtp_send(
                                c_email,
                                f"Consolidated Report - {c_name}",
                                f"Respected TPO,\n\nPlease find attached the monthly consolidated student report.",
                                [
                                    (f"{c_name}_Report.pdf", generate_college_pdf(c_name, c_students)),
                                    (f"{c_name}_Records.xlsx", generate_college_excel(c_students))
                                ],
                                sender_email, app_password, is_simulated=demo_mode
                            )
                            st.success(f"Delivered to {c_email}!")
                        except Exception as e:
                            st.error(f"Error: {e}")

st.divider()

# ----------------- SECTION 2: INDIVIDUAL STUDENTS TABLE & WHATSAPP -----------------
st.subheader("👨‍🎓 Student Evaluation Matrix")

for idx, s in enumerate(filtered_students):
    with st.container(border=True):
        row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([2.5, 2.2, 2.5, 1.3, 2.5])
        
        with row_c1:
            st.markdown(f"**{s['StudentName']}** (`{s['RollNo']}`)")
            st.caption(f"📱 {s['ParentMobile']} | ✉️ {s['ParentEmail']}")
            
        with row_c2:
            st.markdown(f"**{s['CollegeName']}**")
            st.caption(f"Batch: {s['Batch']} | Year: {s['Year']}")
            
        with row_c3:
            st.markdown(f"Attendance: **{s['AttendedClasses']}/{s['TotalClasses']} ({s['AttendancePct']}%)**")
            st.caption(f"Tech: {s['TechnicalPct']}% | Soft Skills: {s['SoftSkillsPct']}%")
            
        with row_c4:
            st.markdown(f"**{s['OverallScore']}%**")
            st.caption("Overall Score")
            
        with row_c5:
            clean_phone = re.sub(r'[^0-9]', '', str(s['ParentMobile']))
            if len(clean_phone) == 10:
                clean_phone = "91" + clean_phone
                
            wa_text = f"*INFOBEANS FOUNDATION - Progress Report*\n\nDear Parent,\nProgress Report for *{s['StudentName']}* ({s['RollNo']}), *{s['CollegeName']}* for {report_month}:\n- Batch: {s['Batch']} ({s['Year']})\n- Attendance: {s['AttendedClasses']}/{s['TotalClasses']} ({s['AttendancePct']}%)\n- Technical: {s['TechnicalPct']}%\n- Soft Skills: {s['SoftSkillsPct']}%\n- Overall: {s['OverallScore']}%\n\nWarm regards,\n*InfoBeans Foundation Team*"
            wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(wa_text)}"
            
            st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25D366; color:white; font-weight:bold; font-size:12px; padding:6px; border-radius:6px; text-decoration:none; margin-bottom:6px;">💬 WhatsApp Message</a>', unsafe_allow_html=True)
            
            wb_col1, wb_col2 = st.columns(2)
            pdf_data = generate_student_pdf(s, report_month)
            wb_col1.download_button("📄 PDF", data=pdf_data, file_name=f"{s['RollNo']}_Report.pdf", mime="application/pdf", key=f"spdf_{idx}", use_container_width=True)
            
            if wb_col2.button("✉️ Email", key=f"smail_{idx}", use_container_width=True):
                with st.spinner("Sending..."):
                    try:
                        execute_smtp_send(
                            s['ParentEmail'],
                            f"Student Progress Report - {s['StudentName']}",
                            f"Dear Parent,\n\nPlease find attached the report for {s['StudentName']}.",
                            [(f"{s['RollNo']}_Report.pdf", generate_student_pdf(s, report_month))],
                            sender_email, app_password, is_simulated=demo_mode
                        )
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Error: {e}")
