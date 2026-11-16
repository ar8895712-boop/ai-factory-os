# Contributing to AI Factory Operating System

Thank you for your interest in contributing to **AI Factory OS**! We welcome bug reports, pull requests, and suggestions to enhance our predictive maintenance digital-twin platform.

---

## 1. Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please treat others with respect and professionalism.

---

## 2. Development Setup

1. **Fork & Clone** the repository:
   ```bash
   git clone https://github.com/your-username/ai-factory-os.git
   cd ai-factory-os
   ```

2. **Backend Setup**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python scripts/seed_db.py
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Run the Test Suite**:
   ```bash
   pytest tests/ -v
   ```

---

## 3. Pull Request Guidelines

- **Branch Naming**: Use descriptive prefixes:
  - `feature/add-feature-name`
  - `fix/resolve-issue-name`
  - `docs/update-readme`
- **Conventional Commits**: Format your commits clearly:
  - `feat: add vibration spectrogram anomaly detector`
  - `fix: resolve division by zero in health score calculation`
  - `docs: update API schema for simulation endpoints`
- **Verification**: Ensure all 79 tests pass with `pytest tests/` and frontend builds cleanly with `npm run build` before opening a pull request.
- **Scope & Safety**: Never commit secrets, `.env` files, or binary model checkpoints directly to Git.

---

## 4. Reporting Issues

When filing an issue, please include:
- A clear, concise title.
- Steps to reproduce the behavior.
- Expected vs. actual behavior.
- OS, Python, and Node versions.
