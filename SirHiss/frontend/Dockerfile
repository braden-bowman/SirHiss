# Multi-stage build for optimized frontend
FROM node:18-alpine AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files for better caching
COPY package*.json ./
# Use npm install if no package-lock.json exists, otherwise use npm ci
RUN if [ -f package-lock.json ]; then \
    npm ci --omit=dev --cache /tmp/.npm && npm cache clean --force; \
    else \
    npm install --production --cache /tmp/.npm && npm cache clean --force; \
    fi

# Development stage
FROM node:18-alpine AS dev
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY package*.json ./

# Install dev dependencies
RUN npm install --omit=optional

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start the React app in development mode with optimized settings
CMD ["npm", "start"]

# Production build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependencies and source
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS production
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx config if needed
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]