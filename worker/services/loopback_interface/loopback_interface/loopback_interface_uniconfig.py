import json

from frinx.common.frinx_rest import UNICONFIG_URL_BASE
from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import DoWhileTask
from frinx.common.workflow.task import DynamicForkTask
from frinx.common.workflow.task import DynamicForkTaskInputParameters
from frinx.common.workflow.task import JoinTask
from frinx.common.workflow.task import JsonJqTask
from frinx.common.workflow.task import JsonJqTaskInputParameters
from frinx.common.workflow.task import LambdaTask
from frinx.common.workflow.task import LambdaTaskInputParameters
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx_worker.inventory import InventoryService
from frinx_worker.uniconfig.structured_data import StructuredData
from frinx_worker.uniconfig.uniconfig_manager import UniconfigManager


class LoopbackInterfaceService(ServiceWorkflowsImpl):
    class CreateLoopbackInterface(WorkflowImpl):
        name: str = "Create_loopback_interface_uniconfig"
        version: int = 1
        description: str = "Create loopback interface on device via uniconfig controller"
        labels: list[str] = ["DEMO", "INTERFACES", "UNICONFIG", "OPENCONFIG"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_id: WorkflowInputField = WorkflowInputField(
                name="device_id",
                frontend_default_value=None,
                description="Unique device identifier. Example: IOS01",
                type=FrontendWFInputFieldType.STRING,
            )

            loopback_id: WorkflowInputField = WorkflowInputField(
                name="loopback_id",
                frontend_default_value=None,
                description="Unique loopback identifier (e.g. 77)",
                type=FrontendWFInputFieldType.STRING,
            )

            uniconfig_url_base: WorkflowInputField = WorkflowInputField(
                name="uniconfig_url_base",
                frontend_default_value=UNICONFIG_URL_BASE,
                description="Uniconfig zone url",
                type=FrontendWFInputFieldType.STRING,
            )

            uniconfig_server_id: WorkflowInputField = WorkflowInputField(
                name="uniconfig_server_id",
                frontend_default_value=None,
                description="Uniconfig zone url",
                type=FrontendWFInputFieldType.STRING,
            )

            transaction_id: WorkflowInputField = WorkflowInputField(
                name="transaction_id",
                frontend_default_value=None,
                description="Uniconfig transaction id",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            response_body: str

        @staticmethod
        def _template(loopback_id: str | None) -> str:
            template = {
                "interface": [
                    {
                        "name": f"Loopback{loopback_id}",
                        "config": {
                            "type": "iana-if-type:softwareLoopback",
                            "enabled": False,
                            "name": f"Loopback{loopback_id}",
                        },
                    }
                ]
            }

            return json.dumps(template, indent=4).replace('"', '"').replace("\n", "\r\n")

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            write_loopback = SimpleTask(
                name=StructuredData.WriteStructuredData,
                task_reference_name="UNICONFIG_write_structured_device_data",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        node_id=workflow_inputs.device_id.wf_input,
                        uri=f"/frinx-openconfig-interfaces:interfaces/interface=Loopback{workflow_inputs.loopback_id.wf_input}",
                        template=self._template(loopback_id=workflow_inputs.loopback_id.wf_input),
                        method="PUT",
                        uniconfig_url_base=workflow_inputs.uniconfig_url_base.wf_input,
                        uniconfig_server_id=workflow_inputs.uniconfig_server_id.wf_input,
                        transaction_id=workflow_inputs.transaction_id.wf_input,
                    )
                ),
            )

            self.tasks = [write_loopback]

    class CreateLoopbackAllInUniconfig(WorkflowImpl):
        name: str = "Create_loopback_all_in_uniconfig"
        version: int = 1
        description: str = "Create loopback interface for all devices in uniconfig topology"
        labels: list[str] = ["DEMO", "INTERFACES", "UNICONFIG", "OPENCONFIG"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            labels: WorkflowInputField = WorkflowInputField(
                name="labels",
                frontend_default_value=None,
                description="Device labels. Example: CLI",
                type=FrontendWFInputFieldType.STRING,
            )

            loopback_id: WorkflowInputField = WorkflowInputField(
                name="loopback_id",
                frontend_default_value=None,
                description="Loopback identifier (e.g. 77)",
                type=FrontendWFInputFieldType.STRING,
            )

            zone: WorkflowInputField = WorkflowInputField(
                name="zone",
                frontend_default_value=UNICONFIG_URL_BASE,
                description="Uniconfig zone",
                type=FrontendWFInputFieldType.STRING,
            )

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            tx_start = SimpleTask(
                name=UniconfigManager.CreateTransaction,
                task_reference_name="tx_start",
                input_parameters=SimpleTaskInputParameters(root=dict(uniconfig_url_base=workflow_inputs.zone.wf_input)),
            )

            commit_tx = SimpleTask(
                name=UniconfigManager.CommitTransaction,
                task_reference_name="tx_commit",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        uniconfig_url_base=tx_start.output_ref("uniconfig_url_base"),
                        uniconfig_server_id=tx_start.output_ref("uniconfig_server_id"),
                        transaction_id=tx_start.output_ref("transaction_id"),
                    )
                ),
            )

            get_labels = SimpleTask(
                name=InventoryService.InventoryGetLabelsId,
                task_reference_name="get_labels",
                input_parameters=SimpleTaskInputParameters(root=dict(labels=workflow_inputs.labels.wf_input)),
            )

            get_pages_cursors = SimpleTask(
                name=InventoryService.InventoryGetPagesCursors,
                task_reference_name="get_pages_cursors",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(labels=get_labels.output_ref("labels_id"), cursor_step=10, cursors_per_group=1)
                ),
            )

            convert_to_string = LambdaTask(
                name="convert_to_string",
                task_reference_name="convert_to_string",
                input_parameters=LambdaTaskInputParameters(
                    lambdaValue=get_pages_cursors.output_ref("cursors_groups"),
                    script_expression='return $.lambdaValue["loop_"+($.iterator-1).toString()]',
                    iterator="${loop_device_pages.output.iteration}",
                ),
            )

            get_pages_cursors_fork_task = SimpleTask(
                name=InventoryService.InventorySubWorkflowForkFormat,
                task_reference_name="get_pages_cursors_fork_task",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        task="Create_loopback_interface_uniconfig",
                        cursors_groups=convert_to_string.output_ref("result"),
                        task_input=dict(
                            loopback_id=workflow_inputs.loopback_id.wf_input,
                            uniconfig_url_base=tx_start.output_ref("uniconfig_url_base"),
                            uniconfig_server_id=tx_start.output_ref("uniconfig_server_id"),
                            transaction_id=tx_start.output_ref("transaction_id"),
                        ),
                    )
                ),
            )

            fork = DynamicForkTask(
                name="dyn_fork",
                task_reference_name="dyn_fork",
                dynamic_fork_tasks_param="dynamic_tasks",
                dynamic_fork_tasks_input_param_name="dynamic_tasks_input",
                input_parameters=DynamicForkTaskInputParameters(
                    dynamic_tasks=get_pages_cursors_fork_task.output_ref("dynamic_tasks"),
                    dynamic_tasks_input=get_pages_cursors_fork_task.output_ref("dynamic_tasks_input"),
                ),
            )

            join = JoinTask(name="join", task_reference_name="join")

            loop_task = DoWhileTask(
                name="loop_device_pages",
                task_reference_name="loop_device_pages",
                input_parameters=dict(value=get_pages_cursors.output_ref("number_of_groups")),
                loop_condition="if ( $.loop_device_pages['iteration'] < $.value ) { true; } else { false; }",
                loop_over=[tx_start, convert_to_string, get_pages_cursors_fork_task, fork, join, commit_tx],
            )

            join_results = JsonJqTask(
                name="join_results",
                task_reference_name="join_results",
                input_parameters=JsonJqTaskInputParameters(
                    query_expression="{output: .data[]|iterables|.join}", data=loop_task.output_ref()
                ),
            )

            self.tasks = [get_labels, get_pages_cursors, loop_task, join_results]
