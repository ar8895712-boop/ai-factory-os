## 📌 Pull Request Overview

### Description
<!-- Provide a clear, brief summary of what this PR introduces or fixes. -->

### Type of Change
- [ ] `feat`: A new user-facing feature or API endpoint
- [ ] `fix`: A bug fix
- [ ] `docs`: Documentation updates or markdown corrections
- [ ] `style`: Formatting, missing semi-colons, style changes
- [ ] `refactor`: Code reorganization with no behavior changes
- [ ] `perf`: A code change that improves performance or latency
- [ ] `test`: Adding missing unit, integration, or E2E tests
- [ ] `chore`: Build tasks, package updates, DevOps manifests

---

## 🔬 Subsystems Affected
- [ ] Frontend (React 18 / Vite / Tailwind UI)
- [ ] Backend REST / WebSocket APIs (FastAPI)
- [ ] Machine Learning Core (PyTorch / XGBoost / TreeSHAP)
- [ ] Simulation Engine (SimPy / Digital Twin Replay)
- [ ] Database / ORM Models (SQLAlchemy / Neon / SQLite)
- [ ] DevOps & Deployment (Docker / GitHub Actions / Vercel / Render)

---

## 🧪 Verification & Evidence

### Test Execution
```text
# Paste test output here: e.g., pytest tests/
```

### Visual / Functional Verification
<!-- Attach screenshot or GIF if modifying frontend components or charts -->

---

## ✅ Pre-Merge Security & Quality Checklist
- [ ] No secrets, real API keys, or private database passwords are included in code or commits.
- [ ] `.env` and `config.yaml` are NOT committed (`.env.example` and `config.example.yaml` updated if new variables were added).
- [ ] No heavy binary files (`*.pt`, `*.pkl`, raw datasets) added directly to Git.
- [ ] All 79 automated tests pass cleanly with `pytest tests/`.
- [ ] Frontend builds with zero errors: `npm run build` inside `/frontend`.
- [ ] Commit history follows Conventional Commits format (`type(scope): subject`).
