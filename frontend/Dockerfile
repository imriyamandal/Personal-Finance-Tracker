# Stage 1: Build React SPA
FROM node:20-alpine AS build

WORKDIR /app

# Copy packages and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build static assets
COPY . .
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:stable-alpine

# Copy compiled SPA dist files to nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Expose Nginx server port
EXPOSE 80

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
