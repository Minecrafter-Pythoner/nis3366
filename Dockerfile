# Stage 1: Build Vue frontend
FROM node:18 AS frontend-builder
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build

# Stage 2: Build backend
FROM python:3.10-slim AS backend-builder
WORKDIR /app
COPY backend/ .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Stage 3: Final image with Nginx and backend
FROM nginx:1.25-alpine

# Copy Nginx config
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built frontend to Nginx web root
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy backend to /app
COPY --from=backend-builder /app /app

# Install supervisor to run both Nginx and FastAPI
RUN apk add --no-cache supervisor
COPY ./supervisord.conf /etc/supervisord.conf

# Expose Nginx port
EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
