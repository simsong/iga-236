#!/usr/bin/env python3
# Generates a minimal PDF that *visibly* says "This file does not contain a virus"
# and *contains* the raw EICAR test string so AV will likely trigger.
# WARNING: Saving this file may trigger/quarantine by AV.

EICAR = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

def make_pdf_bytes():
    # PDF header; the second line is a binary marker recommended by the spec.
    parts = []
    parts.append(b"%PDF-1.4\n")
    parts.append(b"%\xE2\xE3\xCF\xD3\n")
    # Put the EICAR string in a PDF comment so it appears *verbatim* in the file bytes.
    parts.append(b"%" + EICAR.encode("ascii") + b"\n")

    # Objects we’ll assemble with correct byte offsets for the xref.
    # 1: Catalog
    obj1 = b"<< /Type /Catalog /Pages 2 0 R >>\n"
    # 2: Pages
    obj2 = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
    # 3: Single Page
    obj3 = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
    )
    # 4: Content stream (visible text)
    text = b"BT /F1 24 Tf 72 720 Td (This file does not contain a virus) Tj ET\n"
    obj4 = b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"endstream\n"
    # 5: Font
    obj5 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"

    objects = [obj1, obj2, obj3, obj4, obj5]

    # Assemble objects and track offsets.
    buf = b"".join(parts)
    offsets = [0]  # obj 0 is the free head; real objects start at index 1
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj\n".encode("ascii") + obj + b"endobj\n"

    # xref table
    startxref = len(buf)
    n = len(objects)
    xref = [b"xref\n", f"0 {n+1}\n".encode("ascii")]
    xref.append(b"0000000000 65535 f \n")  # free object 0
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("ascii"))
    buf += b"".join(xref)

    # trailer and EOF
    trailer = (
        b"trailer\n<< /Size " + str(n + 1).encode() +
        b" /Root 1 0 R >>\nstartxref\n" +
        str(startxref).encode() + b"\n%%EOF\n"
    )
    buf += trailer

    # (Optional) Append EICAR once more after EOF to maximize AV detection across engines.
    buf += b"\n" + EICAR.encode("ascii") + b"\n"
    return buf

def main(out_path="eicar_test.pdf"):
    data = make_pdf_bytes()
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Wrote {out_path} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
