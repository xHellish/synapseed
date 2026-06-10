# Auth Patterns Reference — Security Auditor

> Complete reference for JWT, RBAC, OAuth2, and session security patterns.
> Used by the `security-auditor` skill when implementing or reviewing authentication systems.

---

## JWT Implementation (Python + FastAPI)

```python
# Python — secure JWT with FastAPI
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends

SECRET_KEY = settings.secret_key  # 32+ random bytes from secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, expected_type: str = "access") -> str:
    credentials_exception = HTTPException(status_code=401, detail="Invalid token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
        if payload.get("type") != expected_type:
            raise credentials_exception
        return subject
    except JWTError:
        raise credentials_exception
```

### JWT Security Checklist

- ✅ Use `timezone.utc` for all datetime operations (no naive datetimes)
- ✅ Include `type` claim to differentiate access vs refresh tokens
- ✅ Use `HS256` or `RS256` — never `none` or weak algorithms
- ✅ Secret key must be 32+ random bytes (`secrets.token_hex(32)`)
- ✅ Short expiry for access tokens (15-60 min), longer for refresh (7-30 days)
- ❌ Never store tokens in localStorage (XSS risk) — use httpOnly cookies
- ❌ Never log tokens or include them in error messages

---

## JWT Implementation (TypeScript + Express)

```typescript
import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';

const SECRET_KEY = process.env.JWT_SECRET!; // Must be set in environment
const ACCESS_EXPIRES = '30m';
const REFRESH_EXPIRES = '7d';

export function createAccessToken(userId: string): string {
  return jwt.sign(
    { sub: userId, type: 'access' },
    SECRET_KEY,
    { expiresIn: ACCESS_EXPIRES, algorithm: 'HS256' }
  );
}

export function verifyToken(token: string, expectedType: 'access' | 'refresh'): string {
  try {
    const payload = jwt.verify(token, SECRET_KEY) as jwt.JwtPayload;
    if (payload.type !== expectedType) {
      throw new Error('Invalid token type');
    }
    return payload.sub as string;
  } catch {
    throw new UnauthorizedError('Invalid or expired token');
  }
}

// Middleware
export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing authorization header' });
    return;
  }
  try {
    const token = header.slice(7);
    req.userId = verifyToken(token, 'access');
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

---

## RBAC (Role-Based Access Control) — Python

```python
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends

class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"

# Hierarchy: each role grants access to its own level AND all lower levels
# ROLE_HIERARCHY[user_role] = set of roles that user can act as
ROLE_HIERARCHY: dict[Role, set[Role]] = {
    Role.ADMIN:  {Role.ADMIN, Role.EDITOR, Role.VIEWER},
    Role.EDITOR: {Role.EDITOR, Role.VIEWER},
    Role.VIEWER: {Role.VIEWER},
}

def require_role(minimum_role: Role):
    """Decorator that enforces a minimum role requirement.
    
    Usage: @require_role(Role.ADMIN) means only admins can access.
    The check is: does the current user's role hierarchy include the minimum_role?
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            # ✅ Correct: check if minimum_role is in the SET OF ROLES the user CAN GRANT
            # Admin can grant {Admin, Editor, Viewer} — so Admin passes any minimum_role check
            # Viewer can grant {Viewer} — so Viewer fails Editor or Admin minimum_role checks
            if minimum_role not in ROLE_HIERARCHY[current_user.role]:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage examples:
@app.delete("/users/{user_id}")
@require_role(Role.ADMIN)   # Only admins
async def delete_user(user_id: str, current_user: User):
    await user_service.delete(user_id)

@app.put("/posts/{post_id}")
@require_role(Role.EDITOR)  # Editors and admins
async def update_post(post_id: str, current_user: User):
    ...
```

### RBAC Security Checklist

- ✅ Deny by default — require explicit `require_role` on every protected route
- ✅ Check authorization AFTER authentication (confirm identity, then check permissions)
- ✅ Use role hierarchy to avoid duplicating checks
- ✅ Log authorization failures for security monitoring
- ❌ Never trust role claims from client-side (JWT claims only, validated server-side)
- ❌ Avoid flat permission lists — prefer hierarchical roles

---

## OAuth2 with PKCE (Recommended for SPAs)

```typescript
// Frontend — Authorization Code + PKCE flow
async function initiateOAuthLogin(provider: 'google' | 'github'): Promise<void> {
  const codeVerifier = generateCodeVerifier(); // 43-128 random chars
  const codeChallenge = await generateCodeChallenge(codeVerifier); // SHA256 + base64url
  
  sessionStorage.setItem('pkce_verifier', codeVerifier);
  
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: 'openid profile email',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    state: generateState(), // CSRF protection
  });
  
  window.location.href = `${PROVIDER_AUTH_URL}?${params}`;
}

function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}
```

---

## Session Security

```python
# FastAPI + secure session configuration
from fastapi.middleware.sessions import SessionMiddleware
import secrets

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,     # 32+ random bytes
    session_cookie="session",
    max_age=1800,                         # 30 minutes
    same_site="lax",                      # CSRF protection
    https_only=True,                      # Force HTTPS
    httponly=True,                        # Prevent JS access (XSS protection)
)
```

### Session Security Checklist

- ✅ `httponly=True` — prevent JavaScript access (XSS protection)
- ✅ `secure=True` / `https_only=True` — only send over HTTPS
- ✅ `same_site="lax"` or `"strict"` — CSRF protection
- ✅ Rotate session ID after login (session fixation prevention)
- ✅ Invalidate server-side session on logout
- ❌ Never store sensitive data in client-side cookies
- ❌ Avoid `same_site="none"` unless required for cross-origin use cases
