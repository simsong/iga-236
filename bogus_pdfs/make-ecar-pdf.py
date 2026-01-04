from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_eicar_test_pdf(filename):
    """
    Creates a PDF file with a specific text message and the EICAR test string.
    
    Args:
        filename (str): The name of the PDF file to be created.
    """
    try:
        # Create a new PDF file
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Define the EICAR string
        eicar_string = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        
        # Add the main text to the PDF
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 700, "THIS PDF DOES NOT CONTAIN A VIRUS")
        
        # Embed the EICAR string as a raw byte stream
        # This makes the string part of the PDF's internal content,
        # which is what antivirus software will scan.
        c.drawString(100, 650, f"Embedded EICAR Test String: {eicar_string.decode('utf-8')}")

        # You can also embed the string in an invisible part of the document
        # to ensure it's not visible but still scannable.
        # This example makes it visible for demonstration purposes.

        # Save the PDF
        c.save()
        
        print(f"Successfully created '{filename}'.")
        print("This file should be detected by antivirus software.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function to create the PDF
if __name__ == "__main__":
    create_eicar_test_pdf("eicar_test_document.pdf")
