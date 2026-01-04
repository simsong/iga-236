This is a single-page HTML application for GPG password guessing/brute-forcing.

The application allows users to:
- Configure character sets (lowercase, uppercase, symbols, digits)
- Set password length (1-8 characters)
- Automatically generate and test passwords against a GPG-encrypted message
- View real-time statistics (guesses per second, elapsed time, estimated completion time)

## Development

### Setup
```bash
make install
```

### Run Development Server
```bash
make dev
```

### Build
```bash
make build
```

## Testing

### Run Tests
```bash
make check
# or
npm run test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run Tests with Coverage
```bash
npm run test:coverage
# or
make test-coverage
```

### Test Strategy

The test suite focuses on testing pure, non-async functions first:
- `generatePassword()` - Tests password generation using base-N arithmetic
- `formatTime()` - Tests time formatting in HH:MM:SS format

Future tests will cover async functions and DOM interactions using mocks.

## CI/CD

Tests run automatically on pull requests via GitHub Actions. Coverage reports are uploaded to Codecov.

### Local Testing
Run `make check` to execute all tests locally before committing.
