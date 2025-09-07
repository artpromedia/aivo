#!/bin/sh
# Health check script for mailserver

# Check if postfix is running
if ! pgrep -f "postfix" > /dev/null; then
    echo "Postfix is not running"
    exit 1
fi

# Check if port 25 is listening
if ! netstat -ln | grep -q ":25 "; then
    echo "Port 25 is not listening"
    exit 1
fi

echo "Mailserver is healthy"
exit 0
