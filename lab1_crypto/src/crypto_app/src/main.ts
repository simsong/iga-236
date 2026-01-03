import * as openpgp from "openpgp";

const form = document.getElementById("decryptForm") as HTMLFormElement;
const passphraseInput = document.getElementById("passphrase") as HTMLInputElement;
const encryptedInput = document.getElementById("encryptedMessage") as HTMLTextAreaElement;
const decryptedOutput = document.getElementById("decryptedMessage") as HTMLTextAreaElement;
const decryptBtn = document.getElementById("decryptBtn") as HTMLButtonElement;

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  const passphrase = passphraseInput.value.trim();
  const encryptedText = encryptedInput.value.trim();
  
  if (!passphrase || !encryptedText) {
    decryptedOutput.value = "Please enter both passphrase and encrypted message.";
    return;
  }
  
  // Disable button during decryption
  decryptBtn.disabled = true;
  decryptBtn.textContent = "Decrypting...";
  decryptedOutput.value = "";
  
  try {
    // Read the encrypted message
    const message = await openpgp.readMessage({
      armoredMessage: encryptedText
    });
    
    // Attempt to decrypt
    const { data: decrypted } = await openpgp.decrypt({
      message,
      passwords: [passphrase],
      format: "utf8"
    });
    
    // Success - show decrypted message
    decryptedOutput.value = decrypted as string;
    
  } catch (error) {
    // Decryption failed
    decryptedOutput.value = "cannot decrypt";
  } finally {
    // Re-enable button
    decryptBtn.disabled = false;
    decryptBtn.textContent = "Decrypt";
  }
});

