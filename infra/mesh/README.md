# gRPC Mesh Infrastructure - Quick Start Guide

This directory contains a complete gRPC service mesh implementation with mTLS,
service discovery, observability, and resilience patterns.

## Quick Start

### 1. Generate Certificates

```bash
# Windows
.\scripts\generate-certs.ps1 -CertDir .\certs

# Linux/macOS  
./scripts/generate-certs.sh ./certs
```

### 2. Deploy Infrastructure

```bash
# Deploy all components
python scripts/deploy-mesh.py deploy

# Deploy specific components
python scripts/deploy-mesh.py deploy --components consul jaeger prometheus
```

### 3. Test the Mesh

```bash
python scripts/test-mesh.py --verbose
```

### 4. Monitor the Mesh

- **Consul UI**: <http://localhost:8500>
- **Jaeger UI**: <http://localhost:16686>  
- **Prometheus**: <http://localhost:9090>
- **Grafana**: <http://localhost:3000> (admin/admin123)

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service A     │    │   Service B     │    │   Service C     │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ gRPC Server │ │    │ │ gRPC Server │ │    │ │ gRPC Server │ │
│ │   :8080     │ │    │ │   :8080     │ │    │ │   :8080     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Envoy Sidecar│ │    │ │Envoy Sidecar│ │    │ │Envoy Sidecar│ │
│ │   :50051    │ │    │ │   :50051    │ │    │ │   :50051    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Service Discovery│
                    │    (Consul)     │
                    │    :8500        │
                    └─────────────────┘
```

## Components

### Core Infrastructure

- **Envoy Proxy**: mTLS, load balancing, circuit breakers
- **Consul**: Service discovery and health checking
- **Certificates**: Self-signed CA with service certificates

### Observability

- **Jaeger**: Distributed tracing
- **Prometheus**: Metrics collection  
- **Grafana**: Metrics visualization
- **StatsD**: Metrics aggregation

### Resilience Patterns

- **Circuit Breakers**: Automatic failure detection
- **Retries**: Exponential backoff with jitter
- **Timeouts**: Per-route deadline enforcement
- **Health Checks**: gRPC health check protocol

## Configuration Files

### Envoy Configuration

- `envoy/bootstrap.yaml` - Inbound proxy configuration
- `envoy/sidecar.yaml` - Outbound proxy configuration

### Monitoring

- `prometheus/prometheus.yml` - Metrics collection rules
- `grafana/dashboards/` - Pre-built dashboards
- `grafana/provisioning/` - Automated setup

### Scripts

- `scripts/generate-certs.{sh,ps1}` - Certificate generation
- `scripts/deploy-mesh.py` - Deployment automation
- `scripts/test-mesh.py` - Integration testing

### Python Libraries

- `python/mesh_client.py` - gRPC mesh client library
- `python/health_service.py` - Health check implementations

## Service Integration

### Adding a New Service

1. **Create service certificates**:

```bash
# Add service name to generate-certs script, then run:
./scripts/generate-certs.sh ./certs
```

1. **Add to docker-compose.yml**:

```yaml
my-service:
  build: ../../services/my-service
  environment:
    - SERVICE_NAME=my-service
    - GRPC_PORT=50051

my-service-envoy:
  image: envoyproxy/envoy:v1.28.0
  volumes:
    - ./envoy/bootstrap.yaml:/etc/envoy/envoy.yaml:ro
    - ./certs/services/my-service.crt:/etc/ssl/certs/service.crt:ro
    - ./certs/services/my-service-key.pem:/etc/ssl/private/service.key:ro
```

1. **Implement health checks**:

```python
from infra.mesh.python.health_service import add_health_servicer

# In your gRPC server setup:
health_servicer = add_health_servicer(server)
health_servicer.set_serving()  # Mark as healthy
```

1. **Use mesh client**:

```python
from infra.mesh.python.mesh_client import create_mesh_client

with create_mesh_client() as mesh_client:
    stub = mesh_client.create_stub(
        "target-service",
        TargetServiceStub,
        timeout=10.0
    )
    response = stub.SomeMethod(request)
```

## Security Features

### mTLS Configuration

- Root CA for service mesh
- Individual certificates per service
- SAN-based certificate validation
- Automatic certificate distribution

### Network Policies

- Service-to-service encryption
- Certificate-based authentication
- Network segmentation via Envoy

## Performance Tuning

### Connection Management

```yaml
# HTTP/2 optimization
http2_protocol_options:
  initial_stream_window_size: 65536
  initial_connection_window_size: 1048576
  max_concurrent_streams: 100
```

### Circuit Breaker Settings

```yaml
circuit_breakers:
  thresholds:
  - priority: DEFAULT
    max_connections: 100
    max_pending_requests: 200
    max_requests: 500
    max_retries: 5
```

### Retry Policies

```yaml
retry_policy:
  retry_on: "5xx,reset,connect-failure,refused-stream"
  num_retries: 3
  per_try_timeout: 5s
  retry_back_off:
    base_interval: 0.25s
    max_interval: 2s
```

## Troubleshooting

### Common Issues

1. **Certificate Errors**:

```bash
# Check certificate validity
openssl x509 -in certs/services/service-name.crt -text -noout

# Verify SAN entries
openssl x509 -in certs/services/service-name.crt -text | grep -A5 "Subject Alternative Name"
```

1. **Connection Issues**:

```bash
# Check Envoy admin interface
curl http://localhost:9901/clusters
curl http://localhost:9901/listeners

# Check service discovery
curl http://localhost:8500/v1/catalog/services
```

1. **Performance Issues**:

```bash
# Check Envoy stats
curl http://localhost:9901/stats | grep -E "(retry|circuit|timeout)"

# View Jaeger traces
open http://localhost:16686
```

### Debug Commands

```bash
# Check mesh status
python scripts/deploy-mesh.py status

# Run comprehensive tests  
python scripts/test-mesh.py --verbose

# View Envoy configuration
curl http://localhost:9901/config_dump | jq

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Production Considerations

### Security

- [ ] Replace self-signed certificates with proper CA
- [ ] Implement certificate rotation
- [ ] Add RBAC policies
- [ ] Enable audit logging

### Scalability  

- [ ] Configure horizontal pod autoscaling
- [ ] Implement multi-region support
- [ ] Add traffic splitting/canary deployments
- [ ] Optimize connection pooling

### Monitoring

- [ ] Set up alerting rules
- [ ] Configure log aggregation
- [ ] Implement SLO/SLI tracking
- [ ] Add business metrics dashboards

### Reliability

- [ ] Configure backup and restore
- [ ] Implement disaster recovery
- [ ] Add chaos engineering tests
- [ ] Set up runbook automation

## References

- [Envoy Proxy Documentation](https://www.envoyproxy.io/docs)
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)
- [Consul Service Discovery](https://www.consul.io/docs/discovery)
- [Prometheus Monitoring](https://prometheus.io/docs)
- [Jaeger Tracing](https://www.jaegertracing.io/docs)
