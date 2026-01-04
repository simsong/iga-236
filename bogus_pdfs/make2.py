from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2

def create_initial_pdf(filename="initial.pdf"):
    """Creates a basic PDF with a visible text message."""
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 700, "THIS PDF DOES NOT CONTAIN A VIRUS")
    c.drawString(100, 680, "This file is for testing purposes only.")
    c.save()

def inject_eicar_into_pdf(input_file="initial.pdf", output_file="eicar_test_file.pdf"):
    """
    Injects the raw EICAR string into the PDF's internal structure.
    """
    # Define the EICAR string as raw bytes
    eicar_string = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    # Create the initial PDF
    create_initial_pdf(input_file)

    # Open the initial PDF in binary mode
    with open(input_file, 'rb') as in_f:
        pdf_reader = PyPDF2.PdfReader(in_f)
        pdf_writer = PyPDF2.PdfWriter()

        # Add all pages from the reader to the writer
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Create a new, raw stream object to hold the EICAR string
        eicar_stream = PyPDF2.pdf.StreamObject()
        eicar_stream.setData(eicar_string)
        
        # This is a key step: we add the raw stream to the PDF's objects list.
        # This makes the bytes part of the file's internal structure,
        # which is what antivirus software will scan.
        eicar_stream_ref = pdf_writer._addObject(eicar_stream)

        # You can add the EICAR object to the PDF's metadata or a page's dictionary,
        # but simply adding it to the object list is enough to trigger scanners.
        # For this demonstration, we just need the object to exist in the file.
        
        # Write the modified PDF to a new file
        with open(output_file, 'wb') as out_f:
            pdf_writer.write(out_f)

    print(f"Successfully created '{output_file}'.")
    print("This file should be detected by antivirus software.")

# Run the function
if __name__ == "__main__":
    inject_eicar_into_pdf()
