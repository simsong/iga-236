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
const s2kForm = document.getElementById("s2kForm") as HTMLFormElement;
const s2kCipher = document.getElementById("s2kCipher") as HTMLInputElement;
const s2kAlgorithm = document.getElementById("s2kAlgorithm") as HTMLInputElement;
const s2kHash = document.getElementById("s2kHash") as HTMLInputElement;
const s2kSalt = document.getElementById("s2kSalt") as HTMLInputElement;
const s2kIterations = document.getElementById("s2kIterations") as HTMLInputElement;
const body = document.body;

// Verify S2K elements exist
if (!s2kForm || !s2kCipher || !s2kAlgorithm || !s2kHash || !s2kSalt || !s2kIterations) {
  console.error("S2K DOM elements not found on page load!");
  console.error("Missing:", {
    s2kForm: !s2kForm,
    s2kCipher: !s2kCipher,
    s2kAlgorithm: !s2kAlgorithm,
    s2kHash: !s2kHash,
    s2kSalt: !s2kSalt,
    s2kIterations: !s2kIterations
  });
} else {
  console.log("S2K DOM elements found on page load:", {
    s2kForm: s2kForm.id,
    s2kCipher: s2kCipher.id,
    s2kAlgorithm: s2kAlgorithm.id,
    s2kHash: s2kHash.id,
    s2kSalt: s2kSalt.id,
    s2kIterations: s2kIterations.id
  });
}

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
 * Extract and display S2K parameters from a GPG message
 */
async function extractAndDisplayS2K(encryptedText: string): Promise<void> {
  try {
    const message = await openpgp.readMessage({
      armoredMessage: encryptedText
    });
    
    // Extract S2K parameters from message packets
    // OpenPGP.js v5+ uses a packets iterator
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const msgAny = message as any;
    
    // Debug: log EVERYTHING about the message structure
    console.log("=== FULL MESSAGE OBJECT ===");
    console.log(JSON.stringify(msgAny, (key, value) => {
      // Handle circular references and functions
      if (typeof value === 'function') {
        return '[Function]';
      }
      if (value instanceof Uint8Array) {
        return Array.from(value).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
      }
      if (value instanceof ArrayBuffer) {
        return Array.from(new Uint8Array(value)).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
      }
      return value;
    }, 2));
    
    console.log("=== MESSAGE OBJECT KEYS ===");
    console.log(Object.keys(msgAny));
    
    console.log("=== MESSAGE PACKETS ===");
    console.log("msgAny.packets:", msgAny.packets);
    console.log("msgAny.packets type:", typeof msgAny.packets);
    console.log("msgAny.packets constructor:", msgAny.packets?.constructor?.name);
    
    // Try to inspect packets in detail
    if (msgAny.packets) {
      console.log("=== PACKETS ITERATION ===");
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const packetsArray = Array.from(msgAny.packets as any);
        console.log("Packets array length:", packetsArray.length);
        packetsArray.forEach((pkt: unknown, i: number) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const p = pkt as any;
          console.log(`Packet ${i}:`, {
            tag: p.tag,
            constructor: p.constructor?.name,
            keys: Object.keys(p),
            fullObject: JSON.stringify(p, (key, value) => {
              if (typeof value === 'function') return '[Function]';
              if (value instanceof Uint8Array) {
                return Array.from(value).map((b: number) => b.toString(16).padStart(2, '0')).join('').toUpperCase();
              }
              if (value instanceof ArrayBuffer) {
                return Array.from(new Uint8Array(value)).map((b: number) => b.toString(16).padStart(2, '0')).join('').toUpperCase();
              }
              return value;
            }, 2)
          });
        });
      } catch (e) {
        console.log("Error iterating packets:", e);
      }
    }
    
    // Try different ways to access packets
    let packets: unknown[] = [];
    
    // Method 1: Direct array access
    if (Array.isArray(msgAny.packets)) {
      packets = msgAny.packets;
      console.log("Packets accessed as array");
    }
    // Method 2: Iterator
    else if (msgAny.packets && typeof msgAny.packets[Symbol.iterator] === 'function') {
      try {
        packets = Array.from(msgAny.packets);
        console.log("Packets accessed via iterator");
      } catch (e) {
        console.log("Iterator failed:", e);
      }
    }
    // Method 3: Try packetList or list property
    else if (msgAny.packetList) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const list = msgAny.packetList as any;
      if (Array.isArray(list)) {
        packets = list;
      } else if (list && typeof list[Symbol.iterator] === 'function') {
        packets = Array.from(list);
      }
      console.log("Packets accessed via packetList");
    }
    // Method 4: Try accessing nested properties
    else if (msgAny.packets) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const pktObj = msgAny.packets as any;
      if (pktObj.list) {
        packets = Array.isArray(pktObj.list) ? pktObj.list : Array.from(pktObj.list);
        console.log("Packets accessed via packets.list");
      } else if (pktObj.packets) {
        packets = Array.isArray(pktObj.packets) ? pktObj.packets : Array.from(pktObj.packets);
        console.log("Packets accessed via packets.packets");
      }
    }
    
    // Method 5: Try to iterate using for...of if it's iterable
    if (packets.length === 0 && msgAny.packets) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const tempPackets: unknown[] = [];
        for (const pkt of msgAny.packets as any) {
          tempPackets.push(pkt);
        }
        packets = tempPackets;
        console.log("Packets accessed via for...of loop");
      } catch (e) {
        console.log("for...of failed:", e);
      }
    }
    
    console.log("Extracted packets:", packets);
    console.log("Number of packets:", packets.length);
    
    // Cipher algorithm mapping (RFC 4880)
    const cipherMap: Record<number, string> = {
      7: "AES128",
      8: "AES192", 
      9: "AES256",
      2: "IDEA",
      3: "TripleDES",
      4: "CAST5",
      11: "Twofish"
    };
    
    // Hash algorithm mapping (RFC 4880)
    const hashMap: Record<number, string> = {
      1: "MD5",
      2: "SHA1",
      3: "RIPEMD160",
      8: "SHA256",
      9: "SHA384",
      10: "SHA512",
      11: "SHA224"
    };
    
    // S2K algorithm mapping (RFC 4880)
    const s2kMap: Record<number, string> = {
      0: "Simple S2K",
      1: "Salted S2K",
      2: "Reserved",
      3: "Iterated and Salted S2K"
    };
    
    // Look for symmetric key encrypted data packet
    // Based on actual structure: first packet has sessionKeyAlgorithm and s2k
    for (let i = 0; i < packets.length; i++) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const pkt = packets[i] as any;
      
      console.log(`Packet ${i}:`, {
        version: pkt.version,
        sessionKeyAlgorithm: pkt.sessionKeyAlgorithm,
        s2k: pkt.s2k,
        keys: Object.keys(pkt)
      });
      
      // Look for packet with s2k and sessionKeyAlgorithm (first packet in the structure)
      if (pkt.s2k && pkt.sessionKeyAlgorithm !== null && pkt.sessionKeyAlgorithm !== undefined) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const symKeyPacket = pkt as any;
        
        const algorithm = symKeyPacket.sessionKeyAlgorithm; // This is the cipher algorithm
        const s2k = symKeyPacket.s2k;
        
        console.log("Found sym key packet with S2K:", { algorithm, s2k });
        
        if (algorithm && s2k) {
          // Map cipher algorithm
          const cipher = cipherMap[algorithm] || `Unknown (${algorithm})`;
          
          // Map S2K type (it's a string like "iterated", not a number)
          let s2kType = "Unknown";
          if (s2k.type === "iterated" || s2k.type === "iterated-salted") {
            s2kType = "Iterated and Salted S2K";
          } else if (s2k.type === "salted") {
            s2kType = "Salted S2K";
          } else if (s2k.type === "simple") {
            s2kType = "Simple S2K";
          } else if (s2k.type) {
            s2kType = s2k.type.charAt(0).toUpperCase() + s2k.type.slice(1) + " S2K";
          }
          
          // Map hash algorithm (s2k.algorithm is the hash algorithm)
          const hash = hashMap[s2k.algorithm ?? -1] || `Unknown (${s2k.algorithm})`;
          
          // Extract salt (it's already a hex string!)
          let salt = "N/A";
          if (s2k.salt) {
            if (typeof s2k.salt === 'string') {
              // Already a hex string, just uppercase it
              salt = s2k.salt.toUpperCase();
            } else if (s2k.salt instanceof Uint8Array) {
              salt = Array.from(s2k.salt as Uint8Array)
                .map((b) => b.toString(16).padStart(2, '0'))
                .join('')
                .toUpperCase();
            } else {
              // Try to convert array-like object
              const values = Object.values(s2k.salt) as number[];
              salt = Array.from(new Uint8Array(values))
                .map((b) => b.toString(16).padStart(2, '0'))
                .join('')
                .toUpperCase();
            }
          }
          
          // Extract iteration count (s2k.c is the encoded count)
          const encodedCount = s2k.c !== null && s2k.c !== undefined ? s2k.c : "N/A";
          // Calculate actual iteration count from encoded value
          // Encoded count formula: 16 + (c & 15)) << ((c >> 4) + 6)
          let actualCount = "N/A";
          if (typeof encodedCount === 'number') {
            const exp = (encodedCount >> 4) + 6;
            const mantissa = 16 + (encodedCount & 15);
            actualCount = (mantissa << exp).toLocaleString();
          }
          
          // Display S2K parameters in form fields
          const iterationsDisplay = actualCount !== "N/A" 
            ? `${actualCount} (encoded: ${encodedCount})`
            : String(encodedCount);
          
          console.log("Setting S2K display:", { cipher, s2kType, hash, salt, iterationsDisplay });
          console.log("S2K form elements:", { s2kForm, s2kCipher, s2kAlgorithm, s2kHash, s2kSalt, s2kIterations });
          
          // Check only the input fields (form element is optional for setting values)
          if (!s2kCipher || !s2kAlgorithm || !s2kHash || !s2kSalt || !s2kIterations) {
            console.error("S2K input elements not found!");
            console.error("Missing elements:", {
              s2kCipher: !s2kCipher,
              s2kAlgorithm: !s2kAlgorithm,
              s2kHash: !s2kHash,
              s2kSalt: !s2kSalt,
              s2kIterations: !s2kIterations
            });
            return;
          }
          
          console.log("Setting form field values...");
          s2kCipher.value = cipher;
          s2kAlgorithm.value = s2kType;
          s2kHash.value = hash;
          s2kSalt.value = salt;
          s2kIterations.value = iterationsDisplay;
          
          console.log("Values set:", {
            cipher: s2kCipher.value,
            algorithm: s2kAlgorithm.value,
            hash: s2kHash.value,
            salt: s2kSalt.value,
            iterations: s2kIterations.value
          });
          
          // Show the form if it exists (try multiple ways to find it)
          if (s2kForm) {
            s2kForm.style.display = "block";
            console.log("S2K form display set to block");
          } else {
            // Try to find the form via the input's form property or by ID
            const form = s2kCipher.form || document.getElementById("s2kForm");
            if (form) {
              (form as HTMLFormElement).style.display = "block";
              console.log("S2K form found via input.form, display set to block");
            } else {
              console.warn("S2K form element not found, but values were set");
            }
          }
          return;
        }
      }
    }
    
    // No S2K parameters found
    if (s2kForm) {
      s2kForm.style.display = "none";
    }
  } catch (error) {
    // Failed to parse message - hide S2K info
    console.debug("Failed to extract S2K parameters:", error);
    if (s2kForm) {
      s2kForm.style.display = "none";
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

// Extract and display S2K parameters when encrypted message changes
encryptedInput.addEventListener("input", () => {
  const text = encryptedInput.value.trim();
  console.log("Encrypted message input changed, length:", text.length);
  if (text && text.includes("BEGIN PGP MESSAGE")) {
    console.log("Attempting to extract S2K parameters...");
    void extractAndDisplayS2K(text);
  } else {
    console.log("No PGP message detected, hiding S2K info");
    if (s2kForm) {
      s2kForm.style.display = "none";
    }
  }
});

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
