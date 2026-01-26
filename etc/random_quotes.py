"""
Generate a different random quote for each student
"""

import random
import subprocess
import io
import uuid
import csv
from pathlib import Path
READINGS_DIR = "/Users/simsong/Library/CloudStorage/OneDrive-Personal/current/HKS IGA 236/2026 Optional Readings"
MINSIZE = 160
CONGRATS = "Congratulations! You decrypted the simple message.\n"
URL = "https://cybersecurity-policy.org/api/v1/decrypt/submit?guid={guid}"
OUTFILE = Path(__file__).parent / "outfile.csv"

sources = []
class Source:
    def __init__(self, path):
        self.path = path
        self.text = path.read_text(errors='ignore')
        self.paragraphs = self.text.split("\n")
    def __repr__(self):
        return str(self.path)
    def random_paragraph(self):
        for _ in range(100):
            text = random.choice(self.paragraphs).strip()
            if text[0:1] in "0123456789[.": # ignore references
                continue
            if len(text) > MINSIZE:
                return text
        raise RuntimeError(f"Could not find a paragraph in {self.path} longer than {MINSIZE} characters")

def encrypt(email,text,count,alphabet):
    guid = str(uuid.uuid4())

    with OUTFILE.open("a") as f:
        c = csv.writer(f)
        c.writerow([email,guid,count,len(alphabet)])

    print(OUTFILE)

    text += "\n\n--\n\n" + URL.format(guid=guid) + "\n\n"
    password = "".join([random.choice(alphabet) for _ in range(count)])
    print("password:",password)
    p = subprocess.run(f"gpg -ca --batch --passphrase '{password}'",input=text.encode(),stdout=subprocess.PIPE,shell=True)
    out = p.stdout.decode()
    print("Encrypted:")
    print(out)
    return f"Encryption Alphabet: {alphabet}\nCharacter count: {count}\n{out}\n\n"


def assign(email):
    source = random.choice(sources)
    print(source.path.name)
    out = []
    out.append(encrypt(email,CONGRATS,4,"1"))
    out.append(encrypt(email,source.random_paragraph(),4,"0123456789"))
    out.append(encrypt(email,source.random_paragraph(),3,"abcdefghijklmnopqrstuvwxyz"))
    out.append(encrypt(email,source.random_paragraph(),2,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
    print("".join(out))


def main():
    root = Path(READINGS_DIR)
    for (dirpath, dirnames, filenames) in root.walk():
        for fname in filenames:
            if fname.endswith(".txt"):
                sources.append(Source(dirpath /fname))
    print("Sources: ",len(sources))
    assign("simsong@acm.org")

if __name__=="__main__":
    main()
