import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from fpdf import FPDF

# ----------------------------
# โหลดข้อมูลลูกหนี้จากไฟล์ Excel
# ----------------------------
customers_df = pd.read_excel("customers.xlsx")
customer_amounts = dict(zip(customers_df["NAME"], customers_df["AmountDue"]))

st.title("📄 ระบบจัดการข้อมูลลูกหนี้ (4 ปี)")

# ----------------------------
# แบบฟอร์มกรอกข้อมูล
# ----------------------------
st.header("[1] กรอกข้อมูลการชำระ")

with st.form("payment_form"):
    customer_name = st.selectbox("ชื่อลูกค้า", options=customers_df["NAME"].tolist())
    payment_date = st.date_input("วันที่ชำระ", value=datetime.today())
    amount_paid = st.number_input("จำนวนเงินที่จ่าย", min_value=0.0, step=100.0)
    note = st.text_input("หมายเหตุ (ถ้ามี)", "")
    submit_btn = st.form_submit_button("💾 บันทึกข้อมูลและพิมพ์ใบเสร็จ")

# ----------------------------
# บันทึกข้อมูลลง Excel
# ----------------------------
payments_file = "debt_payments.xlsx"
if os.path.exists(payments_file):
    payments_df = pd.read_excel(payments_file)
else:
    payments_df = pd.DataFrame(columns=["ชื่อลูกค้า", "วันที่จ่าย", "จำนวนเงิน", "หมายเหตุ"])

if submit_btn:
    new_row = {
        "ชื่อลูกค้า": customer_name,
        "วันที่จ่าย": payment_date.strftime("%Y-%m-%d"),
        "จำนวนเงิน": amount_paid,
        "หมายเหตุ": note
    }
    payments_df = pd.concat([payments_df, pd.DataFrame([new_row])], ignore_index=True)
    payments_df.to_excel(payments_file, index=False)
    st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว")

# ----------------------------
# แสดงยอดทันที
# ----------------------------
if customer_name:
    total_due = customer_amounts[customer_name]
    current_fiscal = payment_date.year if payment_date.month >= 4 else payment_date.year - 1
    start_date = date(current_fiscal, 4, 5)
    end_date = date(current_fiscal + 1, 3, 5)

    this_year_df = payments_df[(payments_df["ชื่อลูกค้า"] == customer_name) & 
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date >= start_date) & 
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date <= end_date)]

    paid_sum = this_year_df["จำนวนเงิน"].sum()
    required_yearly = total_due / 4
    remaining = required_yearly - paid_sum

    today = datetime.today().date()
    penalty = 0
    if today > end_date:
        penalty = max(0, remaining) * 0.15

    st.markdown(f"<div style='color:#FFFFFF; font-size:20px;'>ยอดหนี้ทั้งหมด:&nbsp;&nbsp;&nbsp;&nbsp;{total_due:,.2f} บาท</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#FFFFFF; font-size:20px;'>ยอดสะสมปี {current_fiscal}-{current_fiscal+1}:&nbsp;&nbsp;&nbsp;&nbsp;{paid_sum:,.2f} บาท</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#FFFFFF; font-size:20px;'>ยอดคงเหลือปีนี้:&nbsp;&nbsp;&nbsp;&nbsp;{remaining:,.2f} บาท</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#FFFFFF; font-size:20px;'>ค่าปรับ (ถ้ามี):&nbsp;&nbsp;&nbsp;&nbsp;{penalty:,.2f} บาท</div>", unsafe_allow_html=True)

        # คำนวณยอดชำระรวม 4 ปี และยอดหนี้คงเหลือรวม 4 ปี
    start_4_years_ago = date(current_fiscal - 3, 4, 5)
    end_this_year = date(current_fiscal + 1, 3, 5)

    paid_4_years = payments_df[
        (payments_df["ชื่อลูกค้า"] == customer_name) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date >= start_4_years_ago) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date <= end_this_year)
    ]["จำนวนเงิน"].sum()

    total_remaining_4_years = total_due - paid_4_years

    st.markdown(f"<div style='color:#FFFFFF; font-size:20px;'>ยอดหนี้คงเหลือรวม 4 ปี:&nbsp;&nbsp;&nbsp;&nbsp;{total_remaining_4_years:,.2f} บาท</div>", unsafe_allow_html=True)

      # ----------------------------
    # สร้างใบเสร็จ PDF (A4)
    # ----------------------------
    if submit_btn:
        receipt_name = f"receipt_{customer_name}_{payment_date.strftime('%Y%m%d')}.pdf"
        pdf = FPDF("P", "mm", "A4")
        pdf.add_page()

        pdf.add_font('THSarabunNew', '', 'THSarabunNew.ttf', uni=True)

        pdf.set_font('THSarabunNew', '', 26)
        pdf.set_y(20)
        pdf.cell(0, 10, "ใบเสร็จรับเงิน", ln=True, align='L')
        pdf.ln(10)

        pdf.set_font('THSarabunNew', '', 18)
        pdf.cell(100, 10, f"ชื่อ: {customer_name}",ln=True, align='L')
        pdf.cell(0, 10,f"วันที่ชำระ: {payment_date.strftime('%d/%m/%Y')}", ln=True, align='L')

        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        pdf.set_font('THSarabunNew', '', 16)
        pdf.cell(80, 10, "จำนวนที่จ่าย:", align='L')
        pdf.cell(0, 10, f"{amount_paid:,.2f} บาท", ln=True, align='R')

        pdf.cell(80, 10, "ค่าปรับ (ถ้ามี):", align='L')
        pdf.cell(0, 10, f"{penalty:,.2f} บาท", ln=True, align='R')

        pdf.cell(80, 10, "รวมทั้งสิ้น (รวมค่าปรับ):", align='L')
        pdf.cell(0, 10, f"{amount_paid + penalty:,.2f} บาท", ln=True, align='R')

        pdf.ln(10)

        pdf.cell(80, 10, f"ยอดสะสมปี {current_fiscal}-{current_fiscal+1}:", align='L')
        pdf.cell(0, 10, f"{paid_sum:,.2f} บาท", ln=True, align='R')

        pdf.cell(80, 10, "ยอดคงเหลือปีนี้:", align='L')
        pdf.cell(0, 10, f"{remaining:,.2f} บาท", ln=True, align='R')

        # คำนวณยอดชำระรวม 4 ปี และยอดหนี้คงเหลือรวม 4 ปี
        start_4_years_ago = date(current_fiscal - 3, 4, 5)
        end_this_year = date(current_fiscal + 1, 3, 5)

        paid_4_years = payments_df[
        (payments_df["ชื่อลูกค้า"] == customer_name) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date >= start_4_years_ago) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date <= end_this_year)
        ]["จำนวนเงิน"].sum()

        total_remaining_4_years = total_due - paid_4_years

        pdf.cell(80, 10, "ยอดหนี้คงเหลือรวม 4 ปี:", align='L')
        pdf.cell(0, 10, f"{total_remaining_4_years:,.2f} บาท", ln=True, align='R')


        pdf.ln(10)

        pdf.cell(0, 10, f"หมายเหตุ: {note}", ln=True, align='L')
        pdf.ln(10)

        pdf.set_font('THSarabunNew', '', 14)
        pdf.cell(0, 10, "ผู้รับเงิน..................................                                                                                           ผู้ชำระเงิน..................................", ln=True, align='L')

        pdf.output(receipt_name)

        with open(receipt_name, "rb") as f:
            st.download_button("📥 ดาวน์โหลดใบเสร็จ (PDF)", f, file_name=receipt_name)

    # ----------------------------
    # ตารางสรุปยอดย้อนหลัง 4 ปี
    # ----------------------------
    st.header("[2] สรุปยอดย้อนหลัง 4 ปี")
    summary = []
    for i in range(4):
        year = current_fiscal - i
        start = date(year, 4, 5)
        end = date(year + 1, 3, 5)
        df_year = payments_df[(payments_df["ชื่อลูกค้า"] == customer_name) & 
                               (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date >= start) & 
                               (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date <= end)]
        paid = df_year["จำนวนเงิน"].sum()
        due = total_due / 4
        balance = due - paid
        summary.append({
            "ปีงบประมาณ": f"{year}-{year+1}",
            "ยอดที่ต้องจ่าย": due,
            "ยอดที่จ่ายแล้ว": paid,
            "ยอดคงเหลือ": balance
        })

    summary_df = pd.DataFrame(summary)
    st.dataframe(summary_df.style.format({
        "ยอดที่ต้องจ่าย": "{:,.2f}",
        "ยอดที่จ่ายแล้ว": "{:,.2f}",
        "ยอดคงเหลือ": "{:,.2f}"
    }))
    st.header("[3] สรุปรายปี + ค่าปรับ (รายบุคคล)")

fiscal_ranges = {
    "2025-2026": (date(2025, 4, 5), date(2026, 3, 5)),
    "2026-2027": (date(2026, 4, 5), date(2027, 3, 5)),
    "2027-2028": (date(2027, 4, 5), date(2028, 3, 5)),
    "2028-2029": (date(2028, 4, 5), date(2029, 3, 5))
}

selected_range = st.selectbox("เลือกช่วงปีงบประมาณ", list(fiscal_ranges.keys()))
start_date, end_date = fiscal_ranges[selected_range]
st.subheader(f"รายงาน: {selected_range} ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})")

if datetime.today().date() < end_date:
    st.info("📌 ยังไม่ถึงกำหนดสิ้นปี จึงไม่มีข้อมูลค่าปรับ")
else:
    total_debt = customer_amounts[customer_name]
    required_yearly = total_debt / 4

    paid = payments_df[(payments_df["ชื่อลูกค้า"] == customer_name) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date >= start_date) &
        (pd.to_datetime(payments_df["วันที่จ่าย"]).dt.date <= end_date)]["จำนวนเงิน"].sum()

    shortage = max(0, required_yearly - paid)
    penalty = shortage * 0.15

    report_df = pd.DataFrame([{
        "ยอดต้องจ่าย": required_yearly,
        "ยอดที่จ่าย": paid,
        "ขาด": shortage,
        "ค่าปรับ": penalty
    }])

    st.dataframe(report_df.style.format("{:.2f}"))