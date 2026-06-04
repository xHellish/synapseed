# ============================================
# SynapSeed — Frontend Dockerfile (Vite dev server)
# ============================================
# Imagen para desarrollo con HMR. Para producción usar
# `vite build` + servidor estático (Nginx) en otra etapa.

FROM node:20-alpine

WORKDIR /app

# Copiar manifest primero para cache de dependencias
COPY package.json ./

# Si usás pnpm/npm con lockfile, lo copiamos también:
# COPY package-lock.json pnpm-lock.yaml yarn.lock* ./

# (en dev montamos los volúmenes desde docker-compose,
#  por lo que npm install corre dentro del contenedor)
RUN npm install --no-audit --no-fund || true

# Copiar el resto del código
COPY . .

EXPOSE 5173

# Vite dev server escucha en 0.0.0.0:5173
# (HMR funciona porque montamos el código como volumen)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
