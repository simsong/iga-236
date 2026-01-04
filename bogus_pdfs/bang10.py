#!/usr/bin/env python3
from pypdf import PdfWriter

def main():
    writer = PdfWriter()
    # 8.5" x 11" page
    writer.add_blank_page(width=612, height=792)
    writer.add_js("app.alert('bang');")
    with open("bang.pdf", "wb") as f:
        writer.write(f)

if __name__ == "__main__":
    main()

