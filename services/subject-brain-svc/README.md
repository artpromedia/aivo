# Subject-Brain Service

AI-powered planner and runtime for per-learner-subject GPU pods with Kubernetes autoscaling.

## Overview

The Subject-Brain Service provides personalized learning activity planning and
execution through ephemeral Kubernetes pods with GPU autoscaling. Each
learner-subject combination gets its own runtime environment that scales based
on demand and automatically terminates when idle.

## Features

### 🧠 AI-Powered Planner

- **Learner Analysis**: Evaluates baseline knowledge and mastery levels
- **Context-Aware Planning**: Considers coursework topics and teacher constraints
- **Personalized Sequences**: Generates optimal activity sequences for learning sessions
- **Multi-Subject Support**: Mathematics, Science, Language Arts, Social Studies,
  Foreign Languages

### 🚀 Dynamic Runtime Management

- **Per-Learner-Subject Pods**: Isolated execution environments for each
  learner-subject
- **GPU Resource Allocation**: Automatic GPU assignment based on computational
  needs
- **Elastic Scaling**: Horizontal Pod Autoscaler based on GPU queue depth and
  resource utilization
- **Cost Optimization**: TTL-based scale-to-zero for idle runtimes

### 📊 Advanced Monitoring

- **Real-Time Metrics**: GPU queue depth, CPU/memory utilization, active
  learners
- **Scaling Analytics**: Performance data for optimization decisions
- **Health Monitoring**: Comprehensive service and pod health checks

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Planner Service│────│ Activity Plans  │
│   (REST API)    │    │  (AI Planning)  │    │ (Personalized)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │ Runtime Manager │────│ Kubernetes API  │
         │              │ (Pod Lifecycle) │    │ (Pod Management) │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         └──────────────│ HPA Controller  │────│ GPU Autoscaler  │
                        │ (Auto Scaling)  │    │ (Queue-Based)   │
                        └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Kubernetes cluster with GPU nodes
- NVIDIA GPU Operator installed
- Prometheus for metrics collection
- PostgreSQL database
- Redis cache

### Deployment

1. **Create Namespace and RBAC**:

```bash
kubectl apply -f k8s/namespace.yaml
```

1. **Deploy HPA and Secrets**:

```bash
kubectl apply -f k8s/hpa.yaml
```

1. **Deploy Service**:

```bash
kubectl apply -f k8s/deployment.yaml
```

1. **Verify Deployment**:

```bash
kubectl get pods -n subject-brain
kubectl get hpa -n subject-brain
```

### Configuration

Key environment variables:

```bash
# Service Configuration
SUBJECT_BRAIN_DEBUG=false
SUBJECT_BRAIN_LOG_LEVEL=INFO
SUBJECT_BRAIN_DATABASE_URL=postgresql://user:pass@localhost:5432/subject_brain
SUBJECT_BRAIN_REDIS_URL=redis://localhost:6379/0

# Kubernetes Configuration  
SUBJECT_BRAIN_K8S_NAMESPACE=subject-brain
SUBJECT_BRAIN_K8S_SERVICE_ACCOUNT=subject-brain-sa

# GPU Configuration
SUBJECT_BRAIN_GPU_NODE_SELECTOR={"accelerator": "nvidia-tesla-v100"}
SUBJECT_BRAIN_GPU_RESOURCE_REQUESTS={"nvidia.com/gpu": "1"}

# Autoscaling Configuration
SUBJECT_BRAIN_HPA_ENABLED=true
SUBJECT_BRAIN_HPA_MIN_REPLICAS=0
SUBJECT_BRAIN_HPA_MAX_REPLICAS=100
SUBJECT_BRAIN_HPA_TARGET_GPU_QUEUE_DEPTH=10
SUBJECT_BRAIN_HPA_TARGET_CPU_UTILIZATION=70
```

## API Usage

### Create Activity Plan

```http
POST /plan
Content-Type: application/json

{
  "learner_id": "learner_123",
  "subject": "mathematics", 
  "session_duration_minutes": 30,
  "force_refresh": false
}
```

### Get Runtime Status

```http
GET /runtime/{runtime_id}
```

### Monitor Metrics

```http
GET /metrics
```

Response:

```json
{
  "service_metrics": {
    "active_runtimes": 15,
    "total_pods": 15
  },
  "scaling_metrics": {
    "total_gpu_queue_depth": 45,
    "average_cpu_utilization": 68.5,
    "average_memory_usage_mb": 1536.2,
    "pending_requests": 3
  }
}
```

## Autoscaling Behavior

### Scale-Up Triggers

- **GPU Queue Depth**: > 10 requests per pod
- **CPU Utilization**: > 70% average across pods  
- **Memory Utilization**: > 80% average across pods

### Scale-Down Triggers

- **Idle Detection**: No activity for 5+ minutes (configurable TTL)
- **Low Utilization**: Sustained low resource usage
- **Queue Emptying**: GPU queue depth drops below threshold

### Scaling Policies

- **Scale-Up**: 100% increase every 15 seconds (max 4 pods)
- **Scale-Down**: 10% decrease every 60 seconds (max 1 pod)
- **Stabilization**: 30s up, 300s down windows

## Planner Intelligence

### Input Analysis

1. **Learner Baseline**: Current knowledge and skill levels
2. **Mastery Levels**: Per-topic proficiency (Not Started → Advanced)
3. **Coursework Topics**: Available learning content and prerequisites
4. **Teacher Constraints**: Preferences, blocked topics, time limits

### Planning Logic

1. **Need Assessment**: Identify struggling areas and knowledge gaps
2. **Topic Prioritization**: Weight by learning needs and prerequisites
3. **Activity Selection**: Choose optimal activity types (lesson, practice, assessment)
4. **Difficulty Adjustment**: Adapt content complexity to learner level
5. **Sequence Optimization**: Order activities for maximum learning efficiency

### Activity Types

- **Lesson**: Structured instruction for new concepts
- **Practice**: Skill reinforcement and application
- **Assessment**: Progress evaluation and feedback
- **Remediation**: Targeted support for struggling areas
- **Enrichment**: Advanced challenges for mastered topics

## Runtime Lifecycle

### Pod Creation

1. **Resource Allocation**: CPU, memory, and GPU assignment
2. **Environment Setup**: Learner context and activity plan injection
3. **Health Checks**: Readiness and liveness probe configuration
4. **Monitoring**: Metrics collection and status tracking

### Execution Monitoring

- **Activity Progress**: Real-time tracking of learning activities
- **Resource Usage**: CPU, GPU, and memory utilization
- **Performance Metrics**: Queue depth and response times
- **Health Status**: Pod and application health monitoring

### Termination Conditions

- **Completion**: All planned activities finished successfully
- **Timeout**: Maximum runtime duration exceeded
- **Idle TTL**: No activity for configured time period
- **Resource Limits**: Memory or CPU limits exceeded
- **Manual**: Explicit termination request

## Monitoring and Observability

### Metrics Exposed

- `subject_brain_active_runtimes_total`: Number of active runtime pods
- `subject_brain_gpu_queue_depth`: Current GPU processing queue depth
- `subject_brain_cpu_utilization_percent`: Average CPU utilization
- `subject_brain_memory_usage_bytes`: Memory usage across pods
- `subject_brain_plan_generation_duration_seconds`: Time to generate plans
- `subject_brain_runtime_duration_seconds`: Runtime execution duration

### Health Endpoints

- `GET /health`: Service health status
- `GET /metrics`: Prometheus metrics
- `GET /runtime/{id}`: Individual runtime status

### Logging

- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Learner ID, subject, runtime ID in all logs

## Development

### Local Setup

```bash
# Clone repository
git clone <repository-url>
cd services/subject-brain-svc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Integration tests
pytest tests/integration/
```

### Building

```bash
# Build Docker image
docker build -t subject-brain-svc:latest .

# Run container
docker run -p 8000:8000 -p 9090:9090 subject-brain-svc:latest
```

## Production Considerations

### Resource Planning

- **GPU Nodes**: Ensure sufficient GPU-enabled nodes
- **Memory**: Plan for 2GB+ per runtime pod
- **Storage**: Persistent volumes for AI models
- **Network**: High bandwidth for model loading

### Security

- **RBAC**: Least-privilege service account permissions
- **Secrets**: Encrypted storage of database and API keys
- **Network Policies**: Restrict pod-to-pod communication
- **Image Scanning**: Regular vulnerability assessment

### Monitoring

- **Alerts**: Set up alerts for high queue depth, pod failures
- **Dashboards**: Grafana dashboards for operational visibility
- **Logging**: Centralized log aggregation and analysis
- **Tracing**: Distributed tracing for request flows

## Troubleshooting

### Common Issues

**Pods Stuck in Pending**:

- Check GPU node availability
- Verify resource quotas
- Review node selectors

**High GPU Queue Depth**:

- Monitor autoscaler metrics
- Check scaling policies
- Verify node capacity

**Plan Generation Failures**:

- Check external service connectivity
- Review learner data availability
- Verify authentication tokens

### Useful Commands

```bash
# Check pod status
kubectl get pods -n subject-brain -l app=subject-brain-svc

# View HPA status
kubectl get hpa -n subject-brain subject-brain-hpa

# Check logs
kubectl logs -n subject-brain -l app=subject-brain-svc

# Monitor scaling events
kubectl get events -n subject-brain --sort-by='.lastTimestamp'

# Check GPU allocation
kubectl describe nodes -l accelerator=nvidia-tesla-v100
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
