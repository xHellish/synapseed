# Example: API Design Review

## 1. Análisis de Requerimientos
El equipo ha propuesto una API para gestionar un sistema de e-commerce. La propuesta original contiene las siguientes rutas:
- `GET /getAllProducts`
- `POST /addProduct`
- `POST /updateProduct?id=5`
- `GET /products/123/reviews/456/author/details`

**Problemas identificados:**
- Uso de verbos en las URIs (`getAllProducts`, `addProduct`).
- Uso de `POST` y Query Parameters para actualizaciones (`updateProduct?id=5`).
- Anidamiento excesivo de recursos (`/products/123/reviews/456/author/details`).

## 2. Diseño de Endpoints
Se propone una refactorización orientada a recursos (RESTful):

| Endpoint Antiguo | Nuevo Endpoint Propuesto | Método | Descripción |
|------------------|--------------------------|--------|-------------|
| `GET /getAllProducts` | `/products` | `GET` | Obtiene lista de productos con paginación por cursor. |
| `POST /addProduct` | `/products` | `POST` | Crea un nuevo producto. Devuelve 201 Created. |
| `POST /updateProduct?id=5` | `/products/{id}` | `PATCH` | Actualización parcial del producto. |
| `GET /products/.../details` | `/reviews/{id}/author` | `GET` | Se aplanan las rutas para evitar anidamiento profundo. |

## 3. Especificación Detallada
A continuación, un extracto del contrato OpenAPI v3:

```yaml
openapi: 3.0.3
info:
  title: E-commerce API
  version: 1.0.0
paths:
  /products:
    get:
      summary: Lista productos
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: after
          in: query
          schema:
            type: string
            description: Cursor para paginación
      responses:
        '200':
          description: Lista de productos obtenida exitosamente.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProductList'
    post:
      summary: Crea un producto
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductInput'
      responses:
        '201':
          description: Producto creado.
```

## 4. Decisiones de Diseño
- **Estilo RESTful**: Se cambiaron las rutas a sustantivos plurales (`/products`) para alinearse con los estándares de la industria.
- **Paginación**: Se optó por paginación por cursor (`after`) dado que el catálogo de productos es extenso y se actualiza frecuentemente, evitando problemas de offset.
- **Códigos de Estado**: Se especificó `201 Created` para la creación exitosa de recursos, con la expectativa de incluir un header `Location`.
