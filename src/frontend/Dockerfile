# ============================================
# SynapSeed — Frontend Dockerfile
# ============================================
# Dev: Vite HMR con volúmenes montados desde docker-compose.
# Prod: multi-stage con build estático servido por Nginx.

# ---------- Etapa de desarrollo ----------
FROM node:20-alpine AS dev

WORKDIR /app

# Copiar manifests primero para aprovechar caché de capas.
# El lockfile puede no existir en clones locales, así que copiamos ambos patrones.
COPY package*.json ./

# Usar npm ci cuando existe lockfile; npm install como fallback local.
RUN if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi

# El resto del código lo montan los volúmenes de docker-compose
# (solo copiamos aquí para que la imagen sea autosuficiente si no se monta)
COPY . .

EXPOSE 5173

# Vite dev server escucha en todas las interfaces (necesario en contenedor)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---------- Etapa de build estático ----------
FROM dev AS builder

RUN npm run build

# ---------- Etapa de producción (Nginx) ----------
FROM nginx:1.27-alpine AS prod

# Configuración mínima de Nginx para SPA
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { try_files $uri $uri/ /index.html; } \
    location /api/ { return 502; } \
}' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
