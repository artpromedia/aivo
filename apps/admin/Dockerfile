# hadolint ignore=DL3007,DL3008
# Use the exact Node version you're developing with
FROM node:20.19-alpine AS builder

# Install security updates
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with security audit
RUN npm ci --only=production && npm audit fix

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Build stage
FROM node:20.19-alpine AS runtime

# Install dumb-init to handle signals properly
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy from builder
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/package*.json ./

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Use dumb-init to start the app
ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "start"]
