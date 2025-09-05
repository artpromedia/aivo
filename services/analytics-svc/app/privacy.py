"""Differential privacy implementation for analytics."""

import random
from typing import Any


class DifferentialPrivacy:
    """Differential privacy implementation using Laplace noise."""

    def __init__(self, epsilon: float = 1.0, sensitivity: float = 1.0) -> None:
        """
        Initialize differential privacy parameters.

        Args:
            epsilon: Privacy budget parameter (smaller = more private)
            sensitivity: Sensitivity of the query (max change per record)
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.scale = sensitivity / epsilon

    def add_laplace_noise(self, value: float) -> float:
        """Add Laplace noise to a numeric value."""
        # Generate Laplace noise: Lap(0, scale)
        u = random.uniform(-0.5, 0.5)
        noise = -self.scale * (u / abs(u)) * (1 - abs(u))
        return max(0, value + noise)  # Ensure non-negative results

    def add_noise_to_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Add differential privacy noise to metrics dictionary."""
        noisy_metrics = {}

        for key, value in metrics.items():
            if isinstance(value, int | float):
                # Add noise to numeric values
                if isinstance(value, int):
                    noisy_value = int(
                        round(self.add_laplace_noise(float(value)))
                    )
                else:
                    noisy_value = self.add_laplace_noise(value)
                noisy_metrics[key] = max(0, noisy_value)
            else:
                # Keep non-numeric values as-is
                noisy_metrics[key] = value

        return noisy_metrics
