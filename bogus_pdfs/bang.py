from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_popup_pdf(filename):
    # Create a new PDF
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Add JavaScript to show a pop-up when the PDF is opened
    js = "app.alert('bang', 3);"
    c.addForm('OpenAction', c.beginFormAction('OpenAction'))
    c.acroForm.action(js)
    c.endFormAction()
    
    # Draw some content (optional, to ensure the PDF has a visible page)
    c.drawString(100, 750, "PDF with Pop-up")
    
    # Set the JavaScript to run when the PDF opens
    c.showPage()
    c.setPageAction('/Open', 'OpenAction')
    
    # Save the PDF
    c.save()

if __name__ == "__main__":
    create_popup_pdf("popup.pdf")
    print("PDF created as 'popup.pdf'")
