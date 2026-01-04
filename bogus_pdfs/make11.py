#!/usr/bin/env python3
import urllib.request

# EICAR test string
EICAR = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

def make_pdf_bytes():
    parts = []
    parts.append(b"%PDF-1.4\n")
    parts.append(b"%\xE2\xE3\xCF\xD3\n")
    parts.append(b"%" + EICAR.encode("ascii") + b"\n")

    obj1 = b"<< /Type /Catalog /Pages 2 0 R >>\n"
    obj2 = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
    obj3 = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
    )
    text = b"BT /F1 24 Tf 72 720 Td (This file does not contain a virus) Tj ET\n"
    obj4 = b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"endstream\n"
    obj5 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"

    objects = [obj1, obj2, obj3, obj4, obj5]

    buf = b"".join(parts)
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj\n".encode("ascii") + obj + b"endobj\n"

    startxref = len(buf)
    n = len(objects)
    xref = [b"xref\n", f"0 {n+1}\n".encode("ascii")]
    xref.append(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("ascii"))
    buf += b"".join(xref)

    trailer = (
        b"trailer\n<< /Size " + str(n + 1).encode() +
        b" /Root 1 0 R >>\nstartxref\n" +
        str(startxref).encode() + b"\n%%EOF\n"
    )
    buf += trailer
    buf += b"\n" + EICAR.encode("ascii") + b"\n"
    return buf

def fetch_url():
    url = "https://simson.net/foo.txt"
    try:
        with urllib.request.urlopen(url) as resp:
            print(f"Fetched {url}, HTTP {resp.status}, {len(resp.read())} bytes")
    except Exception as e:
        print(f"Error fetching {url}: {e}")

def main(out_path="eicar_test.pdf"):
    fetch_url()
    data = make_pdf_bytes()
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Wrote {out_path} ({len(data)} bytes)")

if __name__ == "__main__":
    main()

