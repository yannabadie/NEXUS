# Stage 1: Build
FROM node:20-slim AS builder

WORKDIR /app

# Install Dependencies
COPY package*.json ./
RUN npm ci

# Copy Source
COPY . .

# Build
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Copy Build Artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx Config (Optional: Add custom conf if needed for routing)
# For now, default is fine.

# Expose Port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
