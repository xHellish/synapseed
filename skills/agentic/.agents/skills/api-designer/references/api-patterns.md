# API Design Patterns & Best Practices

## 1. RESTful Resource Naming
- **Use Nouns, Not Verbs**: URIs should represent resources.
  - Good: `/users`, `/articles`, `/users/123/orders`
  - Bad: `/getUsers`, `/createArticle`
- **Pluralization**: Keep resource names plural for consistency.
  - Good: `/users/123`
  - Bad: `/user/123`
- **Hierarchy**: Use sub-resources for relations, but avoid deep nesting (limit to 2-3 levels).
  - Good: `/users/123/orders`
  - If deeper: Use a new root resource. E.g. instead of `/users/123/orders/456/items/789`, use `/orders/456/items/789`.

## 2. HTTP Methods
- `GET`: Read resources. Must be idempotent and safe.
- `POST`: Create a new resource, or execute an action (e.g. `/search`). Not idempotent.
- `PUT`: Replace an existing resource entirely. Idempotent.
- `PATCH`: Partially update a resource. 
- `DELETE`: Remove a resource. Idempotent.

## 3. HTTP Status Codes
- **200 OK**: General success (GET, PUT, PATCH).
- **201 Created**: Resource created successfully (POST). Return `Location` header.
- **204 No Content**: Success but no body (often for DELETE).
- **400 Bad Request**: Client error (validation, malformed request).
- **401 Unauthorized**: Missing or invalid authentication.
- **403 Forbidden**: Authenticated, but lacks permissions (authorization).
- **404 Not Found**: Resource doesn't exist.
- **409 Conflict**: State conflict (e.g., duplicate unique constraint).
- **422 Unprocessable Entity**: Semantic errors in validation.
- **500 Internal Server Error**: Generic server fault. Avoid leaking stack traces.

## 4. Pagination Strategies
### Offset-based Pagination
- **Parameters**: `limit` (page size), `offset` (items to skip).
- **Pros**: Easy to implement, allows jumping to a specific page.
- **Cons**: Poor performance on large datasets. Prone to skipping/duplicating items if data changes between queries.
- **Example**: `GET /users?limit=20&offset=40`

### Cursor-based Pagination
- **Parameters**: `cursor` (pointer to the last item), `limit`.
- **Pros**: Scales well with large datasets. Resilient to data insertions/deletions.
- **Cons**: Harder to implement. Cannot jump to page X.
- **Example**: `GET /users?limit=20&after=eyJpZCI6MTU2fQ==`

## 5. Filtering and Sorting
- **Filtering**: Use query parameters.
  - Exact match: `GET /users?status=active`
  - Complex filters (LHS brackets): `GET /users?age[gte]=18`
- **Sorting**: Use a `sort` parameter, optionally prefixed with `-` for descending.
  - `GET /users?sort=-created_at,name`

## 6. Authentication in Contracts
Always define security schemes in the OpenAPI spec.
- **Bearer Token (JWT)**
- **OAuth2**: Define flows (authorizationCode, clientCredentials).
- **API Keys**: Can be in Headers, Cookies, or Query (prefer Headers for security).

## 7. Versioning Strategies
### URI Versioning
- **Example**: `https://api.example.com/v1/users`
- **Pros**: Simple, highly visible, easy to cache.
- **Cons**: Clutters URIs, breaking links across versions.
### Header Versioning
- **Example**: `Accept: application/vnd.example.v1+json` or `X-API-Version: 1`
- **Pros**: Clean URIs.
- **Cons**: Harder to test in browser, requires header inspection for routing.
### Query Parameter Versioning
- **Example**: `https://api.example.com/users?version=1`
- **Pros**: Easy to test.
- **Cons**: Poor practice for RESTful purity.
