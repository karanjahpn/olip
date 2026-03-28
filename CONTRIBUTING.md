# Contributing to OLIP

First off — thank you! OLIP is an open protocol and gets better with every contributor. This guide will get you from zero to your first pull request.

---

## What We Need Most

Check the [Issues](https://github.com/karanjahpn/olip/issues) tab for open tasks. The highest priority areas are:

### 🔴 P0 — Critical (Core Protocol)
- **Secure Enclave binding** — iOS `SecureEnclave` and Android `StrongBox` / Keystore integration so the Root Identity Key never leaves hardware
- **Shard transport layer** — encrypted delivery of shards to guardians via Matrix, Signal API, or Bluetooth/NFC
- **Biometric step-up** — replace the `print()` stub in `AdaptiveTrustEngine._trigger_step_up_auth()` with real platform biometric APIs

### 🟡 P1 — Important
- **Tamper-proof audit log** — append-only local event log signed with device key
- **Real behavioral sensors** — wire `BehavioralSignals` to typing dynamics, GPS geofencing, IMU data
- **Push notifications** — APNs / FCM integration for guardian alerts with critical alert bypass

### 🟢 P2 — Good First Issues
- Improve test coverage (aim for 100%)
- Add type hints throughout
- Write the Swift or Kotlin bridge for mobile
- Generate the Emergency Recovery Sheet PDF
- Add GitHub Actions CI workflow

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/olip.git
cd olip
```

### 2. Install Dependencies

```bash
pip install -e ".[dev]"
```

Requirements: **Python 3.11+**. No third-party dependencies for the core protocol.

### 3. Run the Tests

```bash
pytest tests/ -v
```

All tests must pass before submitting a PR.

### 4. Run the Demo

```bash
python scripts/demo.py
```

---

## How to Contribute

### Reporting Bugs
- Open an [Issue](https://github.com/karanjahpn/olip/issues)
- Include: what you expected, what happened, your Python version, and steps to reproduce

### Suggesting Features
- Open an Issue with the `enhancement` label
- For significant changes, discuss the approach first before writing code

### Submitting a Pull Request
1. Create a branch: `git checkout -b feat/your-feature-name`
2. Make your changes
3. Add or update tests for your changes
4. Run `pytest tests/ -v` and confirm all pass
5. Commit with a clear message: `git commit -m "feat: add Matrix shard transport"`
6. Push and open a PR against `main`

### Commit Message Format
We use simple conventional commits:
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding or updating tests
- `refactor:` — code change that neither fixes a bug nor adds a feature

---

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Add docstrings to all public functions and classes
- Mark stubs clearly with `# STUB:` comments and a note in the docstring
- Keep the core protocol (`olip/`) dependency-free — no third-party imports

---

## Security Vulnerabilities

**Please do not open a public Issue for security vulnerabilities.**
Instead, email the maintainer directly (add your contact in the README) so it can be patched before public disclosure.

---

## Code of Conduct

Be kind. Be constructive. We're all here to build something useful.

- Critique code, not people
- Welcome newcomers — everyone starts somewhere
- If you're stuck, open an Issue and ask

---

## Questions?

Open a [Discussion](https://github.com/karanjahpn/olip/discussions) or an Issue tagged `question`. We're happy to help.
