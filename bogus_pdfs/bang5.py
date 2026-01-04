from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_popup_pdf(filename):
    # Create a new PDF
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Define the JavaScript for the pop-up
    js = "app.alert('bang', 3);"
    
    # Create an annotation to trigger the JavaScript when the PDF opens
    c.AA('/Open', js, subtype='JavaScript')
    
    # Draw some content (optional, to ensure the PDF has a visible page)
    c.drawString(100, 750, "PDF with Pop-up")
    
    # Save the PDF
    c.showPage()
    c.save()

if __name__ == "__main__":
    create_popup_pdf("popup.pdf")
    print("PDF created as 'popup.pdf'")
