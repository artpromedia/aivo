# PowerShell script for certificate generation on Windows
# Certificate Authority and Service Certificate Generation for gRPC Mesh

param(
    [string]$CertDir = ".\certs",
    [int]$CAValidityDays = 3650,
    [int]$CertValidityDays = 365,
    [int]$KeySize = 2048
)

$ErrorActionPreference = "Stop"

# Create certificate directory structure
New-Item -ItemType Directory -Force -Path "$CertDir\ca" | Out-Null
New-Item -ItemType Directory -Force -Path "$CertDir\services" | Out-Null

Write-Host "🔐 Generating Certificate Authority..." -ForegroundColor Green

# Check if OpenSSL is available
try {
    $opensslVersion = & openssl version 2>$null
    Write-Host "✅ Using OpenSSL: $opensslVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ OpenSSL not found. Please install OpenSSL or use WSL."
    exit 1
}

# Generate CA private key
& openssl genrsa -out "$CertDir\ca\ca-key.pem" $KeySize

# Generate CA certificate
& openssl req -new -x509 -sha256 -days $CAValidityDays `
  -key "$CertDir\ca\ca-key.pem" `
  -out "$CertDir\ca\ca.crt" `
  -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Platform Infrastructure/CN=Aivo Internal CA"

Write-Host "✅ CA certificate generated: $CertDir\ca\ca.crt" -ForegroundColor Green

# Define services for certificate generation
$services = @(
    "event-collector-svc",
    "auth-svc",
    "learner-svc",
    "analytics-svc",
    "tenant-svc",
    "payment-svc",
    "approval-svc",
    "notification-svc",
    "admin-portal-svc",
    "inference-gateway-svc",
    "iep-svc",
    "assessment-svc",
    "coursework-ingest-svc",
    "device-enroll-svc",
    "device-ota-svc",
    "device-policy-svc",
    "edge-bundler-svc",
    "ela-eval-svc",
    "enrollment-router-svc",
    "game-gen-svc",
    "hello-svc",
    "ink-svc",
    "lesson-registry-svc",
    "math-recognizer-svc",
    "model-dispatch-svc",
    "problem-session-svc",
    "science-solver-svc",
    "search-svc",
    "slp-sel-svc",
    "subject-brain-svc"
)

foreach ($service in $services) {
    Write-Host "🔑 Generating certificate for $service..." -ForegroundColor Yellow
    
    # Generate service private key
    & openssl genrsa -out "$CertDir\services\$service-key.pem" $KeySize
    
    # Create certificate signing request
    & openssl req -new -sha256 `
      -key "$CertDir\services\$service-key.pem" `
      -out "$CertDir\services\$service.csr" `
      -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Platform Services/CN=$service"
    
    # Create certificate extension file with SAN
    $extContent = @"
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $service
DNS.2 = $service.default
DNS.3 = $service.default.svc
DNS.4 = $service.default.svc.cluster.local
DNS.5 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"@
    
    $extContent | Out-File -FilePath "$CertDir\services\$service.ext" -Encoding ASCII
    
    # Sign the certificate with CA
    & openssl x509 -req -sha256 -days $CertValidityDays `
      -in "$CertDir\services\$service.csr" `
      -CA "$CertDir\ca\ca.crt" `
      -CAkey "$CertDir\ca\ca-key.pem" `
      -CAcreateserial `
      -out "$CertDir\services\$service.crt" `
      -extensions v3_req `
      -extfile "$CertDir\services\$service.ext"
    
    # Clean up temporary files
    Remove-Item "$CertDir\services\$service.csr"
    Remove-Item "$CertDir\services\$service.ext"
    
    Write-Host "✅ Certificate generated for $service" -ForegroundColor Green
}

# Generate mesh client certificate
Write-Host "🔑 Generating mesh proxy certificates..." -ForegroundColor Yellow

& openssl genrsa -out "$CertDir\mesh-client-key.pem" $KeySize
& openssl req -new -sha256 `
  -key "$CertDir\mesh-client-key.pem" `
  -out "$CertDir\mesh-client.csr" `
  -subj "/C=US/ST=CA/L=San Francisco/O=Aivo Platform/OU=Mesh Proxies/CN=mesh-client"

$meshExtContent = @"
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
"@

$meshExtContent | Out-File -FilePath "$CertDir\mesh-client.ext" -Encoding ASCII

& openssl x509 -req -sha256 -days $CertValidityDays `
  -in "$CertDir\mesh-client.csr" `
  -CA "$CertDir\ca\ca.crt" `
  -CAkey "$CertDir\ca\ca-key.pem" `
  -CAcreateserial `
  -out "$CertDir\mesh-client.crt" `
  -extensions v3_req `
  -extfile "$CertDir\mesh-client.ext"

Remove-Item "$CertDir\mesh-client.csr"
Remove-Item "$CertDir\mesh-client.ext"

Write-Host ""
Write-Host "🎉 Certificate generation complete!" -ForegroundColor Green
Write-Host "📁 CA Certificate: $CertDir\ca\ca.crt" -ForegroundColor Cyan
Write-Host "📁 Service Certificates: $CertDir\services\" -ForegroundColor Cyan
Write-Host "📁 Mesh Client Certificate: $CertDir\mesh-client.crt" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Remember to:" -ForegroundColor Yellow
Write-Host "  1. Distribute CA certificate to all services" -ForegroundColor Yellow
Write-Host "  2. Distribute service-specific certificates to each service" -ForegroundColor Yellow
Write-Host "  3. Set appropriate file permissions in production" -ForegroundColor Yellow
Write-Host "  4. Rotate certificates before expiration" -ForegroundColor Yellow
