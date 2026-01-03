this is a single-page HTML application served from a static website or from Amazon Lando.

The application displays  a text field that is used to enter a GPG passphrase, and a text box that is used to enter a GPG password-protected encrypted document. When the decrypt button is pressed, it runs the JavaScript version of GPG to do the decryption, and it either prints the decrypted version in a text box to the right or it prints that it is the wrong passphrase

Suggested Layout:
```
src/
  crypto_app/
    index.html
    styles.css
    src/        # TS/JS here (e.g., main.ts, worker.ts, ingest.ts, virtual_list.ts)
build/
  crypto_app/   # Vite output for Lambda to serve statically
vite.config.ts
Makefile
package.json
```
