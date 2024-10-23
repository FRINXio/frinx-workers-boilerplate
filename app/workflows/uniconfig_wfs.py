from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.type_aliases import ListStr
from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import InlineTask
from frinx.common.workflow.task import InlineTaskInputParameters
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx_worker.uniconfig.device_discovery import DeviceDiscoveryWorkers
from frinx_worker.uniconfig.uniconfig_manager import UniconfigManager


class UcWorkflows(ServiceWorkflowsImpl):
    class CreateTransaction(WorkflowImpl):
        name: str = "Create_transaction"
        version: int = 1
        description: str = "Create a new UC transaction."
        labels: ListStr = ["TEST"]
        timeout_seconds: int = 60 * 5
        timeout_policy: TimeoutPolicy = TimeoutPolicy.TIME_OUT_WORKFLOW

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            transaction_timeout: WorkflowInputField = WorkflowInputField(
                name="transaction_timeout",
                frontend_default_value=50,
                description="Transaction timeout value for UC transaction.",
                type=FrontendWFInputFieldType.INT,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            transaction_id: str
            calculated_timeout: str

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            calculate_double_timeout = InlineTask(
                name="CalculateDoubleTimeout",
                task_reference_name="double_timeout_task",
                input_parameters=InlineTaskInputParameters(
                    expression="return ($.value * 2)",
                    value=workflow_inputs.transaction_timeout.wf_input
                ))

            create_uc_transaction = SimpleTask(
                name=UniconfigManager.CreateTransaction,
                task_reference_name="create_uc_transaction",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        transaction_timeout=calculate_double_timeout.output_ref("result"),
                    )
                )
            )

            self.tasks = [
                calculate_double_timeout,
                create_uc_transaction
            ]

            self.output_parameters = self.WorkflowOutput(
                transaction_id=create_uc_transaction.output_ref("transaction_id"),
                calculated_timeout=calculate_double_timeout.output_ref("result"))

    class DeviceDiscoveryWorkflow(WorkflowImpl):
        name: str = "Device_discovery"
        version: int = 1
        description: str = "Discover devices from ip address range and make a list of reachable ip addresses."
        labels: list[str] = ["DISCOVERY", "UNICONFIG"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            ip: WorkflowInputField = WorkflowInputField(
                name="ip",
                frontend_default_value=" ",
                description="Allowed formats as range: '192.168.0.10-192.168.0.50', "
                            "single ip: '192.168.0.25' or as network '192.168.0.0/24'",
                type=FrontendWFInputFieldType.STRING,
            )

            tcp_ports: WorkflowInputField = WorkflowInputField(
                name="tcp_ports",
                frontend_default_value=" ",
                description="Allowed formats as range: '1-65535' or as list '22, 23, 830'",
                type=FrontendWFInputFieldType.STRING,
            )

            udp_ports: WorkflowInputField = WorkflowInputField(
                name="udp_ports",
                frontend_default_value=" ",
                description="Allowed formats as range: '1-65535' or as list '22, 830'",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            ...

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            device_discovery = SimpleTask(
                name=DeviceDiscoveryWorkers.DeviceDiscoveryWorker,
                task_reference_name="device_discovery",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        ip=workflow_inputs.ip.wf_input,
                        tcp_port=workflow_inputs.tcp_ports.wf_input,
                        udp_port=workflow_inputs.udp_ports.wf_input
                    )
                )
            )

            self.tasks = [
                device_discovery,
            ]
