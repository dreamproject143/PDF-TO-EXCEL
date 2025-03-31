import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime

# Define folder where PDFs are stored
PDF_FOLDER = "./pdf_files"  # Change this to your local folder path
OUTPUT_FOLDER = "./output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Get list of all PDF files in the folder
pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]

if not pdf_files:
    print("No PDF files found in the folder.")
    exit()

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

# Create a DataFrame
if all_data:
    df = pd.DataFrame(all_data, columns=['Product ID', 'Product Name', 'QTY', 'Delivery Date'])

    # Remove duplicates
    df = df.drop_duplicates()

    # Define output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_FOLDER, f"Corrected_Forecast_{timestamp}.xlsx")

    df.to_excel(output_path, index=False)

    print(f"\n✅ Successfully saved all corrected data to: {output_path}")
else:
    print("\n⚠ No valid data found in the PDFs.")
