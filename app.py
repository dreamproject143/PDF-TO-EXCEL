# app.py

from flask import Flask, request, send_file, jsonify
import os
import pandas as pd
import re
import pdfplumber
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'message': 'No files part'}), 400
    files = request.files.getlist('files')
    for file in files:
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return jsonify({'message': 'Files successfully uploaded'}), 200

@app.route('/process', methods=['POST'])
def process_files():
    all_data = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    text = re.sub(r"\s+", " ", text)
                    product_blocks = re.split(r"(\d{10})", text)[1:]
                    for i in range(0, len(product_blocks), 2):
                        product_id = product_blocks[i].strip()
                        block_text = product_blocks[i + 1].strip()
                        name_match = re.search(r"\d{10}\s+([A-Za-z0-9\-\s]+?)\s+PC", block_text)
                        product_name = name_match.group(1).strip() if name_match else "UNKNOWN"
                        delivery_data = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{3})?\s+(\d{2}/\d{2}/\d{4})", block_text)
                        for qty, delivery_date in delivery_data:
                            qty = qty if qty else "0.000"
                            all_data.append([product_id, product_name, qty, delivery_date])
    
    if all_data:
        df = pd.DataFrame(all_data, columns=['Product ID', 'Product Name', 'QTY', 'Delivery Date'])
        df = df.drop_duplicates()
        output_path = os.path.join(OUTPUT_FOLDER, f"Corrected_Forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(output_path, index=False)
        return send_file(output_path, as_attachment=True)
    
    return jsonify({'message': 'No valid data found in the PDFs.'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
