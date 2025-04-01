import os
import re
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import pdfplumber
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Static files route
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'message': 'No files selected'}), 400
    
    # Clear previous uploads
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

    # Save new uploads
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return jsonify({
        'success': True,
        'message': f'{len(files)} PDF file(s) uploaded successfully'
    })

@app.route('/process', methods=['POST'])
def process_files():
    try:
        # Initialize list to store extracted data
        all_data = []
        
        # Process each PDF in the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Processing file: {filename}")
                
                with pdfplumber.open(filepath) as pdf:
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

        # Create a DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=['Product ID', 'Product Name', 'QTY', 'Delivery Date'])
            df = df.drop_duplicates()

            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Data')
            
            output.seek(0)
            
            # Return the Excel file
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'PDF_Extracted_Data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        else:
            return jsonify({'success': False, 'message': 'No valid data found in the PDFs'}), 400

    except Exception as e:
        print(f"Error processing files: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing files: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
