from flask import Flask, request, render_template, redirect, url_for, session, send_file
import mysql.connector
import datetime
import pandas as pd
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter



app = Flask(__name__, template_folder="templates")
app.secret_key = "your_secret_key"  # Needed for session storage

# Database connection
def connect_db():
    return mysql.connector.connect(host="localhost", user="root", password="#Chowdary@536", database="bill_db")

# Function to get the next Bill No
def get_next_bill_no():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT MAX(BillNo) FROM bills")
    last_bill_no = cursor.fetchone()[0]
    db.close()
    return f"S-{int(last_bill_no.split('-')[1]) + 1}" if last_bill_no else "S-1001"
@app.route('/', methods=['GET', 'POST'])
def bill():
    db = connect_db()
    cursor = db.cursor()

    if request.method == 'POST':
        # Generate Bill Number and Date
        bill_no = get_next_bill_no()
        bill_date = datetime.datetime.now().strftime("%Y-%m-%d")
        bill_time = datetime.datetime.now().strftime("%H:%M")

        # Insert Bill Record
        sql = "INSERT INTO Bills (BillNo, BillDate, BillTime) VALUES (%s, %s, %s)"
        values = (bill_no, bill_date, bill_time)
        cursor.execute(sql, values)

        items = []
        total_amount = 0

        # Insert Bill Items
        item_names = request.form.getlist('item_name[]')
        mrps = request.form.getlist('mrp[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')

        for i in range(len(item_names)):
            item_name = item_names[i]
            mrp = float(mrps[i])
            quantity = float(quantities[i])
            price = float(prices[i])
            amount = quantity * price
            total_amount += amount

            items.append({'ItemName': item_name, 'MRP': mrp, 'Quantity': quantity, 'Price': price, 'Amount': amount})

            sql_1 = "INSERT INTO BillItems (ItemName, BillNo, MRP, Quantity, Price, Amount) VALUES (%s, %s, %s, %s, %s, %s)"
            values_1 = (item_name, bill_no, mrp, quantity, price, amount)
            cursor.execute(sql_1, values_1)

        db.commit()

        return render_template("bill.html", bill_no=bill_no, bill_date=bill_date, bill_time=bill_time, items=items, total_amount=total_amount)

    # GET request - Retrieve the latest bill details
    cursor.execute("SELECT BillNo, BillDate, BillTime FROM Bills ORDER BY BillNo DESC LIMIT 1")
    bill_data = cursor.fetchone()

    if bill_data:
        bill_no, bill_date, bill_time = bill_data
        cursor.execute("SELECT ItemName, MRP, Quantity, Price, Amount FROM BillItems WHERE BillNo = %s", (bill_no,))
        items = cursor.fetchall()
        total_amount = sum(item[4] for item in items)

        db.close()

        return render_template("bill.html", bill_no=bill_no, bill_date=bill_date, bill_time=bill_time, 
                               items=[{'ItemName': row[0], 'MRP': row[1], 'Quantity': row[2], 'Price': row[3], 'Amount': row[4]} for row in items], 
                               total_amount=total_amount)

    db.close()
    return render_template("bill.html", bill_no=None, bill_date=None, bill_time=None, items=[], total_amount=0)

@app.route('/export/excel/<bill_no>')
def export_excel(bill_no):
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Fetch bill items for the given Bill Number
    cursor.execute("SELECT ItemName, MRP, Quantity, Price, Amount FROM BillItems WHERE BillNo = %s", (bill_no,))
    data = cursor.fetchall()

    # Calculate the total amount
    total_amount = sum(item['Amount'] for item in data) if data else 0
    db.close()

    if not data:
        return "No data found for this bill number", 404

    df = pd.DataFrame(data)

    # Add a total row
    total_row = pd.DataFrame([{
        "ItemName": "Total", 
        "MRP": "", 
        "Quantity": "", 
        "Price": "", 
        "Amount": total_amount
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    # Ensure folder exists
    excel_folder = r"D:\Projects\Bill-Receipt\Bill Excel"
    os.makedirs(excel_folder, exist_ok=True)

    # Save to Excel
    file_path = os.path.join(excel_folder, f"{bill_no}.xlsx")
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Bill Details")
        worksheet = writer.sheets["Bill Details"]
        worksheet.set_column('A:E', 15)  # Adjust column width

    return f"Excel file saved at {file_path}"

@app.route('/export/pdf/<bill_no>')
def export_pdf(bill_no):
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Fetch bill items for the given Bill Number
    cursor.execute("SELECT ItemName, MRP, Quantity, Price, Amount FROM BillItems WHERE BillNo = %s", (bill_no,))
    data = cursor.fetchall()

    # Calculate the total amount
    total_amount = sum(item['Amount'] for item in data) if data else 0
    db.close()

    if not data:
        return "No data found for this bill number", 404

    # Ensure folder exists
    pdf_folder = r"D:\Projects\Bill-Receipt\Bill Pdfs"
    os.makedirs(pdf_folder, exist_ok=True)

    # Save PDF
    file_path = os.path.join(pdf_folder, f"{bill_no}.pdf")
    pdf = canvas.Canvas(file_path, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    pdf.drawString(100, 750, f"Bill Details - {bill_no}")

    y_position = 720
    pdf.drawString(100, y_position, "Item Name")
    pdf.drawString(200, y_position, "MRP")
    pdf.drawString(300, y_position, "Quantity")
    pdf.drawString(400, y_position, "Price")
    pdf.drawString(500, y_position, "Amount")
    y_position -= 20

    for item in data:
        pdf.drawString(100, y_position, item['ItemName'])
        pdf.drawString(200, y_position, str(item['MRP']))
        pdf.drawString(300, y_position, str(item['Quantity']))
        pdf.drawString(400, y_position, str(item['Price']))
        pdf.drawString(500, y_position, str(item['Amount']))
        y_position -= 20

    # Add total amount row
    pdf.drawString(400, y_position - 20, "Total Amount:")
    pdf.drawString(500, y_position - 20, str(total_amount))

    pdf.save()

    return f"PDF file saved at {file_path}"

if __name__ == '__main__':
    app.run(debug=True)
