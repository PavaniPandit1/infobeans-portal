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
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="InfoBeans Foundation Portal",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# BRAND COLORS
# ============================================================

BRAND_RED = colors.HexColor("#EA1B3D")
BRAND_SLATE = colors.HexColor("#1E293B")
BRAND_LIGHT = colors.HexColor("#F8FAFC")
BRAND_BORDER = colors.HexColor("#E2E8F0")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_email(email):
    """Clean and normalize email address."""
    return str(email).strip().lower()


def is_valid_email(email):
    """Basic email validation."""
    email = clean_email(email)

    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def clean_app_password(password):
    """
    Google App Passwords are displayed with spaces.
    Remove spaces/special characters so SMTP receives
    the actual 16-character password.
    """
    return re.sub(r"[^a-zA-Z0-9]", "", str(password)).strip()


# ============================================================
# PDF GENERATOR - INDIVIDUAL STUDENT
# ============================================================

def generate_student_pdf(student, report_month):

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

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=BRAND_RED,
        leading=22
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=BRAND_SLATE,
        leading=14
    )

    cell_b = ParagraphStyle(
        "CB",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=BRAND_SLATE
    )

    cell_r = ParagraphStyle(
        "CR",
        fontName="Helvetica",
        fontSize=9,
        textColor=BRAND_SLATE
    )

    elements = []

    # Header
    header_table = Table(
        [
            [
                Paragraph(
                    "<b>INFOBEANS FOUNDATION</b>",
                    title_style
                ),
                Paragraph(
                    f"<b>Session:</b> 2026<br/>"
                    f"<b>Month:</b> {report_month}",
                    subtitle_style
                )
            ]
        ],
        colWidths=[340, 200]
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
        ])
    )

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    attendance_str = (
        f"{student.get('AttendedClasses', 0)} / "
        f"{student.get('TotalClasses', 0)} "
        f"({student.get('AttendancePct', 0)}%)"
    )

    # Student information
    meta_data = [
        [
            Paragraph("<b>Student Name:</b>", cell_b),
            Paragraph(
                str(student.get("StudentName", "N/A")),
                cell_r
            ),
            Paragraph("<b>Batch:</b>", cell_b),
            Paragraph(
                str(student.get("Batch", "N/A")),
                cell_r
            )
        ],

        [
            Paragraph("<b>Roll Number:</b>", cell_b),
            Paragraph(
                str(student.get("RollNo", "N/A")),
                cell_r
            ),
            Paragraph("<b>Academic Year:</b>", cell_b),
            Paragraph(
                str(student.get("Year", "N/A")),
                cell_r
            )
        ],

        [
            Paragraph("<b>College Name:</b>", cell_b),
            Paragraph(
                str(student.get("CollegeName", "N/A")),
                cell_r
            ),
            Paragraph("<b>Overall Score:</b>", cell_b),
            Paragraph(
                f"<b>{student.get('OverallScore', 0)}%</b>",
                cell_b
            )
        ],

        [
            Paragraph("<b>Attendance:</b>", cell_b),
            Paragraph(
                f"<b>{attendance_str}</b>",
                cell_b
            ),
            Paragraph("<b>Parent Mobile:</b>", cell_b),
            Paragraph(
                str(student.get("ParentMobile", "N/A")),
                cell_r
            )
        ]
    ]

    meta_table = Table(
        meta_data,
        colWidths=[95, 175, 95, 175]
    )

    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, BRAND_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Score table
    score_rows = [
        [
            Paragraph("<b>Module</b>", cell_b),
            Paragraph("<b>Max Marks</b>", cell_b),
            Paragraph("<b>Scored</b>", cell_b),
            Paragraph("<b>Percentage</b>", cell_b)
        ],

        [
            Paragraph("Technical Assessment", cell_r),
            Paragraph("100", cell_r),
            Paragraph(
                str(student.get("TechnicalMarks", 0)),
                cell_r
            ),
            Paragraph(
                f"{student.get('TechnicalPct', 0)}%",
                cell_b
            )
        ],

        [
            Paragraph("Soft Skills Assessment", cell_r),
            Paragraph("100", cell_r),
            Paragraph(
                str(student.get("SoftSkillsMarks", 0)),
                cell_r
            ),
            Paragraph(
                f"{student.get('SoftSkillsPct', 0)}%",
                cell_b
            )
        ]
    ]

    score_table = Table(
        score_rows,
        colWidths=[200, 110, 110, 120]
    )

    score_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_SLATE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    elements.append(score_table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<i>This is an official computer-generated "
            "evaluation report by InfoBeans Foundation.</i>",
            subtitle_style
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer


# ============================================================
# PDF GENERATOR - COLLEGE
# ============================================================

def generate_college_pdf(college_name, students):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=BRAND_RED
    )

    sub_style = ParagraphStyle(
        "CSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=BRAND_SLATE
    )

    th_style = ParagraphStyle(
        "TH",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.white
    )

    tb_style = ParagraphStyle(
        "TB",
        fontName="Helvetica",
        fontSize=8,
        textColor=BRAND_SLATE
    )

    elements = []

    total = len(students)

    third_yr = len([
        s for s in students
        if "3" in str(s.get("Year", ""))
    ])

    fourth_yr = len([
        s for s in students
        if "4" in str(s.get("Year", ""))
    ])

    avg_att = round(
        sum(s.get("AttendancePct", 0) for s in students)
        / (total or 1),
        1
    )

    avg_tech = round(
        sum(s.get("TechnicalPct", 0) for s in students)
        / (total or 1),
        1
    )

    avg_soft = round(
        sum(s.get("SoftSkillsPct", 0) for s in students)
        / (total or 1),
        1
    )

    elements.append(
        Paragraph(
            "<b>INFOBEANS FOUNDATION - "
            "CONSOLIDATED INSTITUTION REPORT</b>",
            title_style
        )
    )

    elements.append(
        Paragraph(
            f"<b>Institution:</b> {college_name} | "
            f"<b>Total Enrolled:</b> {total} "
            f"(3rd Year: {third_yr}, 4th Year: {fourth_yr}) | "
            f"<b>Avg Attendance:</b> {avg_att}% | "
            f"<b>Avg Tech:</b> {avg_tech}% | "
            f"<b>Avg Soft Skills:</b> {avg_soft}%",
            sub_style
        )
    )

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
            Paragraph(
                str(s.get("RollNo", "")),
                tb_style
            ),

            Paragraph(
                str(s.get("StudentName", "")),
                tb_style
            ),

            Paragraph(
                str(s.get("Batch", "")),
                tb_style
            ),

            Paragraph(
                str(s.get("Year", "")),
                tb_style
            ),

            Paragraph(
                f"{s.get('AttendedClasses', 0)}/"
                f"{s.get('TotalClasses', 0)} "
                f"({s.get('AttendancePct', 0)}%)",
                tb_style
            ),

            Paragraph(
                f"{s.get('TechnicalMarks', 0)} "
                f"({s.get('TechnicalPct', 0)}%)",
                tb_style
            ),

            Paragraph(
                f"{s.get('SoftSkillsMarks', 0)} "
                f"({s.get('SoftSkillsPct', 0)}%)",
                tb_style
            ),

            Paragraph(
                f"{s.get('OverallScore', 0)}%",
                tb_style
            )
        ])

    col_table = Table(
        table_data,
        colWidths=[
            70,
            160,
            65,
            55,
            120,
            90,
            100,
            70
        ]
    )

    col_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_SLATE),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, BRAND_LIGHT]
            ),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
        ])
    )

    elements.append(col_table)

    doc.build(elements)

    buffer.seek(0)

    return buffer


# ============================================================
# EXCEL GENERATOR
# ============================================================

def generate_college_excel(students):

    df = pd.DataFrame(students)

    cols = [
        "RollNo",
        "StudentName",
        "CollegeName",
        "Year",
        "Batch",
        "AttendedClasses",
        "TotalClasses",
        "AttendancePct",
        "TechnicalMarks",
        "TechnicalPct",
        "SoftSkillsMarks",
        "SoftSkillsPct",
        "OverallScore",
        "ParentMobile",
        "ParentEmail",
        "CollegeEmail"
    ]

    available_cols = [
        c for c in cols
        if c in df.columns
    ]

    export_df = df[available_cols]

    buffer = io.BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Student Records"
        )

    buffer.seek(0)

    return buffer


# ============================================================
# SMTP EMAIL FUNCTION
# ============================================================

def execute_smtp_send(
    to_email,
    subject,
    body_text,
    attachments,
    sender_email,
    app_pwd
):

    clean_sender = clean_email(sender_email)
    clean_to = clean_email(to_email)
    clean_pwd = clean_app_password(app_pwd)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not clean_sender:
        raise ValueError(
            "Sender Gmail address is required."
        )

    if not is_valid_email(clean_sender):
        raise ValueError(
            f"Invalid Sender Gmail address: {clean_sender}"
        )

    if not clean_to:
        raise ValueError(
            "Recipient email address is missing."
        )

    if not is_valid_email(clean_to):
        raise ValueError(
            f"Invalid recipient email address: {clean_to}"
        )

    if not clean_pwd:
        raise ValueError(
            "Gmail App Password is required."
        )

    if len(clean_pwd) != 16:
        raise ValueError(
            "Google App Password should contain 16 characters."
        )

    # --------------------------------------------------------
    # CREATE EMAIL
    # --------------------------------------------------------

    msg = MIMEMultipart()

    msg["From"] = (
        f"InfoBeans Foundation <{clean_sender}>"
    )

    msg["To"] = clean_to
    msg["Subject"] = subject

    msg.attach(
        MIMEText(
            body_text,
            "plain",
            "utf-8"
        )
    )

    # --------------------------------------------------------
    # ATTACH FILES
    # --------------------------------------------------------

    for filename, file_buffer in attachments:

        # Make sure buffer starts from beginning
        file_buffer.seek(0)

        part = MIMEBase(
            "application",
            "octet-stream"
        )

        part.set_payload(
            file_buffer.read()
        )

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"'
        )

        msg.attach(part)

    # --------------------------------------------------------
    # GMAIL SMTP
    # --------------------------------------------------------

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                clean_sender,
                clean_pwd
            )

            server.send_message(msg)

        return True

    except smtplib.SMTPAuthenticationError as e:

        raise ValueError(
            "Gmail authentication failed (535 BadCredentials). "
            "Make sure:\n"
            "1. Sender Gmail is correct.\n"
            "2. 2-Step Verification is ON.\n"
            "3. App Password belongs to the SAME Gmail account.\n"
            "4. You entered the 16-character App Password, "
            "NOT your normal Gmail password."
        ) from e

    except smtplib.SMTPRecipientsRefused as e:

        raise ValueError(
            f"Gmail rejected the recipient address: {clean_to}"
        ) from e

    except smtplib.SMTPException as e:

        raise ValueError(
            f"Gmail SMTP error: {e}"
        ) from e

    except Exception as e:

        raise ValueError(
            f"Email sending failed: {e}"
        ) from e


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div style="background-color:#EA1B3D; padding:12px; '
        'border-radius:8px; text-align:center; margin-bottom:12px;">'
        '<span style="color:white; font-size:18px; font-weight:900; '
        'letter-spacing:1px;">InfoBeans</span>'
        '<span style="color:white; font-size:13px; font-weight:400; '
        'display:block;">FOUNDATION</span>'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload Multi-Batch Excel File",
        type=["xlsx", "xls"]
    )

    st.divider()

    st.markdown("### ⚙️ Dispatch Settings")

    report_month = st.text_input(
        "Evaluation Month",
        value="September 2026"
    )

    sender_email = st.text_input(
        "Sender Gmail",
        placeholder="example@gmail.com"
    )

    app_password = st.text_input(
        "Gmail App Password",
        type="password",
        placeholder="16-character App Password"
    )

    st.caption(
        "Use a Google App Password, not your normal Gmail password."
    )

    # --------------------------------------------------------
    # TEST SMTP CONNECTION
    # --------------------------------------------------------

    if st.button(
        "🔌 Test Gmail Connection",
        use_container_width=True
    ):

        if not sender_email:
            st.error(
                "Enter Sender Gmail first."
            )

        elif not app_password:
            st.error(
                "Enter Gmail App Password first."
            )

        else:

            try:

                clean_sender = clean_email(
                    sender_email
                )

                clean_pwd = clean_app_password(
                    app_password
                )

                if not is_valid_email(clean_sender):
                    raise ValueError(
                        "Invalid Gmail address."
                    )

                if len(clean_pwd) != 16:
                    raise ValueError(
                        "App Password must contain 16 characters."
                    )

                with st.spinner(
                    "Testing Gmail connection..."
                ):

                    with smtplib.SMTP(
                        "smtp.gmail.com",
                        587,
                        timeout=20
                    ) as server:

                        server.ehlo()
                        server.starttls()
                        server.ehlo()

                        server.login(
                            clean_sender,
                            clean_pwd
                        )

                st.success(
                    "✅ Gmail connection successful!"
                )

            except smtplib.SMTPAuthenticationError:

                st.error(
                    "❌ Authentication failed. "
                    "Check your Gmail and App Password."
                )

            except Exception as e:

                st.error(
                    f"❌ Connection failed: {e}"
                )


# ============================================================
# MAIN TITLE
# ============================================================

st.markdown(
    '<div style="border-left:5px solid #EA1B3D; padding-left:15px; '
    'margin-bottom:20px;">'
    '<h1 style="margin:0; font-size:26px; font-weight:800; '
    'color:#EA1B3D;">InfoBeans Foundation</h1>'
    '<p style="margin:2px 0 0 0; font-size:14px; opacity:0.8;">'
    'Student Progress & Multi-College Reporting Portal</p>'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# REQUIRE EXCEL FILE
# ============================================================

if uploaded_file is None:

    st.info(
        "👆 Please upload your Excel file from the sidebar to activate."
    )

    st.stop()


# ============================================================
# DATA PROCESSING
# ============================================================

try:

    xls = pd.ExcelFile(uploaded_file)

    students = []

    for sheet in xls.sheet_names:

        df = pd.read_excel(
            xls,
            sheet_name=sheet
        ).fillna("")

        for idx, row in df.iterrows():

            row_dict = {
                str(k).strip(): v
                for k, v in row.to_dict().items()
            }

            name = str(
                row_dict.get("Student Name")
                or row_dict.get("Name")
                or f"Student {idx + 1}"
            )

            email = str(
                row_dict.get("Parent Email")
                or row_dict.get("Email")
                or ""
            ).strip()

            mobile = str(
                row_dict.get("Parent Mobile")
                or row_dict.get("Mobile")
                or row_dict.get("Phone")
                or ""
            ).strip()

            college = str(
                row_dict.get("College Name")
                or row_dict.get("College")
                or "Unassigned College"
            )

            college_email = str(
                row_dict.get("College Email")
                or row_dict.get("TPO Email")
                or ""
            ).strip()

            roll = str(
                row_dict.get("Roll No")
                or row_dict.get("Roll")
                or f"IB-{1000 + idx}"
            )

            year_raw = str(
                row_dict.get("Year")
                or row_dict.get("Academic Year")
                or "3rd Year"
            )

            year = (
                "3rd Year"
                if "3" in year_raw
                else (
                    "4th Year"
                    if "4" in year_raw
                    else year_raw
                )
            )

            # Attendance
            total_classes = float(
                str(
                    row_dict.get(
                        "Total Classes",
                        0
                    )
                ).replace("%", "")
                or 0
            )

            attended_classes = float(
                str(
                    row_dict.get(
                        "Attended Classes",
                        0
                    )
                ).replace("%", "")
                or 0
            )

            if total_classes > 0:

                att_pct = round(
                    (
                        attended_classes
                        / total_classes
                    ) * 100,
                    1
                )

            else:

                att_pct = float(
                    str(
                        row_dict.get(
                            "Attendance %",
                            0
                        )
                    ).replace("%", "")
                    or 0
                )

            # Technical
            tech_marks = float(
                str(
                    row_dict.get(
                        "Technical Marks (100)",
                        0
                    )
                ).replace("%", "")
                or 0
            )

            tech_pct = float(
                str(
                    row_dict.get(
                        "Technical %",
                        tech_marks
                    )
                ).replace("%", "")
                or tech_marks
            )

            # Soft skills
            soft_marks = float(
                str(
                    row_dict.get(
                        "Soft Skills Marks (100)",
                        0
                    )
                ).replace("%", "")
                or 0
            )

            soft_pct = float(
                str(
                    row_dict.get(
                        "Soft Skills %",
                        soft_marks
                    )
                ).replace("%", "")
                or soft_marks
            )

            # Overall
            default_overall = round(
                (tech_marks * 0.6)
                + (soft_marks * 0.4),
                1
            )

            overall_score = float(
                str(
                    row_dict.get(
                        "Overall Score %",
                        default_overall
                    )
                ).replace("%", "")
                or 0
            )

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

                "TotalClasses": int(
                    total_classes
                ),

                "AttendedClasses": int(
                    attended_classes
                ),

                "AttendancePct": att_pct,

                "TechnicalMarks": tech_marks,

                "TechnicalPct": tech_pct,

                "SoftSkillsMarks": soft_marks,

                "SoftSkillsPct": soft_pct,

                "OverallScore": overall_score
            })


except Exception as e:

    st.error(
        f"Error reading file: {e}"
    )

    st.stop()


# ============================================================
# FILTERS
# ============================================================

with st.container():

    col_f1, col_f2, col_f3 = st.columns(
        [1.2, 1.2, 2.6]
    )

    with col_f1:

        batch_list = [
            "ALL"
        ] + sorted(
            list(
                set(
                    s["Batch"]
                    for s in students
                )
            )
        )

        selected_batch = st.selectbox(
            "Batch Filter",
            batch_list
        )

    with col_f2:

        selected_year = st.selectbox(
            "Academic Year",
            [
                "ALL",
                "3rd Year",
                "4th Year"
            ]
        )

    filtered_temp = [
        s for s in students
        if (
            selected_batch == "ALL"
            or s["Batch"] == selected_batch
        )
        and (
            selected_year == "ALL"
            or s["Year"] == selected_year
        )
    ]

    all_colleges = sorted(
        list(
            set(
                s["CollegeName"]
                for s in filtered_temp
            )
        )
    )

    with col_f3:

        selected_colleges = st.multiselect(
            "Colleges Filter",
            all_colleges,
            default=all_colleges
        )


filtered_students = [
    s for s in filtered_temp
    if s["CollegeName"] in selected_colleges
]


# ============================================================
# METRIC CARDS
# ============================================================

m1, m2, m3, m4, m5 = st.columns(5)

total_count = len(filtered_students)

y3_count = len([
    s for s in filtered_students
    if "3" in s["Year"]
])

y4_count = len([
    s for s in filtered_students
    if "4" in s["Year"]
])

avg_att = round(
    sum(
        s["AttendancePct"]
        for s in filtered_students
    )
    / (total_count or 1),
    1
)

avg_tech = round(
    sum(
        s["TechnicalPct"]
        for s in filtered_students
    )
    / (total_count or 1),
    1
)

avg_soft = round(
    sum(
        s["SoftSkillsPct"]
        for s in filtered_students
    )
    / (total_count or 1),
    1
)

m1.metric(
    "Total Students",
    total_count
)

m2.metric(
    "3rd / 4th Year",
    f"{y3_count} / {y4_count}"
)

m3.metric(
    "Avg Attendance",
    f"{avg_att}%"
)

m4.metric(
    "Avg Tech Score",
    f"{avg_tech}%"
)

m5.metric(
    "Avg Soft Skills",
    f"{avg_soft}%"
)


st.divider()


# ============================================================
# BULK DISPATCH
# ============================================================

st.subheader(
    "⚡ Bulk Dispatch Operations"
)

act_c1, act_c2 = st.columns(2)


# ============================================================
# SEND TO PARENTS
# ============================================================

with act_c1:

    if st.button(
        "📧 Send Individual Email to All Filtered Parents",
        use_container_width=True,
        type="primary"
    ):

        if not sender_email:

            st.error(
                "Please enter Sender Gmail."
            )

        elif not app_password:

            st.error(
                "Please enter Gmail App Password."
            )

        elif total_count == 0:

            st.warning(
                "No students available for selected filters."
            )

        else:

            progress_bar = st.progress(0)

            status_text = st.empty()

            success_count = 0

            failed_students = []

            for i, st_data in enumerate(
                filtered_students
            ):

                target_email = clean_email(
                    st_data["ParentEmail"]
                )

                status_text.info(
                    f"Dispatching "
                    f"({i + 1}/{total_count}): "
                    f"{st_data['StudentName']} "
                    f"→ {target_email or 'NO EMAIL'}"
                )

                try:

                    # Do NOT send to sender as fallback
                    if not target_email:

                        raise ValueError(
                            "Parent email is missing."
                        )

                    if not is_valid_email(
                        target_email
                    ):

                        raise ValueError(
                            f"Invalid parent email: "
                            f"{target_email}"
                        )

                    pdf = generate_student_pdf(
                        st_data,
                        report_month
                    )

                    execute_smtp_send(

                        target_email,

                        f"Student Progress Report - "
                        f"{st_data['StudentName']}",

                        f"Dear Parent,\n\n"
                        f"Please find attached the "
                        f"monthly progress report for "
                        f"{st_data['StudentName']}.\n\n"
                        f"Warm regards,\n"
                        f"InfoBeans Foundation Team",

                        [
                            (
                                f"{st_data['RollNo']}_Report.pdf",
                                pdf
                            )
                        ],

                        sender_email,
                        app_password
                    )

                    success_count += 1

                except Exception as e:

                    failed_students.append(
                        (
                            st_data["StudentName"],
                            str(e)
                        )
                    )

                progress_bar.progress(
                    (i + 1) / total_count
                )

            # Results
            status_text.empty()

            if success_count == total_count:

                st.success(
                    f"✅ Successfully sent "
                    f"{success_count} parent reports!"
                )

            else:

                st.warning(
                    f"Completed: {success_count} successful, "
                    f"{len(failed_students)} failed."
                )

                if failed_students:

                    with st.expander(
                        "❌ View Failed Emails"
                    ):

                        for name, error in failed_students:

                            st.error(
                                f"**{name}:** {error}"
                            )


# ============================================================
# SEND TO COLLEGES
# ============================================================

with act_c2:

    if st.button(
        "🏛️ Send Consolidated PDF + Excel to All Colleges",
        use_container_width=True
    ):

        if not sender_email:

            st.error(
                "Please enter Sender Gmail."
            )

        elif not app_password:

            st.error(
                "Please enter Gmail App Password."
            )

        else:

            col_list = sorted(
                list(
                    set(
                        s["CollegeName"]
                        for s in filtered_students
                    )
                )
            )

            if not col_list:

                st.warning(
                    "No colleges found."
                )

            else:

                progress_bar = st.progress(0)

                status_text = st.empty()

                success_col_count = 0

                failed_colleges = []

                for i, col_name in enumerate(
                    col_list
                ):

                    c_students = [
                        s
                        for s in filtered_students
                        if s["CollegeName"] == col_name
                    ]

                    c_email = clean_email(
                        c_students[0].get(
                            "CollegeEmail",
                            ""
                        )
                    )

                    status_text.info(
                        f"Dispatching "
                        f"({i + 1}/{len(col_list)}): "
                        f"{col_name} → "
                        f"{c_email or 'NO EMAIL'}"
                    )

                    try:

                        if not c_email:

                            raise ValueError(
                                "College/TPO email is missing."
                            )

                        if not is_valid_email(
                            c_email
                        ):

                            raise ValueError(
                                f"Invalid college email: "
                                f"{c_email}"
                            )

                        pdf = generate_college_pdf(
                            col_name,
                            c_students
                        )

                        excel = generate_college_excel(
                            c_students
                        )

                        execute_smtp_send(

                            c_email,

                            f"Consolidated Report - "
                            f"{col_name}",

                            f"Respected TPO,\n\n"
                            f"Please find attached the "
                            f"monthly consolidated "
                            f"student report.\n\n"
                            f"Warm regards,\n"
                            f"InfoBeans Foundation Team",

                            [
                                (
                                    f"{col_name}_Report.pdf",
                                    pdf
                                ),

                                (
                                    f"{col_name}_Records.xlsx",
                                    excel
                                )
                            ],

                            sender_email,
                            app_password
                        )

                        success_col_count += 1

                    except Exception as e:

                        failed_colleges.append(
                            (
                                col_name,
                                str(e)
                            )
                        )

                    progress_bar.progress(
                        (i + 1) / len(col_list)
                    )

                status_text.empty()

                if success_col_count == len(col_list):

                    st.success(
                        f"✅ Successfully sent "
                        f"reports to all "
                        f"{success_col_count} institutions!"
                    )

                else:

                    st.warning(
                        f"Completed: "
                        f"{success_col_count} successful, "
                        f"{len(failed_colleges)} failed."
                    )

                    if failed_colleges:

                        with st.expander(
                            "❌ View Failed Colleges"
                        ):

                            for name, error in failed_colleges:

                                st.error(
                                    f"**{name}:** {error}"
                                )


st.divider()


# ============================================================
# COLLEGE REPORT CARDS
# ============================================================

st.subheader(
    "🏛️ Institution / TPO Reports"
)

col_cards = sorted(
    list(
        set(
            s["CollegeName"]
            for s in filtered_students
        )
    )
)

if not col_cards:

    st.info(
        "No colleges matching filter."
    )

else:

    grid_cols = st.columns(2)

    for idx, c_name in enumerate(
        col_cards
    ):

        c_students = [
            s
            for s in filtered_students
            if s["CollegeName"] == c_name
        ]

        c_y3 = len([
            s for s in c_students
            if "3" in s["Year"]
        ])

        c_y4 = len([
            s for s in c_students
            if "4" in s["Year"]
        ])

        c_email = clean_email(
            c_students[0].get(
                "CollegeEmail",
                ""
            )
        )

        with grid_cols[idx % 2]:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"**{c_name}** "
                    f"({len(c_students)} Students)"
                )

                st.caption(
                    f"3rd Year: **{c_y3}** | "
                    f"4th Year: **{c_y4}** | "
                    f"Target Email: "
                    f"`{c_email or 'Not provided'}`"
                )

                b1, b2, b3 = st.columns(3)

                # PDF
                c_pdf = generate_college_pdf(
                    c_name,
                    c_students
                )

                b1.download_button(
                    "📄 PDF Summary",
                    data=c_pdf,
                    file_name=f"{c_name}_Report.pdf",
                    mime="application/pdf",
                    key=f"cpdf_{idx}",
                    use_container_width=True
                )

                # Excel
                c_xls = generate_college_excel(
                    c_students
                )

                b2.download_button(
                    "📊 Excel Sheet",
                    data=c_xls,
                    file_name=f"{c_name}_Records.xlsx",
                    mime=(
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    key=f"cxls_{idx}",
                    use_container_width=True
                )

                # Send TPO
                if b3.button(
                    "✉️ Send TPO",
                    key=f"cmail_{idx}",
                    use_container_width=True
                ):

                    if not sender_email:

                        st.error(
                            "Enter Sender Gmail first."
                        )

                    elif not app_password:

                        st.error(
                            "Enter Gmail App Password first."
                        )

                    elif not c_email:

                        st.error(
                            f"No TPO email found "
                            f"for {c_name}."
                        )

                    elif not is_valid_email(
                        c_email
                    ):

                        st.error(
                            f"Invalid TPO email: "
                            f"{c_email}"
                        )

                    else:

                        with st.spinner(
                            "Dispatching..."
                        ):

                            try:

                                execute_smtp_send(

                                    c_email,

                                    f"Consolidated Report - "
                                    f"{c_name}",

                                    f"Respected TPO,\n\n"
                                    f"Please find attached "
                                    f"the monthly consolidated "
                                    f"student report.\n\n"
                                    f"Warm regards,\n"
                                    f"InfoBeans Foundation Team",

                                    [
                                        (
                                            f"{c_name}_Report.pdf",
                                            generate_college_pdf(
                                                c_name,
                                                c_students
                                            )
                                        ),

                                        (
                                            f"{c_name}_Records.xlsx",
                                            generate_college_excel(
                                                c_students
                                            )
                                        )
                                    ],

                                    sender_email,
                                    app_password
                                )

                                st.success(
                                    f"✅ Delivered to "
                                    f"{c_email}!"
                                )

                            except Exception as e:

                                st.error(
                                    f"❌ Error: {e}"
                                )


st.divider()


# ============================================================
# STUDENT EVALUATION MATRIX
# ============================================================

st.subheader(
    "👨‍🎓 Student Evaluation Matrix"
)

for idx, s in enumerate(
    filtered_students
):

    with st.container(
        border=True
    ):

        row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns(
            [2.5, 2.2, 2.5, 1.3, 2.5]
        )

        # ----------------------------------------------------
        # Student
        # ----------------------------------------------------

        with row_c1:

            st.markdown(
                f"**{s['StudentName']}** "
                f"(`{s['RollNo']}`)"
            )

            st.caption(
                f"📱 {s['ParentMobile']} | "
                f"✉️ {s['ParentEmail'] or 'No email'}"
            )

        # ----------------------------------------------------
        # College
        # ----------------------------------------------------

        with row_c2:

            st.markdown(
                f"**{s['CollegeName']}**"
            )

            st.caption(
                f"Batch: {s['Batch']} | "
                f"Year: {s['Year']}"
            )

        # ----------------------------------------------------
        # Performance
        # ----------------------------------------------------

        with row_c3:

            st.markdown(
                f"Attendance: "
                f"**{s['AttendedClasses']}/"
                f"{s['TotalClasses']} "
                f"({s['AttendancePct']}%)**"
            )

            st.caption(
                f"Tech: {s['TechnicalPct']}% | "
                f"Soft Skills: "
                f"{s['SoftSkillsPct']}%"
            )

        # ----------------------------------------------------
        # Overall
        # ----------------------------------------------------

        with row_c4:

            st.markdown(
                f"**{s['OverallScore']}%**"
            )

            st.caption(
                "Overall Score"
            )

        # ----------------------------------------------------
        # Actions
        # ----------------------------------------------------

        with row_c5:

            clean_phone = re.sub(
                r"[^0-9]",
                "",
                str(s["ParentMobile"])
            )

            if len(clean_phone) == 10:

                clean_phone = (
                    "91" + clean_phone
                )

            wa_text = (
                "*INFOBEANS FOUNDATION - "
                "Progress Report*\n\n"
                "Dear Parent,\n"
                f"Progress Report for "
                f"*{s['StudentName']}* "
                f"({s['RollNo']}), "
                f"*{s['CollegeName']}* "
                f"for {report_month}:\n"
                f"- Batch: {s['Batch']} "
                f"({s['Year']})\n"
                f"- Attendance: "
                f"{s['AttendedClasses']}/"
                f"{s['TotalClasses']} "
                f"({s['AttendancePct']}%)\n"
                f"- Technical: "
                f"{s['TechnicalPct']}%\n"
                f"- Soft Skills: "
                f"{s['SoftSkillsPct']}%\n"
                f"- Overall: "
                f"{s['OverallScore']}%\n\n"
                "Warm regards,\n"
                "*InfoBeans Foundation Team*"
            )

            wa_url = (
                f"https://wa.me/{clean_phone}"
                f"?text="
                f"{urllib.parse.quote(wa_text)}"
            )

            if len(clean_phone) >= 12:

                st.markdown(
                    f'<a href="{wa_url}" target="_blank" '
                    f'style="display:block; text-align:center; '
                    f'background-color:#25D366; color:white; '
                    f'font-weight:bold; font-size:12px; padding:6px; '
                    f'border-radius:6px; text-decoration:none; '
                    f'margin-bottom:6px;">💬 WhatsApp Message</a>',
                    unsafe_allow_html=True
                )

            else:

                st.caption(
                    "⚠️ Invalid parent mobile"
                )

            wb_col1, wb_col2 = st.columns(2)

            # PDF
            pdf_data = generate_student_pdf(
                s,
                report_month
            )

            wb_col1.download_button(
                "📄 PDF",
                data=pdf_data,
                file_name=f"{s['RollNo']}_Report.pdf",
                mime="application/pdf",
                key=f"spdf_{idx}",
                use_container_width=True
            )

            # Email
            target_parent_email = clean_email(
                s["ParentEmail"]
            )

            if wb_col2.button(
                "✉️ Email",
                key=f"smail_{idx}",
                use_container_width=True
            ):

                if not sender_email:

                    st.error(
                        "Enter Sender Gmail first."
                    )

                elif not app_password:

                    st.error(
                        "Enter Gmail App Password first."
                    )

                elif not target_parent_email:

                    st.error(
                        f"No parent email found "
                        f"for {s['StudentName']}."
                    )

                elif not is_valid_email(
                    target_parent_email
                ):

                    st.error(
                        f"Invalid parent email: "
                        f"{target_parent_email}"
                    )

                else:

                    with st.spinner(
                        "Sending..."
                    ):

                        try:

                            execute_smtp_send(

                                target_parent_email,

                                f"Student Progress Report - "
                                f"{s['StudentName']}",

                                f"Dear Parent,\n\n"
                                f"Please find attached the "
                                f"monthly progress report "
                                f"for {s['StudentName']}.\n\n"
                                f"Warm regards,\n"
                                f"InfoBeans Foundation Team",

                                [
                                    (
                                        f"{s['RollNo']}_Report.pdf",
                                        generate_student_pdf(
                                            s,
                                            report_month
                                        )
                                    )
                                ],

                                sender_email,
                                app_password
                            )

                            st.success(
                                f"✅ Sent to "
                                f"{target_parent_email}!"
                            )

                        except Exception as e:

                            st.error(
                                f"❌ Error: {e}"
                            )
