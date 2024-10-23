import argparse
import logging
import pathlib

from dotenv import load_dotenv
from frinx.client.frinx_conductor_wrapper import FrinxConductorWrapper
from frinx.common.logging.config import LoggerConfig


def register_tasks(conductor_client: FrinxConductorWrapper) -> None:
    logging.info("Register tasks")

    from frinx_worker.uniconfig.cli_network_topology import CliNetworkTopology
    from frinx_worker.uniconfig.connection_manager import ConnectionManager
    from frinx_worker.uniconfig.snapshot_manager import SnapshotManager
    from frinx_worker.uniconfig.structured_data import StructuredData
    from frinx_worker.uniconfig.uniconfig_manager import UniconfigManager

    from app.workers.boilerplate_worker import SumWorker

    SumWorker().register(conductor_client=conductor_client)

    UniconfigManager().register(conductor_client=conductor_client)
    SnapshotManager().register(conductor_client=conductor_client)
    ConnectionManager().register(conductor_client=conductor_client)
    StructuredData().register(conductor_client=conductor_client)
    CliNetworkTopology().register(conductor_client=conductor_client)


def register_workflows() -> None:
    logging.info("Register workflows")

    from app.workflows.boilerplate_workflow import SumWorkflow
    from app.workflows.uniconfig_wfs import UcWorkflows

    SumWorkflow().register(overwrite=True)
    UcWorkflows().register(overwrite=True)

def main(env_file_path: pathlib.Path | None = None) -> None:
    LoggerConfig().setup_logging()

    if env_file_path and env_file_path.exists():
        load_dotenv(env_file_path)

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
    conductor_client.start_workers()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env_file",
        nargs="?",
        type=pathlib.Path,
        help="Path to environment file. When not set, default values are used.",
    )
    args = parser.parse_args()
    main(args.env_file)
