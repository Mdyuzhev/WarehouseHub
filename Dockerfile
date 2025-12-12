# =============================================================================
# Dockerfile для warehouse-frontend (Vue.js + Nginx)
# Multi-stage build
# =============================================================================

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Копируем package files
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходники
COPY . .

# Собираем production build
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:alpine AS production

# Копируем собранное приложение
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Порт
EXPOSE 80

# Nginx запускается автоматически
CMD ["nginx", "-g", "daemon off;"]
