/**
 * Utility functions for password generation and time formatting
 */

/**
 * Generate password number n from alphabet using base-N arithmetic
 * Generates passwords in lexicographic order: 'aa', 'ab', 'ac', ..., 'az', 'ba', ...
 * @param n - The password number (0-indexed)
 * @param alphabet - The character set to use
 * @param len - The length of the password
 * @returns The generated password string
 */
export function generatePassword(n: number, alphabet: string, len: number): string {
  const base = alphabet.length;
  if (base === 0) return "";
  if (len === 0) return "";
  
  // Build password from right to left (least significant first), then reverse
  // This gives us lexicographic order: 'aa', 'ab', 'ac', ..., 'az', 'ba', ...
  const chars: string[] = [];
  let remaining = n;
  
  for (let i = 0; i < len; i++) {
    chars.push(alphabet[remaining % base]);
    remaining = Math.floor(remaining / base);
  }
  
  // Reverse to get left-to-right order (most significant first)
  return chars.reverse().join("");
}

/**
 * Format time in HH:MM:SS format
 * @param seconds - Time in seconds (can be fractional)
 * @returns Formatted time string (HH:MM:SS)
 */
export function formatTime(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

