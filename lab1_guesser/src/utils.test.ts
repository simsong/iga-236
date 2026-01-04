import { describe, it, expect } from "vitest";
import { generatePassword, formatTime } from "./utils";

describe("generatePassword", () => {
  it("should generate password of correct length", () => {
    const alphabet = "abc";
    const len = 5;
    const password = generatePassword(0, alphabet, len);
    expect(password).toHaveLength(len);
  });

  it("should generate first password (n=0) with first character repeated", () => {
    const alphabet = "abc";
    const password = generatePassword(0, alphabet, 3);
    expect(password).toBe("aaa");
  });

  it("should generate sequential passwords correctly in lexicographic order", () => {
    const alphabet = "ab";
    expect(generatePassword(0, alphabet, 2)).toBe("aa");
    expect(generatePassword(1, alphabet, 2)).toBe("ab");
    expect(generatePassword(2, alphabet, 2)).toBe("ba");
    expect(generatePassword(3, alphabet, 2)).toBe("bb");
  });

  it("should generate digits in correct order: 00, 01, 02, ..., 09, 10, 11", () => {
    const alphabet = "0123456789";
    expect(generatePassword(0, alphabet, 2)).toBe("00");
    expect(generatePassword(1, alphabet, 2)).toBe("01");
    expect(generatePassword(2, alphabet, 2)).toBe("02");
    expect(generatePassword(9, alphabet, 2)).toBe("09");
    expect(generatePassword(10, alphabet, 2)).toBe("10");
    expect(generatePassword(11, alphabet, 2)).toBe("11");
    expect(generatePassword(99, alphabet, 2)).toBe("99");
  });

  it("should generate lowercase letters in correct order: aa, ab, ac, ..., az, ba", () => {
    const alphabet = "abcdefghijklmnopqrstuvwxyz";
    expect(generatePassword(0, alphabet, 2)).toBe("aa");
    expect(generatePassword(1, alphabet, 2)).toBe("ab");
    expect(generatePassword(2, alphabet, 2)).toBe("ac");
    expect(generatePassword(25, alphabet, 2)).toBe("az");
    expect(generatePassword(26, alphabet, 2)).toBe("ba");
    expect(generatePassword(27, alphabet, 2)).toBe("bb");
  });

  it("should handle single character alphabet", () => {
    const alphabet = "a";
    expect(generatePassword(0, alphabet, 3)).toBe("aaa");
    expect(generatePassword(1, alphabet, 3)).toBe("aaa"); // Wraps around
  });


  it("should handle different password lengths", () => {
    const alphabet = "01";
    expect(generatePassword(0, alphabet, 1)).toBe("0");
    expect(generatePassword(1, alphabet, 1)).toBe("1");
    expect(generatePassword(0, alphabet, 4)).toBe("0000");
    expect(generatePassword(15, alphabet, 4)).toBe("1111");
  });

  it("should return empty string for empty alphabet", () => {
    expect(generatePassword(0, "", 5)).toBe("");
  });

  it("should return empty string for zero length", () => {
    expect(generatePassword(0, "abc", 0)).toBe("");
  });

  it("should handle large password numbers", () => {
    const alphabet = "abcdefghijklmnopqrstuvwxyz";
    const password = generatePassword(1000, alphabet, 3);
    expect(password).toHaveLength(3);
    // Verify it's a valid combination
    for (const char of password) {
      expect(alphabet).toContain(char);
    }
  });
});

describe("formatTime", () => {
  it("should format zero seconds correctly", () => {
    expect(formatTime(0)).toBe("00:00:00");
  });

  it("should format seconds less than 60", () => {
    expect(formatTime(30)).toBe("00:00:30");
    expect(formatTime(59)).toBe("00:00:59");
  });

  it("should format minutes correctly", () => {
    expect(formatTime(60)).toBe("00:01:00");
    expect(formatTime(90)).toBe("00:01:30");
    expect(formatTime(3599)).toBe("00:59:59");
  });

  it("should format hours correctly", () => {
    expect(formatTime(3600)).toBe("01:00:00");
    expect(formatTime(3661)).toBe("01:01:01");
    expect(formatTime(7323)).toBe("02:02:03");
  });

  it("should handle fractional seconds (floor them)", () => {
    expect(formatTime(30.7)).toBe("00:00:30");
    expect(formatTime(90.9)).toBe("00:01:30");
  });

  it("should handle large time values", () => {
    expect(formatTime(86400)).toBe("24:00:00");
    expect(formatTime(90061)).toBe("25:01:01");
  });

  it("should pad single digit values with zeros", () => {
    expect(formatTime(3661)).toBe("01:01:01");
    expect(formatTime(7323)).toBe("02:02:03");
  });
});

