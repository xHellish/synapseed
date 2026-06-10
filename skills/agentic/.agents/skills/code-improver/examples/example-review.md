# Ejemplo de Output — Code Improver

> Este archivo muestra una revisión de código típica generada por la skill `code-improver`.

---

## Resumen

El módulo `user_service.py` presenta calidad general **Media-Baja**. Se identificaron 4 problemas, incluyendo 1 crítico (almacenamiento inseguro de contraseñas) y 1 alto (método demasiado largo que viola SRP).

## Scorecard

| Aspecto | Puntuación | Notas |
|---------|------------|-------|
| Legibilidad | ⭐⭐⭐ | Nombres claros, pero métodos largos |
| Mantenibilidad | ⭐⭐ | Violación de SRP en `create_user` |
| Rendimiento | ⭐⭐⭐⭐ | Sin problemas significativos |
| Testabilidad | ⭐⭐ | Dependencias hardcodeadas dificultan mocks |
| Seguridad | ⭐ | Contraseñas almacenadas sin hash |

## Hallazgos

### 🔴 CRÍTICO — Almacenamiento Inseguro de Contraseñas

**Ubicación**: `user_service.py`, línea 23

**Por qué es un problema**: Las contraseñas se almacenan en texto plano en la base de datos. Una brecha de datos expone todas las credenciales de todos los usuarios.

**Antes:**
```python
def create_user(self, email: str, password: str) -> User:
    user = User(email=email, password=password)  # ❌ Texto plano!
    self.repo.save(user)
    return user
```

**Después:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(self, email: str, password: str) -> User:
    hashed = pwd_context.hash(password)  # ✅ Hash seguro
    user = User(email=email, password_hash=hashed)
    self.repo.save(user)
    return user
```

## Quick Wins

1. Añadir type hints a todos los métodos públicos
2. Reemplazar `print()` con `logger.info()`
3. Usar `@dataclass` para `UserConfig` en lugar de constructor con 6 parámetros
