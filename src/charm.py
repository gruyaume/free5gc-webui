#!/usr/bin/env python3
# Copyright 2022 Guillaume Belanger
# See LICENSE file for licensing details.

"""Charmed operator for the free5gc WEBUI service."""

import logging

from charms.observability_libs.v1.kubernetes_service_patch import KubernetesServicePatch
from jinja2 import Environment, FileSystemLoader
from lightkube.models.core_v1 import ServicePort
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)

BASE_CONFIG_PATH = "/free5gc/config"
CONFIG_FILE_NAME = "webuicfg.yaml"


class Free5GcWebUIOperatorCharm(CharmBase):
    """Main class to describe juju event handling for the free5gc webui operator."""

    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = self._service_name = "free5gc-webui"
        self._container = self.unit.get_container(self._container_name)
        self.framework.observe(
            self.on.free5gc_webui_pebble_ready, self._on_free5gc_webui_pebble_ready
        )
        self.framework.observe(self.on.install, self._on_install)
        self._service_patcher = KubernetesServicePatch(
            charm=self,
            ports=[ServicePort(name="http", port=5000)],
            service_type="LoadBalancer",
        )

    def _on_install(self, event):
        if not self._container.can_connect():
            self.unit.status = WaitingStatus("Waiting for container to be ready")
            event.defer()
            return
        self._write_config_file()

    def _write_config_file(self) -> None:
        jinja2_environment = Environment(loader=FileSystemLoader("src/templates/"))
        template = jinja2_environment.get_template("webuicfg.yaml.j2")
        content = template.render()
        self._container.push(path=f"{BASE_CONFIG_PATH}/{CONFIG_FILE_NAME}", source=content)
        logger.info(f"Pushed {CONFIG_FILE_NAME} config file")

    @property
    def _config_file_is_written(self) -> bool:
        if not self._container.exists(f"{BASE_CONFIG_PATH}/{CONFIG_FILE_NAME}"):
            logger.info(f"Config file is not written: {CONFIG_FILE_NAME}")
            return False
        logger.info("Config file is written")
        return True

    def _on_free5gc_webui_pebble_ready(self, event) -> None:
        if not self._container.can_connect():
            self.unit.status = WaitingStatus("Waiting for container to be ready")
            event.defer()
            return
        if not self._config_file_is_written:
            self.unit.status = WaitingStatus("Waiting for config file to be written")
            event.defer()
            return
        self._container.add_layer("free5gc-webui", self._pebble_layer, combine=True)
        self._container.replan()
        self.unit.status = ActiveStatus()

    @property
    def _pebble_layer(self) -> Layer:
        """Returns pebble layer for the charm.

        Returns:
            Layer: Pebble Layer
        """
        return Layer(
            {
                "summary": "free5gc-webui layer",
                "description": "pebble config layer for free5gc-webui",
                "services": {
                    "free5gc-webui": {
                        "override": "replace",
                        "startup": "enabled",
                        "command": "/free5gc/webconsole/webconsole -c /free5gc/config/webuicfg.yaml",
                        "environment": self._environment_variables,
                    },
                },
            }
        )

    @property
    def _environment_variables(self) -> dict:
        return {"GIN_MODE": "release"}


if __name__ == "__main__":
    main(Free5GcWebUIOperatorCharm)
