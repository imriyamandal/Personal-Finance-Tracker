# Contributing to Personal Finance Tracker

Thank you for your interest in contributing! We welcome contributions from developers of all skill levels to make this project the best personal financial tracking platform available.

To maintain high code quality, security, and performance, please follow these guidelines when contributing.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Development Setup](#development-setup)
- [Style Guide & Coding Standards](#style-guide--coding-standards)
- [Testing Requirements](#testing-requirements)
- [Security Disclosures](#security-disclosures)

---

## Code of Conduct

By participating in this project, you agree to uphold our commitment to an inclusive, welcoming, and harassment-free environment. Please treat all contributors with respect.

---

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please check the [GitHub Issues](https://github.com/imriyamandal/Personal-Finance-Tracker/issues) first to see if it has already been reported. If not, open a new issue using our **Bug Report** template and include:
* A clear, descriptive title.
* Steps to reproduce the issue.
* Expected vs. actual behavior.
* Screenshots, error logs, or stack traces if available.
* Your operating system, Python version, and browser (for UI bugs).

### Suggesting Enhancements

We are always looking for ways to improve the user experience, machine learning performance, or API efficiency. To suggest an enhancement, create an issue using the **Feature Request** template, outlining:
* The core problem you want to solve.
* A detailed explanation of your proposed solution or feature.
* Mockups, design considerations, or reference implementations where applicable.

### Submitting Pull Requests

1. **Fork** the repository and create your branch from `main`.
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/your-bugfix-name
   ```
2. **Commit** your changes with clear, descriptive commit messages matching the project style (e.g. `feat: add email alert threshold for monthly budgets`).
3. **Write Tests** for any new functionality you introduce, and run existing tests to verify nothing has broken.
4. **Push** your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** against the `main` branch of this repository using our **Pull Request Template**.

---

## Development Setup

For detailed instructions on running and debugging the application, see the [Getting Started](README.md#getting-started) section of the README.

### Backend Setup
* Ensure you are running Python 3.12.
* Use a virtual environment (`venv` or `conda` recommended).
* Install dependencies via `pip install -r requirements.txt`.

### Frontend Setup
* Ensure Node.js (v18+) is installed.
* Run `npm install` inside the `frontend` folder.
* Run `npm run dev` to start the local Vite development server.

---

## Style Guide & Coding Standards

### Python (Backend & ML)
* **PEP 8**: Follow PEP 8 guidelines.
* **Typing**: Use type hints in new function declarations where appropriate.
* **Docstrings**: Document classes, methods, and API routes using Google-style docstrings.
* **Unused Code**: Remove all print debug statements; use loggers (or FastAPI standard logging) if needed.

### React & JS (Frontend)
* **Components**: Organize code into modular components within `frontend/src/components/`.
* **State**: Keep states clean and local where possible.
* **Styling**: Write modular, clean CSS inside `frontend/src/index.css` or specific component stylesheet overrides. Do not use ad-hoc styles unless absolutely necessary.

---

## Testing Requirements

We prioritize stability. No pull request will be merged without passing all checks.

### Running Backend Tests
Ensure the API test suite passes successfully before opening a PR:
```bash
pytest backend/tests/test_api.py
```

### Coverage
If you introduce a new feature or change an existing REST endpoint, make sure to add corresponding unit tests inside `backend/tests/test_api.py`.

---

## Security Disclosures

If you discover a security vulnerability (such as SQL injection, CSRF, or sensitive environment variable exposure), please **do not** open a public issue. Instead, email the repository owner privately at `riya.mandal@example.com` (placeholder) to allow for responsible disclosure and mitigation.
