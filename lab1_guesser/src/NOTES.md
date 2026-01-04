# Development Notes

## Mac Em-Dash Conversion Fix

### Problem
When copying GPG encrypted messages from Mac Mail (or other Mac applications), the system sometimes automatically converts sequences of hyphens into em dashes. For example:
- `-----BEGIN PGP MESSAGE-----` becomes `——BEGIN PGP MESSAGE——`
- This breaks GPG message parsing because GPG requires ASCII hyphens (`--`), not Unicode em dashes (`—`)

### Solution
A paste event listener on the encrypted message textarea automatically detects and fixes this conversion:

1. **Paste Event Handler**: Listens for paste events on the `encryptedMessage` textarea
2. **Post-Paste Processing**: Uses `setTimeout` to process the text after the paste operation completes
3. **Em-Dash Detection**: Checks if the text contains any em dashes (`—`)
4. **Automatic Replacement**: Replaces all em dashes with double hyphens (`--`)
5. **Event Triggering**: Dispatches an `input` event to trigger S2K parameter extraction if needed

### Implementation
```javascript
encryptedInput.addEventListener("paste", (e) => {
  setTimeout(() => {
    const text = encryptedInput.value;
    if (text.includes("—")) {
      encryptedInput.value = text.replace(/—/g, "--");
      encryptedInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, 0);
});
```

### Why This Approach
- **Non-intrusive**: Only fixes the text if em dashes are detected
- **Automatic**: No user action required - happens transparently after paste
- **Preserves Workflow**: Triggers input event so S2K extraction still works
- **Simple**: Single regex replacement handles all occurrences

## S2K Parameter Extraction and Display

### Overview
The application extracts and displays S2K (String-to-Key) parameters from GPG encrypted messages. These parameters are shown in a form between the encrypted message textarea and the decrypted message output.

### Implementation Details

#### 1. Message Structure (OpenPGP.js v5)
When `openpgp.readMessage()` parses a GPG message, it returns a message object with a `packets` array. The first packet contains the S2K parameters:

```javascript
{
  packets: [
    {
      version: 4,
      sessionKeyAlgorithm: 9,  // Cipher algorithm (9 = AES256)
      s2k: {
        algorithm: 8,         // Hash algorithm (8 = SHA256)
        type: "iterated",      // S2K type (string, not number)
        c: 252,                // Encoded iteration count
        salt: "6832A8D8C3F81B83"  // Salt as hex string
      },
      // ... other fields
    },
    // ... other packets
  ]
}
```

#### 2. Parameter Extraction
The `extractAndDisplayS2K()` function:

1. **Reads the message**: Uses `openpgp.readMessage()` to parse the armored GPG message
2. **Accesses packets**: The `packets` property is an array that can be accessed directly
3. **Finds S2K packet**: Looks for the first packet with both `sessionKeyAlgorithm` and `s2k` properties
4. **Extracts parameters**:
   - **Cipher**: Maps `sessionKeyAlgorithm` (9 → "AES256")
   - **S2K Type**: Converts `s2k.type` string ("iterated" → "Iterated and Salted S2K")
   - **Hash**: Maps `s2k.algorithm` (8 → "SHA256")
   - **Salt**: Uses `s2k.salt` directly (already a hex string)
   - **Iterations**: Calculates actual count from encoded value `s2k.c`

#### 3. Iteration Count Calculation
The encoded count (`s2k.c`) is a single byte that encodes the actual iteration count using the formula:
```
actual_count = (16 + (c & 15)) << ((c >> 4) + 6)
```

For example, `c = 252`:
- `exp = (252 >> 4) + 6 = 15 + 6 = 21`
- `mantissa = 16 + (252 & 15) = 16 + 12 = 28`
- `actual_count = 28 << 21 = 58,720,256`

#### 4. Form Population
The extracted values are populated into read-only form fields:
- `s2kCipher`: Cipher algorithm name
- `s2kAlgorithm`: S2K algorithm type
- `s2kHash`: Hash algorithm name
- `s2kSalt`: Salt as uppercase hex string
- `s2kIterations`: Actual count with encoded value in parentheses

#### 5. Display Logic
- The form is hidden by default (`style="display: none;"`)
- When S2K parameters are found, the form is shown via `style.display = "block"`
- The form element is found via `document.getElementById("s2kForm")` or through the input's `form` property as a fallback
- Input fields are checked for existence, but the form element check is optional (values can be set even if form element isn't found initially)

#### 6. Event Handling
- An `input` event listener on the encrypted message textarea triggers extraction
- Extraction happens automatically when a GPG message is pasted (detected by presence of "BEGIN PGP MESSAGE")
- If no valid message is detected, the form is hidden

### Algorithm Mappings

#### Cipher Algorithms (RFC 4880)
- 7: AES128
- 8: AES192
- 9: AES256
- 2: IDEA
- 3: TripleDES
- 4: CAST5
- 11: Twofish

#### Hash Algorithms (RFC 4880)
- 1: MD5
- 2: SHA1
- 3: RIPEMD160
- 8: SHA256
- 9: SHA384
- 10: SHA512
- 11: SHA224

#### S2K Types
- "simple": Simple S2K
- "salted": Salted S2K
- "iterated" or "iterated-salted": Iterated and Salted S2K

### Key Implementation Notes
1. **OpenPGP.js Structure**: The library uses a different structure than raw GPG packets - parameters are in the first packet's `s2k` object
2. **Type Handling**: S2K type is a string ("iterated"), not a number (unlike RFC 4880 which uses 0-3)
3. **Salt Format**: OpenPGP.js provides salt as a hex string, not a Uint8Array
4. **Form Element Access**: The form element may be null on initial page load, so we use fallback methods to find it
5. **Error Handling**: Extraction failures are caught silently and the form remains hidden

## OpenPGP.js "Modification Detected" Error Suppression

### Problem
When attempting to decrypt the same GPG message multiple times with different passwords (as required for password guessing/brute-forcing), OpenPGP.js logs debug messages:

```
[OpenPGP.js debug] Error: Modification detected.
```

These messages flood the console and are false positives - they occur because OpenPGP.js detects that the message object has been "modified" when attempting multiple decrypt operations, even though we're legitimately trying different passwords.

### Solution Attempts

1. **First attempt: Set `ignore_mdc_error` config**
   - Based on Stack Overflow answer: https://stackoverflow.com/questions/64251877/openpgp-js-getting-an-error-error-decrypting-message-session-key-decryption
   - Set `openpgp.config.ignore_mdc_error = true`
   - **Result**: Did not suppress the debug messages (they're logged, not thrown as exceptions)

2. **Second attempt: Filter `console.debug`**
   - Intercepted `console.debug` to filter out messages containing "Modification detected"
   - **Result**: OpenPGP.js may use different console methods, so this didn't catch all messages

3. **Final solution: Intercept all console methods**
   - Intercept `console.debug`, `console.error`, `console.warn`, and `console.log`
   - Filter any message containing "Modification detected" or "[OpenPGP.js debug]"
   - **Result**: Successfully suppresses all OpenPGP.js modification detection debug messages

### Implementation Details

The suppression code is in `main.ts` at the top level, right after importing OpenPGP.js. It:
- Preserves original console methods
- Filters messages based on content (not just method)
- Only suppresses OpenPGP.js modification-related messages, not other important logs

### Why This Approach

- **Config option didn't work**: The `ignore_mdc_error` config prevents exceptions but doesn't suppress debug logging
- **Console interception is necessary**: OpenPGP.js uses internal logging that bypasses normal error handling
- **Comprehensive filtering**: Intercepting all console methods ensures we catch messages regardless of which method OpenPGP.js uses
- **Safe filtering**: Only filters specific OpenPGP.js debug messages, preserving all other console output

### References

- Stack Overflow: https://stackoverflow.com/questions/64251877/openpgp-js-getting-an-error-error-decrypting-message-session-key-decryption
- OpenPGP.js version: 5.11.3

