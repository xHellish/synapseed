# Example: Git Workflow Review & PR Template

## 1. Análisis de Flujo de Trabajo
El equipo necesita un flujo de trabajo ágil que permita integraciones continuas sin bloqueos, asegurando la calidad mediante revisiones de código estructuradas y versiones automatizadas.

## 2. Estrategia de Ramas
Recomendamos **Trunk-Based Development** combinado con **GitHub Flow**.
- Única rama principal: `main`.
- Ramas de características cortas: `feat/nombre-feature` o `fix/nombre-bug`.
- Prohibido el push directo a `main`. Todo debe pasar por un Pull Request (PR).

## 3. Convención de Commits
Usaremos **Conventional Commits**.
Ejemplos:
- `feat(auth): add google oauth login`
- `fix(ui): resolve button alignment on mobile`
- `chore(deps): update react to v18`

## 4. Pull Request Template

A continuación el contenido sugerido para `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
<!-- Describe the problem you are solving and the proposed solution. Include relevant context. -->

## Motivation and Context
<!-- Why is this change required? What problem does it solve? -->
<!-- If it fixes an open issue, please link to the issue here. (e.g., Fixes #123) -->

## Type of change
<!-- Check the relevant option: -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring / Technical Debt

## Testing Details
<!-- Please describe the tests that you ran to verify your changes. Provide instructions so we can reproduce. -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed (describe below)

## Checklist
- [ ] My code follows the style guidelines of this project.
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in hard-to-understand areas.
- [ ] I have made corresponding changes to the documentation.
- [ ] My commit messages follow Conventional Commits format.
- [ ] My changes generate no new warnings.
```

## 5. Automatización de Releases
Se configurará **Semantic Release** en el pipeline principal.
Al hacer merge a `main`, la acción analizará los commits nuevos. Si detecta un `feat`, creará automáticamente el tag `v1.x.x`, generará las release notes en GitHub, y actualizará el archivo `CHANGELOG.md`.
