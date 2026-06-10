# Agentic Workspace — Consideraciones

## Propósito

Este workspace es un entorno agéntico diseñado para asistir en el diseño, análisis y mejora de proyectos de software. Contiene un conjunto de **Agent Skills** reutilizables que se activan según el contexto de la conversación. La fuente de verdad de triggers y metadatos es `.agents/manifest.json`.

## Skills Disponibles

| Skill | Descripción | Triggers principales |
|-------|-------------|----------------------|
| `software-architect` | Diseño de arquitectura, diagramas C4, ADRs | "diseñar sistema", "arquitectura", "diagrama" |
| `structure-analyzer` | Análisis de estructura de proyectos existentes | "analizar estructura", "mapa de dependencias" |
| `code-improver` | Detección de code smells y refactoring | "mejorar código", "refactorizar", "code review" |
| `project-scaffolder` | Scaffolding de proyectos nuevos | "crear proyecto", "inicializar", "setup" |
| `test-strategist` | Estrategia de testing, anti-patrones, cobertura | "escribir tests", "TDD", "cobertura" |
| `security-auditor` | Auditoría de seguridad OWASP, secretos, supply chain | "auditar seguridad", "vulnerabilidades", "OWASP" |
| `docs-generator` | Generación de documentación técnica y runbooks | "generar documentación", "API docs", "runbook" |

> Para la lista completa de triggers, consultar `.agents/manifest.json`.

## Convenciones

### Idioma
- Las instrucciones de las skills están en **inglés** (mejor procesamiento por los modelos)
- Las **respuestas siempre deben ser en español**

### Versionado
- Todas las skills usan versionado semántico (`MAJOR.MINOR.PATCH`) en su frontmatter YAML
- Los cambios se registran en `.agents/CHANGELOG.md`

### Estructura de Archivos

```
Agentic Workspace/
├── .agents/
│   ├── manifest.json              # Catálogo central de skills (fuente de verdad)
│   ├── CHANGELOG.md               # Historial de cambios del workspace
│   ├── scripts/
│   │   └── validate_skills.py     # Validador de integridad de skills
│   └── skills/
│       ├── _template-skill/       # Plantilla para nuevas skills
│       ├── software-architect/    # Diseño de software
│       ├── structure-analyzer/    # Análisis de estructura
│       ├── code-improver/         # Mejoras de código
│       ├── project-scaffolder/    # Scaffolding de proyectos
│       ├── test-strategist/       # Testing y QA
│       ├── security-auditor/      # Auditoría de seguridad
│       └── docs-generator/        # Generación de documentación
├── .clinerules                    # Regla de activación de skills
├── .markdownlint.json             # Configuración de linter de Markdown
├── Consideraciones.md             # Este archivo
├── mejoras_actuales.md            # Backlog de mejoras pendientes
└── README.md                      # Documentación principal del workspace
```

### Lenguajes Soportados

| Lenguaje | Skills |
|----------|--------|
| Python | Todas |
| JavaScript / TypeScript | Todas |
| Go | `software-architect`, `structure-analyzer`, `code-improver`, `project-scaffolder` |
| Java | `software-architect`, `structure-analyzer`, `code-improver`, `project-scaffolder` |
| Rust | `project-scaffolder` |

### Patrones de Diseño

No hay preferencia fija — se adaptan según el proyecto. Las skills están preparadas para recomendar el patrón más adecuado según el contexto. Ver `software-architect/references/design-patterns.md`.

## Uso

Para activar una skill, simplemente describe lo que necesitas. El agente detectará automáticamente cuál skill es relevante consultando los `triggers` en `manifest.json`.

**Ejemplos:**
- *"Quiero diseñar una API REST para gestión de usuarios"* → `software-architect`
- *"Analiza la estructura de este proyecto"* → `structure-analyzer`
- *"Revisa este código y sugiere mejoras"* → `code-improver`
- *"Crea un nuevo proyecto con FastAPI"* → `project-scaffolder`
- *"Escribe los tests para este módulo"* → `test-strategist`
- *"Audita la seguridad de esta API"* → `security-auditor`
- *"Genera la documentación de esta librería"* → `docs-generator`

## Prompts de Activación Avanzada

1. **Structure Analyzer**: "Por favor, activa tu skill de Structure Analyzer para mapear este repositorio. Analiza la organización de carpetas actual, contrástala con tus mejores prácticas en project-patterns.md y genérame un reporte técnico detallado con las fallas de convención de nombres o acoplamientos que encuentres."

2. **Software Architect**: "Necesito definir la estructura para un nuevo módulo de [ej: pagos]. Invoca tu skill de Software Architect para traducir estos requisitos a componentes de software. Proponme los patrones de diseño adecuados basándote en tu guía de design-patterns.md y crea los contratos de las APIs."

3. **Code Improver**: "Revisa el archivo [ruta/del/archivo]. Usa tu skill de Code Improver para detectar vulnerabilidades, anti-patrones o problemas de complejidad ciclomática apoyándote en tu catálogo de code-smells.md. Haz los cambios necesarios de forma automática."

4. **Project Scaffolder**: "Voy a iniciar un nuevo microservicio de [ej: Python/FastAPI]. Activa tu skill de Project Scaffolder y genera la estructura base de directorios siguiendo tus project-templates.md. Configura también el linter, el formateador y déjame el archivo README listo."

5. **Test Strategist**: "Revisa el módulo [ruta/del/módulo] y activa tu skill de Test Strategist. Define la estrategia de testing apropiada, detecta anti-patrones en los tests existentes y genera tests para los casos no cubiertos usando los patrones de testing-patterns.md."

6. **Security Auditor**: "Realiza una auditoría de seguridad de [ruta/del/código]. Activa tu skill de Security Auditor y verifica los puntos del OWASP Top 10 de owasp-checklist.md que apliquen. Identifica vulnerabilidades y proporciona código de remediación."

7. **Docs Generator**: "Genera la documentación técnica para [proyecto/módulo]. Activa tu skill de Docs Generator y crea: docstrings para las funciones públicas, un README actualizado y configura MkDocs/TypeDoc para documentación automática."

## Flujo Autónomo Nocturno (Comando `/goal`)

El workspace está optimizado para tareas de larga duración (por ejemplo, dejar al agente trabajando toda la noche diseñando, validando y testeando código). Para esto se utiliza el comando especial **`/goal`**.

### ¿Qué hace `/goal`?
- **Autonomía total:** El agente no hace pausas para pedir confirmaciones en cada paso. Asume que estás ausente.
- **Bucle de Auto-Corrección:** Si el agente escribe código, intentará ejecutar los tests. Si fallan, leerá los errores en la terminal y se auto-corregirá en un bucle continuo hasta que todo pase en verde.
- **Multitarea:** El agente puede invocar *subagentes* para avanzar en múltiples frentes en paralelo.

### Flujo Ideal (Fire-and-Forget)

Para asegurar resultados óptimos sin supervisión:

1. **La Especificación (Previa):** Pide a la skill `software-architect` que genere un documento con el diseño detallado (ej. `especificacion.md`) mientras estás presente para revisarlo.
2. **Permisos de Terminal:** Asegúrate de conceder permisos de ejecución en la terminal antes de irte a dormir, para que el agente no se quede bloqueado esperando tu "Y" (Yes).
3. **El Prompt Definitivo:**
   > **`/goal`** Lee el archivo `especificacion.md`. Activa `project-scaffolder` para crear la base. Implementa toda la lógica. Luego, usa `test-strategist` para asegurar 100% de cobertura. Si un test falla, arréglalo. No te detengas hasta que toda la suite de pruebas esté pasando y el `README.md` generado con `docs-generator`.

## Mantenimiento

```bash
# Validar integridad de todas las skills
python .agents/scripts/validate_skills.py

# Linting de Markdown
npx markdownlint-cli "**/*.md" --config .markdownlint.json
```
