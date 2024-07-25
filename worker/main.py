import logging
import os

from frinx.common.logging import logging_common
from frinx.common.logging.logging_common import LoggerConfig
from frinx.common.logging.logging_common import Root


def register_tasks(conductor_client):
    logging.info('Register tasks')

    def _uniconfig_workers():
        from frinx_worker.uniconfig.uniconfig_manager import UniconfigManager
        from frinx_worker.uniconfig.snapshot_manager import SnapshotManager
        from frinx_worker.uniconfig.connection_manager import ConnectionManager
        from frinx_worker.uniconfig.structured_data import StructuredData
        from frinx_worker.uniconfig.cli_network_topology import CliNetworkTopology

        UniconfigManager().register(conductor_client=conductor_client)
        SnapshotManager().register(conductor_client=conductor_client)
        ConnectionManager().register(conductor_client=conductor_client)
        StructuredData().register(conductor_client=conductor_client)
        CliNetworkTopology().register(conductor_client=conductor_client)

    def _http_workers():
        from frinx_worker.http import HTTPWorkersService
        HTTPWorkersService().register(conductor_client=conductor_client)

    def _inventory_workers():
        from frinx_worker.inventory import InventoryService
        InventoryService().register(conductor_client=conductor_client)

    def _schellar_workers():
        from frinx_worker.schellar import Schellar
        Schellar().register(conductor_client=conductor_client)

    def _conductor_test():
        from frinx_worker.conductor_system_test import TestWorker
        TestWorker().register(conductor_client=conductor_client)

    def _misc_workers():
        from frinx_worker.python_lambda import PythonLambda
        PythonLambda().register(conductor_client=conductor_client)

    _uniconfig_workers()
    _http_workers()
    _inventory_workers()
    _schellar_workers()
    _conductor_test()
    _misc_workers()


def register_workflows():
    logging.info('Register workflows')

    from frinx_worker.inventory.workflows import Inventory
    Inventory().register(overwrite=True)

    from frinx_worker.schellar.workflows.schellar import SchellarWorkflows
    SchellarWorkflows().register(overwrite=True)

    from frinx_worker.http.workflows.post_to_slack import PostToSlackService
    PostToSlackService().register(overwrite=True)

    from frinx_worker.http.workflows.generic import GenericRequestService
    GenericRequestService().register(overwrite=True)

    from frinx_worker.conductor_system_test.workflows import TestWorkflows
    TestWorkflows().register(overwrite=True)

    from l2_vpn_ptp_oc.create_l2vpn_p2p_oc_uniconfig import L2VPNService
    L2VPNService().register(overwrite=True)

    from loopback_interface.loopback_interface_uniconfig import LoopbackInterfaceService
    LoopbackInterfaceService().register(overwrite=True)


def import_devices() -> None:
    from devices.import_devices import import_devices
    import_devices("devices/cli_device_data.csv", "devices/cli_device_import.json")


def import_blueprints() -> None:
    from devices.import_devices import import_blueprints
    import_blueprints("devices/cli_device_import.json")


def main() -> None:

    logging_common.configure_logging(
        LoggerConfig(root=Root(level=os.environ.get('LOG_LEVEL', 'INFO').upper(), handlers=['console']))
    )
    from frinx.common.telemetry.metrics import Metrics
    from frinx.common.telemetry.metrics import MetricsSettings

    Metrics(settings=MetricsSettings(metrics_enabled=True))

    from frinx.client.frinx_conductor_wrapper import FrinxConductorWrapper
    from frinx.common.frinx_rest import CONDUCTOR_HEADERS
    from frinx.common.frinx_rest import CONDUCTOR_URL_BASE

    conductor_client = FrinxConductorWrapper(
        server_url=CONDUCTOR_URL_BASE,
        polling_interval=0.1,
        max_thread_count=50,
        headers=CONDUCTOR_HEADERS,
    )

    register_tasks(conductor_client)
    register_workflows()
    import_devices()
    import_blueprints()
    conductor_client.start_workers()


if __name__ == '__main__':
    main()
