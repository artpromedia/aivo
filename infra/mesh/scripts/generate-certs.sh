#!/bin/bash
# Certificate Authority and Service Certificate Generation for gRPC Mesh
# This script generates a CA and service certificates for mTLS

set -euo pipefail

CERT_DIR="${1:-./certs}"
CA_VALIDITY_DAYS="${CA_VALIDITY_DAYS:-3650}"
CERT_VALIDITY_DAYS="${CERT_VALIDITY_DAYS:-365}"
KEY_SIZE="${KEY_SIZE:-2048}"

# Create certificate directory
mkdir -p "${CERT_DIR}"/{ca,services}

echo "🔐 Generating Certificate Authority..."

# Generate CA private key
openssl genrsa -out "${CERT_DIR}/ca/ca-key.pem" ${KEY_SIZE}

# Generate CA certificate
openssl req -new -x509 -sha256 -days ${CA_VALIDITY_DAYS} \
  -key "${CERT_DIR}/ca/ca-key.pem" \
  -out "${CERT_DIR}/ca/ca.crt" \
  -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Platform Infrastructure/CN=Aivo Internal CA"

echo "✅ CA certificate generated: ${CERT_DIR}/ca/ca.crt"

# Generate service certificates for each service
SERVICES=(
  "event-collector-svc"
  "auth-svc"
  "learner-svc"
  "analytics-svc"
  "tenant-svc"
  "payment-svc"
  "approval-svc"
  "notification-svc"
  "admin-portal-svc"
  "inference-gateway-svc"
  "iep-svc"
  "assessment-svc"
  "coursework-ingest-svc"
  "device-enroll-svc"
  "device-ota-svc"
  "device-policy-svc"
  "edge-bundler-svc"
  "ela-eval-svc"
  "enrollment-router-svc"
  "game-gen-svc"
  "hello-svc"
  "ink-svc"
  "lesson-registry-svc"
  "math-recognizer-svc"
  "model-dispatch-svc"
  "problem-session-svc"
  "science-solver-svc"
  "search-svc"
  "slp-sel-svc"
  "subject-brain-svc"
)

for service in "${SERVICES[@]}"; do
  echo "🔑 Generating certificate for ${service}..."
  
  # Generate service private key
  openssl genrsa -out "${CERT_DIR}/services/${service}-key.pem" ${KEY_SIZE}
  
  # Create certificate signing request
  openssl req -new -sha256 \
    -key "${CERT_DIR}/services/${service}-key.pem" \
    -out "${CERT_DIR}/services/${service}.csr" \
    -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Platform Services/CN=${service}"
  
  # Create certificate extension file with SAN
  cat > "${CERT_DIR}/services/${service}.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${service}
DNS.2 = ${service}.default
DNS.3 = ${service}.default.svc
DNS.4 = ${service}.default.svc.cluster.local
DNS.5 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
  
  # Sign the certificate with CA
  openssl x509 -req -sha256 -days ${CERT_VALIDITY_DAYS} \
    -in "${CERT_DIR}/services/${service}.csr" \
    -CA "${CERT_DIR}/ca/ca.crt" \
    -CAkey "${CERT_DIR}/ca/ca-key.pem" \
    -CAcreateserial \
    -out "${CERT_DIR}/services/${service}.crt" \
    -extensions v3_req \
    -extfile "${CERT_DIR}/services/${service}.ext"
  
  # Clean up CSR and extension files
  rm "${CERT_DIR}/services/${service}.csr" "${CERT_DIR}/services/${service}.ext"
  
  echo "✅ Certificate generated for ${service}"
done

# Generate generic mesh certificates for Envoy sidecars
echo "🔑 Generating mesh proxy certificates..."

# Mesh client certificate
openssl genrsa -out "${CERT_DIR}/mesh-client-key.pem" ${KEY_SIZE}
openssl req -new -sha256 \
  -key "${CERT_DIR}/mesh-client-key.pem" \
  -out "${CERT_DIR}/mesh-client.csr" \
  -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Mesh Proxies/CN=mesh-client"

cat > "${CERT_DIR}/mesh-client.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = mesh-client
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

openssl x509 -req -sha256 -days ${CERT_VALIDITY_DAYS} \
  -in "${CERT_DIR}/mesh-client.csr" \
  -CA "${CERT_DIR}/ca/ca.crt" \
  -CAkey "${CERT_DIR}/ca/ca-key.pem" \
  -CAcreateserial \
  -out "${CERT_DIR}/mesh-client.crt" \
  -extensions v3_req \
  -extfile "${CERT_DIR}/mesh-client.ext"

rm "${CERT_DIR}/mesh-client.csr" "${CERT_DIR}/mesh-client.ext"

# Set appropriate permissions
chmod 600 "${CERT_DIR}/ca/ca-key.pem"
chmod 644 "${CERT_DIR}/ca/ca.crt"
chmod 600 "${CERT_DIR}/services/"*"-key.pem"
chmod 644 "${CERT_DIR}/services/"*".crt"
chmod 600 "${CERT_DIR}/mesh-client-key.pem"
chmod 644 "${CERT_DIR}/mesh-client.crt"

echo ""
echo "🎉 Certificate generation complete!"
echo "📁 CA Certificate: ${CERT_DIR}/ca/ca.crt"
echo "📁 Service Certificates: ${CERT_DIR}/services/"
echo "📁 Mesh Client Certificate: ${CERT_DIR}/mesh-client.crt"
echo ""
echo "⚠️  Remember to:"
echo "  1. Distribute CA certificate to all services"
echo "  2. Distribute service-specific certificates to each service"
echo "  3. Set appropriate file permissions in production"
echo "  4. Rotate certificates before expiration"
