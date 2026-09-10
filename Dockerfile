FROM node:20-alpine AS base
WORKDIR /app

COPY package*.json ./
COPY apps/tms/package*.json ./apps/tms/
COPY apps/admin/package*.json ./apps/admin/
RUN npm install

FROM base AS tms
COPY apps/tms ./apps/tms
RUN npm --prefix apps/tms run build
EXPOSE 3000
CMD ["npm", "--prefix", "apps/tms", "run", "start"]

FROM base AS admin
COPY apps/admin ./apps/admin
RUN npm --prefix apps/admin run build
EXPOSE 3001
CMD ["npm", "--prefix", "apps/admin", "run", "start"]
