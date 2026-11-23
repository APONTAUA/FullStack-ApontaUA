"""Read-only Locust scenarios for an isolated local ApontaUA environment."""

import ipaddress
import os
from urllib.parse import urlsplit

from locust import HttpUser, LoadTestShape, between, events, task

BASE_URL = os.getenv("PERF_BASE_URL", "http://127.0.0.1:8000")


def _require_local_isolated_target(host: str | None) -> None:
    if os.getenv("PERF_ENVIRONMENT") != "isolated-local":
        raise RuntimeError(
            "Set PERF_ENVIRONMENT=isolated-local only after creating a disposable test stack"
        )

    parsed = urlsplit(host or BASE_URL)
    if parsed.scheme != "http" or not parsed.hostname:
        raise RuntimeError("Performance tests require a local HTTP URL")
    try:
        local_host = parsed.hostname == "localhost" or ipaddress.ip_address(
            parsed.hostname
        ).is_loopback
    except ValueError:
        local_host = False
    if not local_host:
        raise RuntimeError("Performance tests are restricted to localhost/loopback targets")


@events.init.add_listener
def validate_target(environment, **_kwargs) -> None:
    _require_local_isolated_target(environment.host)


class ApontaUAUser(HttpUser):
    host = BASE_URL
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        # The development-only role enables the implemented read-only course listing.
        self.client.headers.update({"X-Dev-Role": "estudante"})

    @task(5)
    def liveness(self) -> None:
        self.client.get("/api/v1/health/live", name="GET /health/live")

    @task(2)
    def readiness(self) -> None:
        self.client.get("/api/v1/health/ready", name="GET /health/ready")

    @task(3)
    def list_courses(self) -> None:
        self.client.get("/api/v1/cursos", name="GET /cursos")


class LocalConcurrencyShape(LoadTestShape):
    """Three measured stages; these are load levels, not performance targets."""

    stages = ((30, 1), (60, 5), (90, 10))

    def tick(self) -> tuple[int, float] | None:
        run_time = self.get_run_time()
        for duration, users in self.stages:
            if run_time < duration:
                return users, 1
        return None
