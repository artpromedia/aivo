# hadolint ignore=DL3007,DL3008
FROM alpine:latest

# Install postfix and related packages
RUN apk update && apk upgrade && \
    apk add --no-cache \
    postfix \
    postfix-pcre \
    ca-certificates \
    rsyslog \
    && rm -rf /var/cache/apk/*

# Create mail directory
RUN mkdir -p /var/mail && \
    chown -R postfix:postfix /var/mail

# Copy configuration files
COPY postfix/ /etc/postfix/

EXPOSE 25 587

CMD ["postfix", "start-fg"]
