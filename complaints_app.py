import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ✅ تحميل بيانات Google Cloud من secrets.toml
google_creds = st.secrets["google"]
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(google_creds, scopes=scopes)
client = gspread.authorize(creds)

# ✅ معرف Google Sheets الخاص بك
SPREADSHEET_ID = "1adEmI-XDrD0xKedCd8082tK09Vjr_pKa8viTbWFJBG4"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ✅ أسماء الأعمدة المطلوبة في Google Sheets
HEADERS = ["Date Submitted", "Complaint ID", "Product Name", "Severity", "Contact Number", "Details", "Submitted By"]

# ✅ التحقق من وجود العناوين في Google Sheets
def ensure_headers():
    existing_data = sheet.get_all_values()
    if not existing_data or existing_data[0] != HEADERS:  # إذا لم تكن العناوين موجودة أو غير صحيحة
        sheet.insert_row(HEADERS, 1)  # إضافة العناوين في الصف الأول

# ✅ استدعاء الدالة لضمان وجود العناوين
ensure_headers()

# ✅ توليد رقم الشكوى تلقائيًا بصيغة CcMMYYNN
def generate_complaint_id():
    today = datetime.now()
    month = today.strftime("%m")  # MM
    year = today.strftime("%y")   # YY
    prefix = f"Cc{month}{year}"   # Format: CcMMYY

    # ✅ جلب جميع القيم من Google Sheets
    complaints = sheet.get_all_records()

    # ✅ استخراج الأرقام التسلسلية السابقة من عمود "Complaint ID"
    serial_numbers = []
    for row in complaints:
        if "Complaint ID" in row and row["Complaint ID"].startswith(prefix):
            serial_part = row["Complaint ID"][-2:]  # آخر رقمين من الشكوى
            if serial_part.isdigit():
                serial_numbers.append(int(serial_part))

    # ✅ تحديد الرقم التسلسلي الجديد
    next_serial = max(serial_numbers, default=0) + 1  # زيادة الرقم التسلسلي
    return f"{prefix}{next_serial:02d}"  # الصيغة: CcMMYYNN

# ✅ واجهة Streamlit
st.title("📋 نظام إدارة الشكاوى")

st.header("📝 إرسال شكوى جديدة")

# ✅ توليد رقم الشكوى تلقائيًا
complaint_id = generate_complaint_id()
st.text_input("رقم الشكوى (تلقائي)", complaint_id, disabled=True)

# ✅ إدخال اسم المنتج، مستوى الخطورة، رقم التواصل، التفاصيل
product = st.text_input("اسم المنتج")
severity = st.selectbox("مستوى الخطورة", ["High", "Medium", "Low"])
contact_number = st.text_input("📞 رقم التواصل")  # ✅ إضافة رقم الهاتف
details = st.text_area("تفاصيل الشكوى")

# ✅ حقل "اسم كاتب الشكوى" (اختياري)
submitted_by = st.text_input("✍ اسم كاتب الشكوى (اختياري)")

# ✅ حفظ تاريخ الإرسال تلقائيًا
date_submitted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if st.button("إرسال الشكوى"):
    if product and details and contact_number:
        # ✅ تجهيز البيانات، إذا لم يُدخل المستخدم اسم كاتب الشكوى، سيتم وضع قيمة فارغة ("")
        new_data = [date_submitted, complaint_id, product, severity, contact_number, details, submitted_by or ""]  
        sheet.append_row(new_data)
        st.success(f"✅ تم إرسال الشكوى بنجاح برقم {complaint_id} في {date_submitted}!")
    else:
        st.error("❌ يرجى ملء جميع الحقول الإجبارية!")

# ✅ حماية الشكاوى بكلمة مرور
st.header("🔒 عرض الشكاوى (للمسؤول فقط)")
admin_password = st.text_input("أدخل كلمة المرور لعرض الشكاوى:", type="password")

# ✅ كلمة المرور الصحيحة التي يجب إدخالها (استبدلها بكلمة سر حقيقية)
CORRECT_PASSWORD = "admin123"

if st.button("تحميل الشكاوى"):
    if admin_password == CORRECT_PASSWORD:
        data = sheet.get_all_values()

        if len(data) > 1:  # إذا كان هناك بيانات غير العنوان
            df = pd.DataFrame(data[1:], columns=data[0])  # تحديد العناوين يدويًا
            st.write(df)
        else:
            st.warning("⚠ لا يوجد شكاوى حتى الآن.")
    else:
        st.error("❌ كلمة المرور غير صحيحة! لا يمكنك عرض الشكاوى.")
