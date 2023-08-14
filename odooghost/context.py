from pathlib import Path

import docker
import yaml
from docker.errors import APIError, NotFound

from odooghost import constant, exceptions


class Context:
    """
    Context holds contextual data for OdooGhost
    """

    def __init__(self) -> None:
        self._app_dir = constant.APP_DIR
        self._config_path = self._app_dir / "config.yml"
        self._data_dir = self._app_dir / "data"
        self._plugins_dir = self._app_dir / "plugins"
        self._docker_client = None

    def check_setup_state(self) -> bool:
        """
        Check setup status

        Returns:
            bool
        """
        return self._app_dir.exists()

    def setup(self, version: str, working_dir: Path) -> None:
        """
        Setup OdooGhost

        Args:
            version (str): OdooGhost version
            working_dir (Path): working directory

        Raises:
            exceptions.ContextAlreadySetupError: Already setup
        """
        if self.check_setup_state():
            raise exceptions.ContextAlreadySetupError("App already setup !")

        # TODO handle OSError
        for _dir in (self._app_dir, self._data_dir, self._plugins_dir):
            _dir.mkdir()
        config_data = dict(
            version=version, working_dir=working_dir.resolve().as_posix()
        )
        with open(self._config_path.as_posix(), "w") as stream:
            yaml.dump(config_data, stream=stream)

    def create_common_network(self) -> None:
        """
        Create common Docker network for stacks

        Raises:
            exceptions.CommonNetworkEnsureError: When create fail
        """
        try:
            self.docker.networks.create(
                name=constant.COMMON_NETWORK_NAME,
                driver="bridge",
                check_duplicate=True,
                attachable=True,
                scope="local",
            )
        except APIError:
            raise exceptions.CommonNetworkEnsureError("Failed to create common network")

    def ensure_common_network(self) -> None:
        """
        Ensure common Docker network

        Raises:
            exceptions.CommonNetworkEnsureError: When ensure fail
        """
        try:
            self.docker.networks.get(constant.COMMON_NETWORK_NAME)
        except NotFound:
            self.create_common_network()
        except APIError:
            raise exceptions.CommonNetworkEnsureError("Failed to ensure common network")

    @property
    def docker(self) -> "docker.DockerClient":
        """
        Lazyily return Docker client

        Returns:
            docker.DockerClient: Docker client instance
        """
        if not self._docker_client:
            self._docker_client = docker.from_env()
        return self._docker_client


ctx = Context()
