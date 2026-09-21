FROM node:22-alpine AS builder

WORKDIR /app
RUN corepack enable pnpm

# Copy workspace config
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./

# Copy frontends
COPY apps/frontend/tms ./apps/frontend/tms
COPY apps/frontend/admin ./apps/frontend/admin

# Install dependencies (only for frontends)
RUN pnpm install --filter tms --filter admin

# Build TMS
FROM builder AS build-tms
RUN pnpm --filter tms run build

# Build Admin
FROM builder AS build-admin
RUN pnpm --filter admin run build

# Serve TMS
FROM nginx:alpine AS tms
COPY --from=build-tms /app/apps/frontend/tms/dist /usr/share/nginx/html
# SPA routing fallback for nginx
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Serve Admin
FROM nginx:alpine AS admin
COPY --from=build-admin /app/apps/frontend/admin/dist /usr/share/nginx/html
# SPA routing fallback for nginx
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
