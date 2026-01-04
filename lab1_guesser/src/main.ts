import * as openpgp from "openpgp";
import { generatePassword, formatTime } from "./utils";

// Configure OpenPGP.js to ignore MDC (Modification Detection Code) errors
// This is necessary when trying multiple passwords on the same message,
// as OpenPGP.js may flag repeated decrypt attempts as modifications
// Reference: https://stackoverflow.com/questions/64251877/openpgp-js-getting-an-error-error-decrypting-message-session-key-decryption
try {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (openpgp.config as any).ignore_mdc_error = true;
} catch {
  // Config might not be available in this version
}

// Suppress OpenPGP.js debug/error messages for "Modification detected"
// These are expected when trying multiple passwords on the same message
// OpenPGP.js logs these through various console methods
const shouldSuppress = (args: unknown[]): boolean => {
  const message = args.map(arg => String(arg)).join(" ");
  return message.includes("Modification detected") || 
         message.includes("[OpenPGP.js debug]");
};

const originalConsoleDebug = console.debug;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleLog = console.log;

console.debug = (...args: unknown[]) => {
  if (!shouldSuppress(args)) {
    originalConsoleDebug.apply(console, args);
  }
};

console.error = (...args: unknown[]) => {
  if (!shouldSuppress(args)) {
    originalConsoleError.apply(console, args);
  }
};

console.warn = (...args: unknown[]) => {
  if (!shouldSuppress(args)) {
    originalConsoleWarn.apply(console, args);
  }
};

console.log = (...args: unknown[]) => {
  if (!shouldSuppress(args)) {
    originalConsoleLog.apply(console, args);
  }
};

// UI Elements
const chkLowercase = document.getElementById("chkLowercase") as HTMLInputElement;
const chkUppercase = document.getElementById("chkUppercase") as HTMLInputElement;
const chkSymbols = document.getElementById("chkSymbols") as HTMLInputElement;
const chkDigits = document.getElementById("chkDigits") as HTMLInputElement;
const passwordLenSelect = document.getElementById("passwordLen") as HTMLSelectElement;
const possibleCharsInput = document.getElementById("possibleChars") as HTMLInputElement;
const totalPossibleInput = document.getElementById("totalPossible") as HTMLInputElement;
const guessesPerSecInput = document.getElementById("guessesPerSec") as HTMLInputElement;
const elapsedTimeInput = document.getElementById("elapsedTime") as HTMLInputElement;
const estTimeInput = document.getElementById("estTime") as HTMLInputElement;
const btnStart = document.getElementById("btnStart") as HTMLButtonElement;
const btnStop = document.getElementById("btnStop") as HTMLButtonElement;
const btnReset = document.getElementById("btnReset") as HTMLButtonElement;
const btnDecrypt = document.getElementById("btnDecrypt") as HTMLButtonElement;
const currentPasswordInput = document.getElementById("currentPassword") as HTMLInputElement;
const encryptedInput = document.getElementById("encryptedMessage") as HTMLTextAreaElement;
const decryptedOutput = document.getElementById("decryptedMessage") as HTMLTextAreaElement;
const errorMessage = document.getElementById("errorMessage") as HTMLDivElement;
const body = document.body;

// State
let alphabet = "";
let passwordLen = 5;
let totalPossible = 0;
let currentGuess = 0;
let isRunning = false;
let isPaused = false;
let startTime = 0;
let lastUpdateTime = 0;
let guessesSinceLastUpdate = 0;
let animationFrameId: number | null = null;
let abortDecrypt = false; // Flag to ignore in-flight decrypts when stopped
let cachedEncryptedText = ""; // Cache encrypted text to avoid modification detection

// Character sets
const LOWERCASE = "abcdefghijklmnopqrstuvwxyz";
const UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?";
const DIGITS = "0123456789";


/**
 * Adjust font size of possibleChars input to fit all characters
 */
function adjustPossibleCharsFontSize() {
  const input = possibleCharsInput;
  const container = input.parentElement;
  if (!container) return;
  
  // Reset to default size to measure
  input.style.fontSize = "1rem";
  
  // Check if content overflows
  if (input.scrollWidth > input.clientWidth && input.value.length > 0) {
    // Calculate scale factor
    const scale = input.clientWidth / input.scrollWidth;
    // Set font size (minimum 0.5rem for readability)
    const newSize = Math.max(0.5, scale) * 1;
    input.style.fontSize = `${newSize}rem`;
  }
}

/**
 * Update the alphabet and total possible passwords based on checkboxes
 */
function updateAlphabet() {
  alphabet = "";
  if (chkLowercase.checked) alphabet += LOWERCASE;
  if (chkUppercase.checked) alphabet += UPPERCASE;
  if (chkSymbols.checked) alphabet += SYMBOLS;
  if (chkDigits.checked) alphabet += DIGITS;
  
  possibleCharsInput.value = alphabet;
  
  // Adjust font size to fit all characters
  setTimeout(adjustPossibleCharsFontSize, 0);
  
  passwordLen = parseInt(passwordLenSelect.value);
  totalPossible = Math.pow(alphabet.length, passwordLen);
  totalPossibleInput.value = totalPossible.toLocaleString();
}

/**
 * Update statistics display
 */
function updateStats() {
  const now = Date.now();
  const elapsedSeconds = (now - startTime) / 1000;
  
  // Update guesses per second (using last second's data)
  if (now - lastUpdateTime >= 1000) {
    const gps = guessesSinceLastUpdate / ((now - lastUpdateTime) / 1000);
    guessesPerSecInput.value = gps.toFixed(2);
    guessesSinceLastUpdate = 0;
    lastUpdateTime = now;
  }
  
  elapsedTimeInput.value = formatTime(elapsedSeconds);
  
  // Calculate estimated time to try all passwords
  if (guessesSinceLastUpdate > 0 && currentGuess > 0) {
    const avgGps = currentGuess / elapsedSeconds;
    if (avgGps > 0) {
      const remainingGuesses = totalPossible - currentGuess;
      const estSeconds = remainingGuesses / avgGps;
      estTimeInput.value = formatTime(estSeconds);
    }
  }
}

/**
 * Attempt to decrypt with a password
 * @param password - The password to try
 * @param ignoreAbort - If true, ignore abortDecrypt flag (for manual decrypt)
 * @returns true if decryption succeeded, false otherwise
 */
async function tryDecrypt(password: string, ignoreAbort = false): Promise<boolean> {
  // Check if we should abort (unless this is a manual decrypt)
  if (!ignoreAbort && abortDecrypt) {
    return false;
  }
  
  // Get encrypted text and cache it to avoid modification detection issues
  const encryptedText = encryptedInput.value.trim();
  if (!encryptedText) return false;
  
  // Update cache if text changed (for manual edits)
  if (ignoreAbort || encryptedText !== cachedEncryptedText) {
    cachedEncryptedText = encryptedText;
  }
  
  // Always read the message fresh for each decrypt attempt
  // OpenPGP.js message objects can't be reused across multiple decrypt calls
  let message: Awaited<ReturnType<typeof openpgp.readMessage>>;
  try {
    message = await openpgp.readMessage({
      armoredMessage: cachedEncryptedText
    });
  } catch {
    return false;
  }
  
  // Check again after async operation
  if (!ignoreAbort && abortDecrypt) {
    return false;
  }
  
  try {
    const { data: decrypted } = await openpgp.decrypt({
      message: message,
      passwords: [password],
      format: "utf8"
    });
    
    // Success! Return true regardless of abortDecrypt - if we found it, we found it
    decryptedOutput.value = decrypted as string;
    body.classList.remove("bg-error");
    body.classList.add("bg-success");
    return true;
  } catch {
    // Decrypt failed - check if we should abort before returning
    if (!ignoreAbort && abortDecrypt) {
      return false;
    }
    return false;
  }
}

/**
 * Manual decrypt function (called by Decrypt button)
 */
async function manualDecrypt() {
  const password = currentPasswordInput.value.trim();
  if (!password) {
    errorMessage.textContent = "Please enter a password.";
    return;
  }
  
  const encryptedText = encryptedInput.value.trim();
  if (!encryptedText) {
    errorMessage.textContent = "Please enter an encrypted GPG message.";
    return;
  }
  
  errorMessage.textContent = "";
  btnDecrypt.disabled = true;
  btnDecrypt.textContent = "Decrypting...";
  
  const found = await tryDecrypt(password, true); // ignoreAbort = true for manual
  
  if (!found) {
    decryptedOutput.value = "cannot decrypt";
    body.classList.remove("bg-success");
    body.classList.add("bg-error");
  }
  
  btnDecrypt.disabled = false;
  btnDecrypt.textContent = "Decrypt";
}

/**
 * Main guessing loop using requestAnimationFrame
 * Updates UI for EVERY password attempt (not batched)
 */
async function guessingLoop() {
  if (!isRunning || isPaused || abortDecrypt) {
    animationFrameId = null;
    return;
  }
  
  // Process one password per frame to ensure UI updates for every attempt
  if (currentGuess >= totalPossible) {
    // Exhausted all possibilities
    isRunning = false;
    btnStart.disabled = false;
    btnStop.disabled = true;
    currentPasswordInput.readOnly = false;
    if (!abortDecrypt) {
      decryptedOutput.value = "cannot decrypt";
      body.classList.remove("bg-success");
      body.classList.add("bg-error");
    } else {
      body.classList.remove("bg-success", "bg-error");
    }
    return;
  }
  
  const password = generatePassword(currentGuess, alphabet, passwordLen);
  
  // Update UI immediately for this password
  currentPasswordInput.value = password;
  
  // Make password input readonly during automation
  currentPasswordInput.readOnly = true;
  
  // Try to decrypt (this will check abortDecrypt internally)
  const found = await tryDecrypt(password, false);
  
  // If we found the password, stop immediately (regardless of abortDecrypt)
  if (found) {
    // Success!
    isRunning = false;
    abortDecrypt = false; // Clear abort flag since we succeeded
    btnStart.disabled = false;
    btnStop.disabled = true;
    currentPasswordInput.readOnly = false;
    animationFrameId = null;
    return;
  }
  
  // Check if we were aborted during decrypt (only if we didn't find it)
  if (abortDecrypt) {
    animationFrameId = null;
    return;
  }
  
  currentGuess++;
  guessesSinceLastUpdate++;
  updateStats();
  
  // Continue to next password
  animationFrameId = requestAnimationFrame(guessingLoop);
}

/**
 * Start guessing
 */
async function startGuessing() {
  if (isRunning && !isPaused) return;
  
  // Validate inputs and build error message
  updateAlphabet();
  const encryptedText = encryptedInput.value.trim();
  
  const errors: string[] = [];
  if (alphabet.length === 0) {
    errors.push("Please select at least one character set option.");
  }
  if (!encryptedText) {
    errors.push("Please enter an encrypted GPG message.");
  }
  
  const errorString = errors.join(" ");
  if (errorString) {
    errorMessage.textContent = errorString;
    return;
  }
  
  // Clear error message if validation passes
  errorMessage.textContent = "";
  
  // Cache encrypted text at start to ensure consistency
  cachedEncryptedText = encryptedInput.value.trim();
  abortDecrypt = false; // Reset abort flag
  
  if (!isRunning) {
    // Starting fresh
    currentGuess = 0;
    startTime = Date.now();
    lastUpdateTime = startTime;
    guessesSinceLastUpdate = 0;
    decryptedOutput.value = "";
    body.classList.remove("bg-success", "bg-error");
    body.classList.add("bg-error");
  }
  
  isRunning = true;
  isPaused = false;
  btnStart.disabled = true;
  btnStop.disabled = false;
  currentPasswordInput.readOnly = true; // Make readonly during automation
  
  // Start the loop
  if (!animationFrameId) {
    animationFrameId = requestAnimationFrame(guessingLoop);
  }
}

/**
 * Stop/pause guessing - IMMEDIATE response
 */
function stopGuessing() {
  // Set flags IMMEDIATELY to stop the loop
  abortDecrypt = true;
  isPaused = true;
  isRunning = false;
  
  // Cancel animation frame immediately
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  
  // Update UI immediately
  btnStart.disabled = false;
  btnStop.disabled = true;
  currentPasswordInput.readOnly = false; // Allow manual entry again
}

/**
 * Reset guessing
 */
function resetGuessing() {
  stopGuessing();
  currentGuess = 0;
  startTime = 0;
  lastUpdateTime = 0;
  guessesSinceLastUpdate = 0;
  abortDecrypt = false;
  currentPasswordInput.value = "";
  currentPasswordInput.readOnly = false;
  decryptedOutput.value = "";
  guessesPerSecInput.value = "0";
  elapsedTimeInput.value = "00:00:00";
  estTimeInput.value = "00:00:00";
  body.classList.remove("bg-success", "bg-error");
}

// Event listeners
btnStart.addEventListener("click", startGuessing);
btnStop.addEventListener("click", stopGuessing);
btnReset.addEventListener("click", resetGuessing);
btnDecrypt.addEventListener("click", manualDecrypt);

// Clear decrypted message and background when user starts typing
currentPasswordInput.addEventListener("input", () => {
  if (!currentPasswordInput.readOnly) {
    decryptedOutput.value = "";
    body.classList.remove("bg-success", "bg-error");
  }
});

// Allow Enter key to trigger manual decrypt
currentPasswordInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !currentPasswordInput.readOnly) {
    manualDecrypt();
  }
});

// Update alphabet when checkboxes or length change
chkLowercase.addEventListener("change", updateAlphabet);
chkUppercase.addEventListener("change", updateAlphabet);
chkSymbols.addEventListener("change", updateAlphabet);
chkDigits.addEventListener("change", updateAlphabet);
passwordLenSelect.addEventListener("change", updateAlphabet);

// Initialize
updateAlphabet();

// Adjust font size on window resize
window.addEventListener("resize", adjustPossibleCharsFontSize);
