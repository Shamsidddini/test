
from flask import Flask, render_template, request, redirect, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import qrcode
from io import BytesIO

app = Flask(__name__)

# Path to the data file
DATA_FILE = 'data/transactions.csv'

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Ensure the CSV file exists and is initialized
if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
    pd.DataFrame(columns=['Category', 'Amount', 'Type']).to_csv(DATA_FILE, index=False)

@app.route('/')
def index():
    # Read the data
    data = pd.read_csv(DATA_FILE)

    # Calculate totals
    income_total = data[data['Type'] == 'Income']['Amount'].sum()
    expenses_total = data[data['Type'] == 'Expense']['Amount'].sum()

    # Group expenses by category for visualization
    expense_data = data[data['Type'] == 'Expense'].groupby('Category')['Amount'].sum().to_dict()

    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Pass totals, expense data, and current time to the template
    return render_template('index.html', income=income_total, expenses=expenses_total, expense_data=expense_data, current_time=current_time)

@app.route('/add_income', methods=['GET', 'POST'])
def add_income():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        # Append income to the data file
        data = pd.read_csv(DATA_FILE)
        new_row = pd.DataFrame([{'Category': category, 'Amount': amount, 'Type': 'Income'}])
        data = pd.concat([data, new_row], ignore_index=True)
        data.to_csv(DATA_FILE, index=False)

        return redirect('/')
    return render_template('add_income.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        # Append expense to the data file
        data = pd.read_csv(DATA_FILE)
        new_row = pd.DataFrame([{'Category': category, 'Amount': amount, 'Type': 'Expense'}])
        data = pd.concat([data, new_row], ignore_index=True)
        data.to_csv(DATA_FILE, index=False)

        return redirect('/')
    return render_template('add_expense.html')

@app.route('/reset', methods=['POST'])
def reset():
    # Clear the contents of the CSV file by reinitializing it
    pd.DataFrame(columns=['Category', 'Amount', 'Type']).to_csv(DATA_FILE, index=False)
    return redirect('/')

@app.route('/generate_pdf')
def generate_pdf():
    # Read the data
    data = pd.read_csv(DATA_FILE)

    # File path for the PDF
    pdf_path = 'data/report.pdf'

    # File path for the chart image
    chart_path = 'data/chart.png'

    # Generate the pie chart
    expense_data = data[data['Type'] == 'Expense'].groupby('Category')['Amount'].sum()
    plt.figure(figsize=(6, 6))
    plt.pie(expense_data, labels=expense_data.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
    plt.title('Expenses by Category')
    plt.savefig(chart_path)
    plt.close()

    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 770, "Shams App - Financial Report")
    c.drawString(100, 750, f"Generated on: {current_time}")
    c.drawString(100, 730, f"Total Income: ${data[data['Type'] == 'Income']['Amount'].sum()}")
    c.drawString(100, 710, f"Total Expenses: ${data[data['Type'] == 'Expense']['Amount'].sum()}")

    # Add expense details by category
    c.drawString(100, 690, "Expenses by Category:")
    y = 670
    for category, amount in data[data['Type'] == 'Expense'].groupby('Category')['Amount'].sum().items():
        c.drawString(120, y, f"{category}: ${amount}")
        y -= 20

    # Embed the pie chart into the PDF
    c.drawImage(chart_path, 150, 400, width=300, height=300)  # Position and size of the chart
    c.save()

    # Serve the PDF
    return send_file(pdf_path, as_attachment=True)

@app.route('/qrcode')
def get_qrcode():
    url = request.host_url
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
