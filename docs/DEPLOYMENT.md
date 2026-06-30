# Production Deployment Guide

## Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Termux

```bash
pkg update -y
pkg install python git rust clang make pkg-config llvm lld -y
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

```bash
docker build -t niveshsetu-ai .
docker run -p 8000:8000 niveshsetu-ai
```

## Cloud Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Bank Production Hardening Checklist

- Replace synthetic data with anonymized/sandbox IDBI APIs.
- Add OAuth/OIDC, RBAC, API gateway throttling, and WAF rules.
- Add encryption-at-rest and secret management.
- Send audit events to SIEM/log lake.
- Run vulnerability assessment and penetration testing.
- Run independent model validation and documented MRM approval.
- Use approved product shelf only after legal/compliance review.
- Add consent ledger and customer grievance workflow.
