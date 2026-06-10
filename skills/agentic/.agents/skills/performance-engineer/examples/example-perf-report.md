# Reporte de Rendimiento: API de Catálogo de Productos

**Fecha**: 2026-05-29  
**Objetivo**: Analizar la degradación de rendimiento en el endpoint `GET /api/v1/products` bajo carga alta.

## 1. Análisis de Rendimiento

- **Métricas Actuales (Bajo Carga):**
  - **Throughput**: 45 RPS (Objetivo: 200 RPS)
  - **Latencia (p95)**: 2.4 segundos (Objetivo: < 300ms)
  - **Error Rate**: 3.5% (Errores 504 Gateway Timeout)
- **Cuello de Botella Identificado**: Las trazas de APM muestran que el 85% del tiempo de respuesta se consume en llamadas a la base de datos PostgreSQL. Específicamente, se identificó un problema de consultas N+1 al obtener las categorías de los productos.

## 2. Estrategia de Medición

- **Profiling**: Se utilizó `cProfile` (Python) para identificar funciones lentas en el código.
- **Load Testing**: Se configuró un script en `k6` para simular 100 usuarios concurrentes navegando el catálogo durante 5 minutos.
- **Monitoreo**: Datadog para observar el uso de CPU y el tiempo de consulta a la base de datos.

## 3. Propuesta de Optimización

1. **Resolver N+1 Queries**: Modificar el ORM para usar `select_related` o `prefetch_related` y obtener productos y categorías en una sola consulta SQL.
2. **Implementar Cache-Aside**: 
   - Añadir una capa de Redis.
   - Cachear la respuesta serializada de `/api/v1/products?page=1` por 5 minutos (TTL).
   - Invalidar la caché automáticamente en operaciones de escritura sobre el inventario.
3. **Paginación Eficiente**: Cambiar la paginación basada en OFFSET por paginación basada en Cursores (Keyset Pagination) para evitar escaneos lentos de tablas grandes.

## 4. Implementación (Ejemplo de Script k6)

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp-up a 50 usuarios
    { duration: '3m', target: 50 },  // Mantener carga
    { duration: '1m', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300'], // 95% de peticiones deben tardar menos de 300ms
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/products?limit=20');
  check(res, { 'status was 200': (r) => r.status == 200 });
  sleep(1);
}
```

## 5. Impacto Esperado

- **Throughput**: Aumento estimado a **350 RPS**.
- **Latencia (p95)**: Reducción drástica a **< 50ms** para hits en caché y ~150ms para cache misses (debido a la consulta SQL optimizada).
- **Recursos**: Reducción del uso de CPU en la base de datos PostgreSQL de un 80% a un 25%.
