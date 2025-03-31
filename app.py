import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from flask import Flask, request, render_template, send_file

app = Flask(__name__)

# Define directories
PDF_FOLDER = "pdf_files"
OUTPUT_FOLDER = "output"
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_pdfs():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        return None, "No PDF files found."

    all_data = []

    for file_name in pdf_files:
        file_path = os.path.join(PDF_FOLDER, file_name)
        print(f"\nProcessing file: {file_name}")

        # Open PDF with pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue  # Skip empty pages

                # Normalize spaces
                text = re.sub(r"\s+", " ", text)

                # Split text into product blocks based on Product ID (10-digit number)
                product_blocks = re.split(r"(\d{10})", text)[1:]

                for i in range(0, len(product_blocks), 2):
                    product_id = product_blocks[i].strip()  # Extract Product ID
                    block_text = product_blocks[i + 1].strip()  # Extract details

                    # Extract Product Name
                    name_match = re.search(r"\d{10}\s+([A-Za-z0-9\-\s]+?)\s+PC", block_text)
                    product_name = name_match.group(1).strip() if name_match else "UNKNOWN"

                    # Extract Delivery Data
                    delivery_data = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{3})?\s+(\d{2}/\d{2}/\d{4})", block_text)

                    for qty, delivery_date in delivery_data:
                        qty = qty if qty else "0.000"  # Fill missing QTY with 0.000
                        all_data.append([product_id, product_name, qty, delivery_date])

    if all_data:
        df = pd.DataFrame(all_data, columns=['Product ID', 'Product Name', 'QTY', 'Delivery Date'])
        df = df.drop_duplicates()

        # Define output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_FOLDER, f"Corrected_Forecast_{timestamp}.xlsx")

        df.to_excel(output_path, index=False)
        return output_path, None

    return None, "No valid data found in the PDFs."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    uploaded_files = request.files.getlist("pdf_files")
    
    if not uploaded_files:
        return "No files uploaded."

    # Save uploaded files
    for file in uploaded_files:
        file.save(os.path.join(PDF_FOLDER, file.filename))

    output_file, error = process_pdfs()
    if error:
        return error

    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
