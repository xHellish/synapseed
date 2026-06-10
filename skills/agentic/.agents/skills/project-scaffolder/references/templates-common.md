# Project Templates Reference

This document contains ready-to-use project templates with complete directory structures, configuration files, and development scripts.

> **⚠️ Versiones de dependencias**: Las versiones especificadas en este documento fueron verificadas en **2026-05-28**.
> Se recomienda revisar y actualizar las versiones trimestralmente o antes de iniciar un proyecto en producción.
> Usa `pip index versions <package>` (Python) o `npm show <package> version` (Node) para verificar la versión más reciente.

---

## Common Files (All Templates)

### `.editorconfig`

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

### `.gitignore` — Python

```gitignore
# Virtual environments
.venv/
venv/
env/

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Coverage
htmlcov/
.coverage
coverage.xml

# mypy
.mypy_cache/

# ruff
.ruff_cache/
```

### `.gitignore` — JavaScript/TypeScript

```gitignore
# Dependencies
node_modules/

# Build
dist/
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
.env.*.local

# Coverage
coverage/

# Logs
*.log
npm-debug.log*

# Cache
.eslintcache
.turbo/
```

### `.nvmrc`

```
22
```

### `.python-version`

```
3.12
```
