# Copyright 2022 Guillaume Belanger
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

from ops import testing
from ops.model import ActiveStatus

from charm import Free5GcWebUIOperatorCharm

testing.SIMULATE_CAN_CONNECT = True


class TestCharm(unittest.TestCase):
    @patch(
        "charm.KubernetesServicePatch",
        lambda charm, ports, service_type: None,
    )
    def setUp(self):
        self.harness = testing.Harness(Free5GcWebUIOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @patch("ops.model.Container.push")
    def test_given_can_connect_to_workload_container_when_on_install_then_config_file_is_written(
        self, patch_push
    ):
        self.harness.set_can_connect(container="free5gc-webui", val=True)

        self.harness.charm.on.install.emit()

        patch_push.assert_called_with(
            path="/free5gc/config/webuicfg.yaml",
            source="info:\n  version: 1.0.0\n  description: WEBUI initial local configuration\n\nconfiguration:\n  mongodb:\n    name: free5gc\n    url: mongodb://mongodb:27017\n\nlogger:\n  WEBUI:\n    ReportCaller: false\n    debugLevel: info",  # noqa: E501
        )

    @patch("ops.model.Container.exists")
    def test_given_config_file_is_written_when_pebble_ready_then_pebble_plan_is_applied(
        self, patch_exists
    ):
        patch_exists.return_value = True

        expected_plan = {
            "services": {
                "free5gc-webui": {
                    "override": "replace",
                    "command": "/free5gc/webconsole/webconsole -c /free5gc/config/webuicfg.yaml",
                    "startup": "enabled",
                    "environment": {"GIN_MODE": "release"},
                }
            },
        }
        self.harness.container_pebble_ready("free5gc-webui")
        updated_plan = self.harness.get_container_pebble_plan("free5gc-webui").to_dict()

        self.assertEqual(expected_plan, updated_plan)

    @patch("ops.model.Container.exists")
    def test_given_config_file_is_written_when_pebble_ready_then_status_is_active(
        self, patch_exists
    ):
        patch_exists.return_value = True

        self.harness.container_pebble_ready("free5gc-webui")

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
