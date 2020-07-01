"""Manage test environments."""

import enum
import os
import subprocess


class EnvironmentState(enum.Enum):

    INACTIVE = "inactive"
    STOPPED = "stopped"
    STARTED = "started"
    STOPPING = "stopping"


class EnvironmentStateError(RuntimeError):
    """Raised when an illegal environment state transition is attempted."""

    def __init__(self, curr_state, requested_state):
        msg = f"cannot transition from ${curr_state} to ${requested_state}"
        super().__init__(msg)


class EnvironmentManager:

    COMPOSE_FILENAME = "docker_compose.yml"

    def __init__(self, directory: str):
        self._compose_path = os.path.join(directory, self.COMPOSE_FILENAME)
        self._proc = None
        if os.path.exists(self._compose_path):
            self.state = EnvironmentState.STOPPED
        else:
            self.state = EnvironmentState.INACTIVE

    def start(self):
        if self.state != EnvironmentState.STOPPED:
            raise EnvironmentStateError(self.state, EnvironmentState.STARTED)
        self._proc = subprocess.Popen(
            ["docker-compose", "-f", self._compose_path, "up"]
        )
        self.state = EnvironmentState.STARTED
        return self

    def stop(self):
        if self.state != EnvironmentState.STOPPING:
            raise EnvironmentStateError(self.state, EnvironmentState.STOPPED)

        subprocess.check_call(["docker-compose", "-f", self._compose_path, "down"])
        self._proc.wait()
        self.state = EnvironmentState.STOPPED

