# hadolint ignore=DL3007,DL3008
FROM alpine:latest

# Install postfix and related packages
RUN apk update && apk upgrade && \
    apk add --no-cache \
    postfix \
    postfix-pcre \
    ca-certificates \
    rsyslog \
    curl \
    && rm -rf /var/cache/apk/*

# Create mail directory
RUN mkdir -p /var/mail && \
    chown -R postfix:postfix /var/mail

# Copy configuration files
COPY postfix/ /etc/postfix/

# Health check endpoint
COPY healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

# Create a simple health check HTTP server
RUN printf '#!/bin/sh\nwhile true; do\n  printf "HTTP/1.1 200 OK\\r\\n\\r\\nOK" | nc -l -p 8080\ndone\n' > /usr/local/bin/health-server.sh && \
    chmod +x /usr/local/bin/health-server.sh

EXPOSE 25 587 993 8080

CMD ["sh", "-c", "/usr/local/bin/health-server.sh & postfix start-fg"]
