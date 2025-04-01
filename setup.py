from setuptools import setup

setup(
    name="pdf-to-excel",
    version="1.0",
    install_requires=[
        "Flask==2.3.2",
        "pdfplumber==0.10.0",
        "pandas==2.0.3",
        "openpyxl==3.1.2",
        "Werkzeug==2.3.7",
        "gunicorn==21.2.0",
        "numpy==1.24.3"
    ],
)
