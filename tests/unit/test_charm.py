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
        lambda charm, ports: None,
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
            source="info:\n  version: 1.0.1\n  description: PCF initial local configuration\n\nconfiguration:\n  serviceList:\n    - serviceName: nwebui-am-policy-control\n    - serviceName: nwebui-smpolicycontrol\n      suppFeat: 3fff\n    - serviceName: nwebui-bdtpolicycontrol\n    - serviceName: nwebui-policyauthorization\n      suppFeat: 3\n    - serviceName: nwebui-eventexposure\n    - serviceName: nwebui-ue-policy-control\n\n  sbi:\n    scheme: http\n    registerIPv4: webui-nwebui # IP used to register to NRF\n    bindingIPv4: 0.0.0.0  # IP used to bind the service\n    port: 80\n    tls:\n      key: config/TLS/webui.key\n      pem: config/TLS/webui.pem\n\n  mongodb:       # the mongodb connected by this PCF\n    name: free5gc                  # name of the mongodb\n    url: mongodb://mongodb:27017 # a valid URL of the mongodb\n\n  nrfUri: http://nrf-nnrf:8000\n  webuiName: PCF\n  timeFormat: 2019-01-02 15:04:05\n  defaultBdtRefId: BdtPolicyId-\n  locality: area1\n\nlogger:\n  PCF:\n    ReportCaller: false\n    debugLevel: info",  # noqa: E501
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
                    "command": "webui -c /free5gc/config/webuicfg.yaml",
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
