# Testing Strategy

## Overview

This project uses **Vitest** as the testing framework, which integrates seamlessly with Vite and TypeScript. The testing strategy follows a bottom-up approach, starting with pure functions and gradually moving to more complex, DOM-dependent functions.

## Test Structure

### Phase 1: Pure Functions (Current)
✅ **Completed**
- `generatePassword()` - Password generation using base-N arithmetic
- `formatTime()` - Time formatting in HH:MM:SS format

These functions are:
- Pure (no side effects)
- Deterministic (same input = same output)
- Easy to test with unit tests
- Located in `src/utils.ts`

### Phase 2: DOM-Dependent Functions (Future)
Functions that interact with DOM elements will require:
- jsdom environment (already configured)
- Mock DOM elements
- State management testing

Examples:
- `updateAlphabet()` - Updates UI based on checkbox state
- `updateStats()` - Updates statistics display
- `stopGuessing()` / `resetGuessing()` - State management functions

### Phase 3: Async Functions (Future)
Functions that interact with external APIs:
- `tryDecrypt()` - GPG decryption (requires mocking openpgp)
- `startGuessing()` - Main orchestration function
- `guessingLoop()` - Animation frame loop

## Running Tests

### Local Development
```bash
# Run all tests once
make check

# Run tests in watch mode (auto-rerun on file changes)
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

### CI/CD
Tests automatically run on:
- Pull requests to `main`/`master`
- Pushes to `main`/`master`

Coverage is uploaded to Codecov automatically.

## Coverage Goals

- **Current**: Focus on pure functions (target: 100% coverage)
- **Future**: Expand to cover DOM interactions and async functions
- **Minimum**: 70% overall coverage (configured in `.codecov.yml`)

## Test File Naming

- Test files: `*.test.ts` (e.g., `utils.test.ts`)
- Located alongside source files in `src/`

## Writing New Tests

1. Create a test file: `src/your-module.test.ts`
2. Import functions to test
3. Use Vitest's `describe()` and `it()` blocks
4. Use `expect()` for assertions

Example:
```typescript
import { describe, it, expect } from "vitest";
import { yourFunction } from "./your-module";

describe("yourFunction", () => {
  it("should handle basic case", () => {
    expect(yourFunction(input)).toBe(expected);
  });
});
```

## CI Integration

### GitHub Actions
- Workflow: `.github/workflows/test.yml`
- Runs on: PRs and pushes to main/master
- Steps:
  1. Checkout code
  2. Setup Node.js (v20)
  3. Install dependencies (`npm ci`)
  4. Run tests with coverage
  5. Upload coverage to Codecov

### Codecov
- Configuration: `.codecov.yml`
- Reports: Coverage badges and PR comments
- Flags: `unittests` (for unit test coverage)

## Next Steps

1. ✅ Extract pure functions to `utils.ts`
2. ✅ Create tests for pure functions
3. ✅ Set up CI/CD pipeline
4. ⏳ Add tests for DOM-dependent functions (with mocks)
5. ⏳ Add tests for async functions (with mocks)
6. ⏳ Add integration tests for full workflow

