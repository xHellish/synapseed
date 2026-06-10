# OWASP Top 10 — Security Checklist

Lista de verificación práctica basada en OWASP Top 10 (2021). Para cada riesgo: descripción, cómo detectarlo, y cómo mitigarlo.

---

## A01:2021 — Broken Access Control

**Descripción**: Los usuarios pueden actuar fuera de sus permisos previstos.

### Checklist
- [ ] ¿Cada endpoint verifica que el usuario autenticado tiene permiso para ese recurso?
- [ ] ¿Los IDs de recursos son opacos (UUIDs) y no secuenciales?
- [ ] ¿La lógica de acceso está centralizada (no duplicada en cada controlador)?
- [ ] ¿Los roles y permisos están definidos explícitamente (no por defecto permisivos)?
- [ ] ¿Los endpoints de administración están protegidos con roles adicionales?
- [ ] ¿Se registran (log) los intentos de acceso no autorizado?

### Red Flags
- Acceder a `/api/users/123` siendo el usuario 456 y obtener datos
- Parámetros como `?admin=true` que elevan privilegios
- Rutas de admin accesibles sin autenticación especial
- IDs numéricos secuenciales expuestos en URLs (`/orders/1`, `/orders/2`...)

### Mitigación
```python
# FastAPI — dependency de autorización reutilizable
def get_resource_or_403(resource_id: str, current_user: User = Depends(get_current_user)):
    resource = db.get(resource_id)
    if resource is None:
        raise HTTPException(404)
    if resource.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Access forbidden")
    return resource
```

---

## A02:2021 — Cryptographic Failures

**Descripción**: Datos sensibles expuestos por cifrado débil o ausente.

### Checklist
- [ ] ¿Las contraseñas usan bcrypt, scrypt, o Argon2 (NOT MD5/SHA1)?
- [ ] ¿Los datos sensibles en tránsito usan TLS 1.2+ (HTTPS obligatorio)?
- [ ] ¿Los datos sensibles en reposo están cifrados?
- [ ] ¿Las claves de cifrado se rotan periódicamente?
- [ ] ¿Los tokens JWT usan RS256 o HS256 con claves fuertes (≥256 bits)?
- [ ] ¿No hay datos sensibles en logs, URLs, o respuestas de error?

### Red Flags
- `hashlib.md5()` o `hashlib.sha1()` para contraseñas
- Datos de tarjetas, SSNs, o contraseñas en texto plano en BD
- HTTP (no HTTPS) en producción
- Cookies sin flags `Secure` y `HttpOnly`

### Mitigación
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

## A03:2021 — Injection

**Descripción**: Datos hostiles enviados a un intérprete (SQL, NoSQL, OS, LDAP).

### Checklist
- [ ] ¿Todas las queries a BD usan parámetros o ORMs (NO interpolación de strings)?
- [ ] ¿Los comandos de sistema operativo validan/escapan sus argumentos?
- [ ] ¿Las búsquedas en LDAP sanitizan el input?
- [ ] ¿Los templates no ejecutan código arbitrario del usuario (SSTI)?
- [ ] ¿Hay validación de tipos en el input antes de procesarlo?

### Red Flags
```python
# ❌ SQL Injection
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ❌ Command Injection
os.system(f"convert {filename} output.pdf")

# ❌ Template Injection (Jinja2)
template = Template(user_input)  # User controls template!
```

### Mitigación
```python
# ✅ Parametrized SQL
stmt = select(User).where(User.name == user_input)  # SQLAlchemy ORM

# ✅ Safe subprocess
import subprocess, shlex
subprocess.run(["convert", filename, "output.pdf"], check=True)  # List, not string

# ✅ Input validation with Pydantic
class SearchQuery(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9 ]+$')
```

---

## A04:2021 — Insecure Design

**Descripción**: Ausencia de patrones de diseño seguros desde el inicio.

### Checklist
- [ ] ¿Existe rate limiting en endpoints de autenticación?
- [ ] ¿Hay límites en el tamaño de uploads y requests?
- [ ] ¿Las funciones de negocio tienen casos de abuso documentados?
- [ ] ¿El diseño asume zero trust (no confiar en redes internas)?
- [ ] ¿Hay protección contra timing attacks en comparaciones de tokens?

### Mitigación
```python
# Rate limiting con slowapi (FastAPI)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 intentos por minuto por IP
async def login(request: Request, credentials: LoginRequest):
    ...

# Constant-time comparison para tokens (evitar timing attacks)
import hmac
def verify_api_key(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided.encode(), expected.encode())
```

---

## A05:2021 — Security Misconfiguration

**Descripción**: Configuraciones inseguras por defecto o incompletas.

### Checklist
- [ ] ¿Los mensajes de error no exponen stack traces en producción?
- [ ] ¿Los headers de seguridad HTTP están configurados?
- [ ] ¿Los puertos y servicios innecesarios están deshabilitados?
- [ ] ¿Las credenciales por defecto (admin/admin) están cambiadas?
- [ ] ¿El modo debug está desactivado en producción?
- [ ] ¿Los archivos de configuración con secretos no están en el repositorio?

### Red Flags
```python
# ❌ Debug mode en producción
app.run(debug=True)  # Expone Werkzeug debugger y tracebacks

# ❌ Errores detallados al cliente
@app.exception_handler(Exception)
async def generic_handler(request, exc):
    return JSONResponse({"error": str(exc), "traceback": traceback.format_exc()})
```

### Mitigación
```python
# ✅ Errores genéricos en producción
@app.exception_handler(Exception)
async def generic_handler(request, exc):
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse({"error": "Internal server error"}, status_code=500)

# ✅ Configuración por entorno
class Settings(BaseSettings):
    debug: bool = False  # Default False — require explicit opt-in
    show_docs: bool = False
```

---

## A06:2021 — Vulnerable and Outdated Components

**Descripción**: Uso de componentes con CVEs conocidos.

### Checklist
- [ ] ¿Se hace `pip-audit` o `npm audit` regularmente?
- [ ] ¿Las versiones de dependencias están fijadas (pinned)?
- [ ] ¿Hay alertas de Dependabot o Renovate configuradas?
- [ ] ¿Se actualiza el OS base de los contenedores Docker?
- [ ] ¿Las imágenes Docker usan imágenes oficiales y recientes?

### Comandos
```bash
# Python
pip-audit                          # Escanea paquetes instalados
pip-audit -r requirements.txt      # Desde archivo

# Node
npm audit                          # Reporte de vulnerabilidades
npm audit fix                      # Corrige automáticamente las seguras
npm outdated                       # Ver paquetes desactualizados

# Docker
docker scout cves image:tag        # Escanear imagen
trivy image myapp:latest           # Alternativa con Trivy
```

---

## A07:2021 — Identification and Authentication Failures

**Descripción**: Debilidades en autenticación e identificación de usuarios.

### Checklist
- [ ] ¿Hay protección contra brute force (rate limiting + lockout)?
- [ ] ¿Los tokens de sesión son suficientemente aleatorios (≥128 bits)?
- [ ] ¿Los tokens se invalidan en logout?
- [ ] ¿Los tokens de reset de contraseña expiran rápido (15min)?
- [ ] ¿Se usa MFA para cuentas privilegiadas?
- [ ] ¿Las contraseñas tienen requisitos mínimos (longitud ≥12)?

### Mitigación
```python
# JWT con expiración corta + refresh tokens
def create_tokens(user_id: str) -> dict:
    access_token = create_jwt(user_id, expires_in=timedelta(minutes=15))
    refresh_token = create_jwt(user_id, expires_in=timedelta(days=7), type="refresh")
    return {"access_token": access_token, "refresh_token": refresh_token}

# Invalidar tokens en logout (blacklist con Redis)
async def logout(token: str, redis: Redis):
    await redis.setex(f"blacklist:{token}", 3600, "1")

async def is_token_valid(token: str, redis: Redis) -> bool:
    return not await redis.exists(f"blacklist:{token}")
```

---

## A08:2021 — Software and Data Integrity Failures

**Descripción**: Código o datos que no verifican integridad (deserialization, CI/CD inseguro).

### Checklist
- [ ] ¿Los webhooks verifican firmas (HMAC)?
- [ ] ¿Los paquetes se instalan desde registros oficiales?
- [ ] ¿El pipeline de CI/CD usa actions/dependencias con versiones fijas (hash)?
- [ ] ¿Los archivos descargados tienen checksums verificados?
- [ ] ¿No se usa `pickle` para deserializar datos no confiables?

### Mitigación
```python
# Verificar firma de webhook (GitHub, Stripe, etc.)
import hmac, hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## A09:2021 — Security Logging and Monitoring Failures

**Descripción**: Sin logging adecuado, los ataques no se detectan.

### Checklist
- [ ] ¿Se registran los intentos de login fallidos?
- [ ] ¿Se registran los accesos no autorizados (403)?
- [ ] ¿Los logs NO contienen contraseñas, tokens, o datos sensibles?
- [ ] ¿Hay alertas configuradas para anomalías (N fallos en X minutos)?
- [ ] ¿Los logs tienen timestamps, IP de origen, y user ID?
- [ ] ¿Los logs son resistentes a tampering (inmutables en producción)?

### Mitigación
```python
import structlog

logger = structlog.get_logger()

# Log de eventos de seguridad (sin datos sensibles)
async def login(credentials: LoginRequest, request: Request):
    try:
        user = await auth_service.authenticate(credentials.email, credentials.password)
        logger.info("login_success", user_id=user.id, ip=request.client.host)
        return create_tokens(user.id)
    except InvalidCredentialsError:
        logger.warning("login_failed", email=credentials.email, ip=request.client.host)
        raise HTTPException(401, "Invalid credentials")
    # ⚠️ No loguear la contraseña, nunca
```

---

## A10:2021 — Server-Side Request Forgery (SSRF)

**Descripción**: La aplicación acepta URLs de usuarios y hace requests a destinos no previstos.

### Checklist
- [ ] ¿Las URLs proporcionadas por usuarios se validan contra una allowlist?
- [ ] ¿Los requests salientes tienen timeouts configurados?
- [ ] ¿Se bloquea el acceso a rangos de IP internos (169.254.x.x, 10.x.x.x, 127.x.x.x)?
- [ ] ¿Las respuestas de URLs externas no se sirven directamente al cliente?

### Mitigación
```python
import ipaddress
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"api.example.com", "cdn.example.com"}

def validate_external_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP/HTTPS allowed")
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain not in allowlist: {parsed.hostname}")
    # Block internal IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Internal IPs not allowed")
    except ValueError:
        pass  # It's a hostname, not IP — OK if in allowlist
    return url
```

---

## Security CI/CD Pipeline

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 8 * * 1'  # Weekly on Mondays

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/gh-action-pip-audit@v1.1.0  # Python
      # OR for Node:
      # - run: npm audit --audit-level=high

  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python  # or javascript, typescript
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3

  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:latest
          severity: HIGH,CRITICAL
          exit-code: '1'
```
