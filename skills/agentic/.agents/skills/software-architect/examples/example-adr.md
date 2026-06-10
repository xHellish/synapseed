# Ejemplo de Output — Software Architect (ADR)

> Este archivo muestra un ADR típico generado por la skill `software-architect`.

---

# ADR-001: Usar PostgreSQL como Base de Datos Principal

## Metadata

| Campo | Valor |
|-------|-------|
| **Status** | `Accepted` |
| **Date** | 2026-05-28 |
| **Review date** | 2027-05-28 |
| **Tags** | `data`, `infra` |
| **Participants** | @architect, @backend-lead, @devops |
| **Implementation** | PR #42 |

---

## Context

Necesitamos elegir una base de datos para el servicio de órdenes. Los requisitos son:
- Transacciones ACID (crítico para operaciones financieras)
- Soporte para queries complejas con JOINs
- Equipo con experiencia en SQL
- Necesidad de escalabilidad vertical a corto plazo

## Decision

Usaremos **PostgreSQL 16** como base de datos principal, accedida a través de SQLAlchemy 2.0 con Alembic para migraciones.

## Consequences

### Positivo
- ACID completo — transacciones seguras para operaciones de pago
- Soporte nativo para JSON/JSONB — flexibilidad para datos semi-estructurados
- El equipo ya tiene experiencia, curva de aprendizaje mínima

### Negativo
- Escalabilidad horizontal más compleja que MongoDB
- Requiere gestión de migraciones (Alembic)

## Alternativas Consideradas

### MongoDB
- **Pros**: Esquema flexible, escalado horizontal nativo
- **Por qué rechazado**: Falta de transacciones ACID completas; datos financieros requieren consistencia fuerte

## Success Metrics

- [ ] Tiempo de respuesta P99 < 100ms en queries de órdenes — By: 2026-08-01
- [ ] Cero pérdida de datos en pruebas de carga — By: 2026-07-01
