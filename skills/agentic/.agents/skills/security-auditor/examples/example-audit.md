# Ejemplo de Output — Security Auditor

> Auditoría de seguridad del endpoint `/api/auth`.

---

## Resumen de Riesgo

**Nivel global: 🔴 CRÍTICO** — 2 vulnerabilidades críticas, 1 alta.

## Vulnerabilidades Encontradas

### 🔴 CRÍTICO — A02: Contraseñas en MD5

**Archivo**: `auth_service.py`, línea 34

```python
# ❌ Vulnerable
hashed = hashlib.md5(password.encode()).hexdigest()

# ✅ Remediación
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)
hashed = pwd_context.hash(password)
```

### 🔴 CRÍTICO — A03: SQL Injection

**Archivo**: `user_repo.py`, línea 67

```python
# ❌ Vulnerable
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ Remediación
stmt = select(User).where(User.email == email)  # ORM
```

## CI/CD de Seguridad Recomendado

```yaml
# .github/workflows/security.yml
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: pypa/gh-action-pip-audit@v1.1.0
      - uses: gitleaks/gitleaks-action@v2
```
