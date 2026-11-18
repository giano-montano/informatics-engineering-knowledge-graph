# Contenedor web: nginx sirve el compilado de la aplicación y reenvía /api y
# /resources a la API, bajo un mismo dominio (ADR-007).
FROM node:22-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM nginx:1.30-alpine
# La imagen de nginx sustituye las variables de entorno de esta plantilla al
# arrancar. Dentro de compose, la API responde en `api:8000`.
ENV IEKG_API_UPSTREAM=api:8000
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
