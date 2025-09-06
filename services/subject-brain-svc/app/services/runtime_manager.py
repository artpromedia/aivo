"""Kubernetes Runtime Manager for per-learner-subject GPU pods."""

import logging
from datetime import datetime, timedelta
from typing import Any

try:
    from kubernetes import client, config
    from kubernetes.client import (
        V1Container,
        V1HorizontalPodAutoscaler,
        V1ObjectMeta,
        V1Pod,
        V1PodSpec,
        V1ResourceRequirements,
    )
    KUBERNETES_AVAILABLE = True
except ImportError:
    # Kubernetes client not available in development environment
    KUBERNETES_AVAILABLE = False
    # Mock objects for development
    client = None  # type: ignore
    config = None  # type: ignore

from ..config import settings
from ..models import (
    RuntimeMetrics,
    RuntimePod,
    RuntimeRequest,
    RuntimeStatus,
)

logger = logging.getLogger(__name__)


class KubernetesRuntimeManager:
    """Manages per-learner-subject runtime pods with GPU autoscaling."""

    def __init__(self) -> None:
        """Initialize the Kubernetes runtime manager."""
        if not KUBERNETES_AVAILABLE:
            logger.warning(
                "Kubernetes client not available. "
                "Service will run in mock mode for development."
            )
            
        self.namespace = settings.k8s_namespace
        self.service_account = settings.k8s_service_account

        # Initialize Kubernetes client
        if KUBERNETES_AVAILABLE:
            self._initialize_kubernetes_client()
        else:
            self.v1 = None
            self.apps_v1 = None
            self.autoscaling_v2 = None

        # Runtime tracking
        self.active_runtimes: dict[str, RuntimePod] = {}
        self.metrics_history: dict[str, list[RuntimeMetrics]] = {}

    def _initialize_kubernetes_client(self) -> None:
        """Initialize the Kubernetes API clients."""
        try:
            if settings.k8s_config_path:
                config.load_kube_config(config_file=settings.k8s_config_path)
            else:
                config.load_incluster_config()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to load k8s config: %s", e)
            # For development, try loading from default location
            try:
                config.load_kube_config()
            except Exception:
                logger.error("No valid Kubernetes configuration found")
                raise

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.autoscaling_v2 = client.AutoscalingV2Api()

        # Runtime tracking
        self.active_runtimes: dict[str, RuntimePod] = {}
        self.metrics_history: dict[str, list[RuntimeMetrics]] = {}

    async def create_runtime(
        self, runtime_request: RuntimeRequest
    ) -> RuntimePod:
        """Create a new per-learner-subject runtime pod."""
        logger.info(
            "Creating runtime %s for learner %s",
            runtime_request.runtime_id,
            runtime_request.learner_id
        )

        # Generate pod name
        pod_name = self._generate_pod_name(
            runtime_request.learner_id,
            runtime_request.subject,
            runtime_request.runtime_id
        )

        # Create pod specification
        pod_spec = self._create_pod_spec(runtime_request)

        # Create pod
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name=pod_name,
                namespace=self.namespace,
                labels={
                    "app": "subject-brain-runtime",
                    "learner-id": runtime_request.learner_id,
                    "subject": runtime_request.subject.value,
                    "runtime-id": runtime_request.runtime_id,
                    "component": "per-learner-subject"
                },
                annotations={
                    "subject-brain/created-at": datetime.utcnow().isoformat(),
                    "subject-brain/ttl-seconds": str(
                        settings.default_ttl_seconds
                    ),
                    "subject-brain/max-runtime-minutes": str(
                        runtime_request.max_runtime_minutes
                    )
                }
            ),
            spec=pod_spec
        )

        try:
            self.v1.create_namespaced_pod(
                namespace=self.namespace,
                body=pod
            )
            logger.info("Created pod %s", pod_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to create pod %s: %s", pod_name, e)
            raise

        # Create runtime tracking object
        runtime_pod = RuntimePod(
            runtime_id=runtime_request.runtime_id,
            learner_id=runtime_request.learner_id,
            subject=runtime_request.subject,
            pod_name=pod_name,
            namespace=self.namespace,
            status=RuntimeStatus.PENDING,
            metrics=RuntimeMetrics(runtime_id=runtime_request.runtime_id)
        )

        # Track the runtime
        self.active_runtimes[runtime_request.runtime_id] = runtime_pod

        return runtime_pod

    def _generate_pod_name(
        self, learner_id: str, subject: str, runtime_id: str
    ) -> str:
        """Generate a unique pod name."""
        # Clean the IDs for Kubernetes naming
        clean_learner = learner_id.replace("_", "-").lower()[:10]
        clean_subject = subject.replace("_", "-").lower()[:10]
        clean_runtime = runtime_id.replace("_", "-").lower()[:8]

        return f"brain-{clean_learner}-{clean_subject}-{clean_runtime}"

    def _create_pod_spec(self, runtime_request: RuntimeRequest) -> "V1PodSpec":
        """Create pod specification for the runtime."""
        # Resource requirements
        resources = V1ResourceRequirements(
            requests={
                "memory": f"{runtime_request.memory_mb}Mi",
                "cpu": str(runtime_request.cpu_cores),
            },
            limits={
                "memory": f"{runtime_request.memory_mb * 2}Mi",
                "cpu": str(runtime_request.cpu_cores * 2),
            }
        )

        # Add GPU resources if required
        if runtime_request.gpu_required:
            resources.requests.update(settings.gpu_resource_requests)
            resources.limits.update(settings.gpu_resource_limits)

        # Container specification
        container = V1Container(
            name="subject-brain-runtime",
            image="subject-brain-runtime:latest",  # Will be built separately
            ports=[{"containerPort": 8080}],
            env=[
                {"name": "LEARNER_ID", "value": runtime_request.learner_id},
                {"name": "SUBJECT", "value": runtime_request.subject.value},
                {"name": "RUNTIME_ID", "value": runtime_request.runtime_id},
                {
                    "name": "ACTIVITY_PLAN",
                    "value": runtime_request.activity_plan.model_dump_json()
                },
                {
                    "name": "MAX_RUNTIME_MINUTES",
                    "value": str(runtime_request.max_runtime_minutes)
                },
            ],
            resources=resources,
            readiness_probe={
                "httpGet": {"path": "/health", "port": 8080},
                "initialDelaySeconds": 10,
                "periodSeconds": 5
            },
            liveness_probe={
                "httpGet": {"path": "/health", "port": 8080},
                "initialDelaySeconds": 30,
                "periodSeconds": 10
            }
        )

        # Pod specification
        pod_spec = V1PodSpec(
            containers=[container],
            service_account_name=self.service_account,
            restart_policy="Never",  # One-time execution
            active_deadline_seconds=runtime_request.max_runtime_minutes * 60,
            termination_grace_period_seconds=30
        )

        # Add node selector for GPU nodes if required
        if runtime_request.gpu_required:
            pod_spec.node_selector = settings.gpu_node_selector

        return pod_spec

    async def get_runtime_status(self, runtime_id: str) -> RuntimePod | None:
        """Get current status of a runtime."""
        if runtime_id not in self.active_runtimes:
            return None

        runtime_pod = self.active_runtimes[runtime_id]

        try:
            # Get pod status from Kubernetes
            pod = self.v1.read_namespaced_pod(
                name=runtime_pod.pod_name,
                namespace=self.namespace
            )

            # Update runtime status
            runtime_pod.status = self._map_pod_status(pod.status.phase)
            runtime_pod.node_name = pod.spec.node_name

            if pod.status.start_time and not runtime_pod.started_at:
                runtime_pod.started_at = pod.status.start_time.replace(
                    tzinfo=None
                )

            # Update metrics
            await self._update_runtime_metrics(runtime_pod)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to get status for runtime %s: %s", runtime_id, e
            )
            runtime_pod.status = RuntimeStatus.TERMINATED

        return runtime_pod

    def _map_pod_status(self, phase: str) -> RuntimeStatus:
        """Map Kubernetes pod phase to runtime status."""
        mapping = {
            "Pending": RuntimeStatus.PENDING,
            "Running": RuntimeStatus.RUNNING,
            "Succeeded": RuntimeStatus.TERMINATED,
            "Failed": RuntimeStatus.TERMINATED,
            "Unknown": RuntimeStatus.TERMINATED
        }
        return mapping.get(phase, RuntimeStatus.TERMINATED)

    async def _update_runtime_metrics(self, runtime_pod: RuntimePod) -> None:
        """Update metrics for a runtime pod."""
        try:
            # In a real implementation, this would query metrics from:
            # - Prometheus/metrics server for CPU/memory
            # - Custom metrics for GPU queue depth
            # - Application metrics for learner activity

            # Simulated metrics for now
            runtime_pod.metrics.last_activity_timestamp = datetime.utcnow()

            # Store metrics history
            if runtime_pod.runtime_id not in self.metrics_history:
                self.metrics_history[runtime_pod.runtime_id] = []

            self.metrics_history[runtime_pod.runtime_id].append(
                runtime_pod.metrics
            )

            # Keep only recent metrics (last hour)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            self.metrics_history[runtime_pod.runtime_id] = [
                m for m in self.metrics_history[runtime_pod.runtime_id]
                if m.last_activity_timestamp > cutoff
            ]

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to update metrics: %s", e)

    async def cleanup_idle_runtimes(self) -> list[str]:
        """Clean up idle runtime pods based on TTL."""
        cleaned_up = []
        current_time = datetime.utcnow()

        for runtime_id, runtime_pod in list(self.active_runtimes.items()):
            # Check if runtime has exceeded TTL
            if runtime_pod.last_activity_at:
                idle_time = current_time - runtime_pod.last_activity_at
                if idle_time.total_seconds() > runtime_pod.ttl_seconds:
                    await self.terminate_runtime(runtime_id)
                    cleaned_up.append(runtime_id)

        return cleaned_up

    async def terminate_runtime(self, runtime_id: str) -> None:
        """Terminate a specific runtime pod."""
        if runtime_id not in self.active_runtimes:
            return

        runtime_pod = self.active_runtimes[runtime_id]

        try:
            # Delete the pod
            self.v1.delete_namespaced_pod(
                name=runtime_pod.pod_name,
                namespace=self.namespace
            )

            # Update status
            runtime_pod.status = RuntimeStatus.TERMINATING

            logger.info("Terminated runtime %s", runtime_id)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to terminate runtime %s: %s", runtime_id, e)

    async def create_hpa(self) -> None:
        """Create Horizontal Pod Autoscaler for the service."""
        if not settings.hpa_enabled:
            return

        hpa_name = "subject-brain-hpa"

        # HPA specification
        hpa = V1HorizontalPodAutoscaler(
            metadata=V1ObjectMeta(
                name=hpa_name,
                namespace=self.namespace
            ),
            spec={
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "subject-brain-svc"
                },
                "minReplicas": settings.hpa_min_replicas,
                "maxReplicas": settings.hpa_max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": (
                                    settings.hpa_target_cpu_utilization
                                )
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": (
                                    settings.hpa_target_memory_utilization
                                )
                            }
                        }
                    },
                    {
                        "type": "Pods",
                        "pods": {
                            "metric": {
                                "name": "gpu_queue_depth"
                            },
                            "target": {
                                "type": "AverageValue",
                                "averageValue": str(
                                    settings.hpa_target_gpu_queue_depth
                                )
                            }
                        }
                    }
                ],
                "behavior": {
                    "scaleUp": {
                        "stabilizationWindowSeconds": (
                            settings.hpa_scale_up_delay_seconds
                        )
                    },
                    "scaleDown": {
                        "stabilizationWindowSeconds": (
                            settings.hpa_scale_down_delay_seconds
                        )
                    }
                }
            }
        )

        try:
            self.autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa
            )
            logger.info("Created HPA %s", hpa_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to create HPA: %s", e)

    async def get_scaling_metrics(self) -> dict[str, Any]:
        """Get current scaling metrics for decision making."""
        total_gpu_queue = sum(
            runtime.metrics.gpu_queue_depth
            for runtime in self.active_runtimes.values()
        )

        avg_cpu = sum(
            runtime.metrics.cpu_utilization_percent
            for runtime in self.active_runtimes.values()
        ) / max(len(self.active_runtimes), 1)

        avg_memory = sum(
            runtime.metrics.memory_usage_mb
            for runtime in self.active_runtimes.values()
        ) / max(len(self.active_runtimes), 1)

        return {
            "active_runtimes": len(self.active_runtimes),
            "total_gpu_queue_depth": total_gpu_queue,
            "average_cpu_utilization": avg_cpu,
            "average_memory_usage_mb": avg_memory,
            "pending_requests": sum(
                runtime.metrics.pending_requests
                for runtime in self.active_runtimes.values()
            )
        }


# Global runtime manager instance
runtime_manager = KubernetesRuntimeManager()
