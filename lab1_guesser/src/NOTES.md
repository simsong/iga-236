# Development Notes

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

