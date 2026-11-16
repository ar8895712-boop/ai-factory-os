# ==============================================================
# frontend/Dockerfile — Multi-Stage Production Build
# Stage 1: Build static assets with Node.js
# Stage 2: Serve optimized bundle with Nginx Alpine (< 25MB)
# ==============================================================

# --- Stage 1: Builder ---
FROM node:18-alpine AS builder

WORKDIR /app

# Cache package installation layer
COPY package*.json ./
RUN npm ci

# Copy frontend source code and compile
COPY . .
RUN npm run build

# --- Stage 2: Production Nginx Server ---
FROM nginx:1.25-alpine AS runner

# Remove default Nginx HTML files
RUN rm -rf /usr/share/nginx/html/*

# Copy built production assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy optimized reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Healthcheck validating nginx status
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
