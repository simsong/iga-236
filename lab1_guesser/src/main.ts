import * as openpgp from "openpgp";
import { generatePassword, formatTime } from "./utils";

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
let gpgMessage: Awaited<ReturnType<typeof openpgp.readMessage>> | null = null;

// Character sets
const LOWERCASE = "abcdefghijklmnopqrstuvwxyz";
const UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?";
const DIGITS = "0123456789";


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
 */
async function tryDecrypt(password: string): Promise<boolean> {
  if (!gpgMessage) {
    try {
      const encryptedText = encryptedInput.value.trim();
      if (!encryptedText) return false;
      gpgMessage = await openpgp.readMessage({
        armoredMessage: encryptedText
      });
    } catch {
      return false;
    }
  }
  
  try {
    const { data: decrypted } = await openpgp.decrypt({
      message: gpgMessage,
      passwords: [password],
      format: "utf8"
    });
    
    // Success!
    decryptedOutput.value = decrypted as string;
    body.style.backgroundColor = "#d4edda"; // Light green
    return true;
  } catch {
    return false;
  }
}

/**
 * Main guessing loop using requestAnimationFrame
 */
async function guessingLoop() {
  if (!isRunning || isPaused) {
    animationFrameId = null;
    return;
  }
  
  // Try a batch of passwords per frame (for performance)
  const batchSize = 10;
  let tried = 0;
  
  while (tried < batchSize && currentGuess < totalPossible && isRunning && !isPaused) {
    const password = generatePassword(currentGuess, alphabet, passwordLen);
    currentPasswordInput.value = password;
    
    const found = await tryDecrypt(password);
    if (found) {
      isRunning = false;
      btnStart.disabled = false;
      btnStop.disabled = true;
      return;
    }
    
    currentGuess++;
    guessesSinceLastUpdate++;
    tried++;
    
    updateStats();
  }
  
  if (currentGuess >= totalPossible) {
    // Exhausted all possibilities
    isRunning = false;
    btnStart.disabled = false;
    btnStop.disabled = true;
    body.style.backgroundColor = "";
    decryptedOutput.value = "cannot decrypt";
    return;
  }
  
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
  
  // Reset GPG message to force re-read
  gpgMessage = null;
  
  if (!isRunning) {
    // Starting fresh
    currentGuess = 0;
    startTime = Date.now();
    lastUpdateTime = startTime;
    guessesSinceLastUpdate = 0;
    decryptedOutput.value = "";
    body.style.backgroundColor = "#f8d7da"; // Light red
  }
  
  isRunning = true;
  isPaused = false;
  btnStart.disabled = true;
  btnStop.disabled = false;
  
  // Start the loop
  if (!animationFrameId) {
    animationFrameId = requestAnimationFrame(guessingLoop);
  }
}

/**
 * Stop/pause guessing
 */
function stopGuessing() {
  isPaused = true;
  isRunning = false;
  btnStart.disabled = false;
  btnStop.disabled = true;
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
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
  gpgMessage = null;
  currentPasswordInput.value = "";
  decryptedOutput.value = "";
  guessesPerSecInput.value = "0";
  elapsedTimeInput.value = "00:00:00";
  estTimeInput.value = "00:00:00";
  body.style.backgroundColor = "";
}

// Event listeners
btnStart.addEventListener("click", startGuessing);
btnStop.addEventListener("click", stopGuessing);
btnReset.addEventListener("click", resetGuessing);

// Update alphabet when checkboxes or length change
chkLowercase.addEventListener("change", updateAlphabet);
chkUppercase.addEventListener("change", updateAlphabet);
chkSymbols.addEventListener("change", updateAlphabet);
chkDigits.addEventListener("change", updateAlphabet);
passwordLenSelect.addEventListener("change", updateAlphabet);

// Initialize
updateAlphabet();
