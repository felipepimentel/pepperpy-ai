"""Convert text file to PDF."""

from fpdf import FPDF

# Create PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

# Read and write text
with open("sample.txt", "r") as f:
    for line in f:
        # Handle headers (lines starting with numbers followed by dots)
        if any(line.startswith(str(i) + ".") for i in range(10)):
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, line.strip(), ln=True)
            pdf.set_font("Helvetica", size=12)
        else:
            # Handle normal text
            pdf.multi_cell(0, 10, line.strip())

# Save PDF
pdf.output("sample.pdf")
