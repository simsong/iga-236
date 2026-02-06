"""
Generate a different random quote for each student
"""

import random
import subprocess
import argparse
import uuid
import csv
from pathlib import Path
from  sendmail_o365v5 import send_mail

READINGS_DIR = "/Users/simsong/Library/CloudStorage/OneDrive-Personal/current/HKS IGA 236/2026 Optional Readings"
MINSIZE = 160
CONGRATS = "Congratulations! You decrypted the simple message.\n"
URL = "https://cybersecurity-policy.org/api/v1/decrypt/submit?guid={guid}"
OUTFILE = Path(__file__).parent / "outfile.csv"

README = """
Below are your encrypted messages. You can decrypt them using the tool at
https://cybersecurity-policy.org/static/lab1_guesser/index.html.
As an extra challenge, figure out the document from which your quotes were taken and
enter this information into Canvas for Lab #1.

"""


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

def encrypt(email,log,text,count,alphabet):
    guid = str(uuid.uuid4())

    with OUTFILE.open("a") as f:
        c = csv.writer(f)
        c.writerow([email,guid,count,len(alphabet)])

    text += "\n\n--\n\n" + URL.format(guid=guid) + "\n\n"
    password = "".join([random.choice(alphabet) for _ in range(count)])
    p = subprocess.run(f"gpg -ca --batch --passphrase '{password}'",input=text.encode(),stdout=subprocess.PIPE,shell=True)
    out = p.stdout.decode()
    log.write("\t"+password)
    return f"Encryption Alphabet: {alphabet}\nCharacter count: {count}\n{out}\n\n"


def assign(email,log):
    """Return the message assigned to the user"""
    source = random.choice(sources)
    log.write(email)
    out = []
    out.append(README)
    out.append(encrypt(email,log,CONGRATS,4,"1"))
    out.append(encrypt(email,log,source.random_paragraph(),4,"0123456789"))
    out.append(encrypt(email,log,source.random_paragraph(),3,"abcdefghijklmnopqrstuvwxyz"))
    out.append(encrypt(email,log,source.random_paragraph(),2,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
    log.write("\n")
    return "".join(out)


def main():
    parser = argparse.ArgumentParser(description='Send out emails',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--root", type=Path, default=READINGS_DIR, help="Root for readings.txt files")
    parser.add_argument("--emails", type=Path, default="emails.txt", help="List of emails to send")
    parser.add_argument("--log", type=Path, default="log.txt", help="logfile")
    args = parser.parse_args()

    log = args.log.open("a")

    for (dirpath, dirnames, filenames) in args.root.walk():
        for fname in filenames:
            if fname.endswith(".txt"):
                sources.append(Source(dirpath /fname))
    print("Sources: ",len(sources))
    with args.emails.open() as f:
        for line in f:
            email = line.strip()
            print(email)
            body = assign(email,log)
            send_mail(email, "Your personalized IGA236 decryption assignment", body)
    log.close()

if __name__=="__main__":
    main()
