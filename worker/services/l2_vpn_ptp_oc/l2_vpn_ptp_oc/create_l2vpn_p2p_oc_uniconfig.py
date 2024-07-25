import json

from frinx.common.frinx_rest import UNICONFIG_URL_BASE
from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import DecisionCaseValueTask
from frinx.common.workflow.task import DecisionCaseValueTaskInputParameters
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.task import SubWorkflowFromDefParam
from frinx.common.workflow.task import SubWorkflowInputParameters
from frinx.common.workflow.task import SubWorkflowTask
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx_worker.http.workflows.post_to_slack import PostToSlackService
from frinx_worker.uniconfig.structured_data import StructuredData
from frinx_worker.uniconfig.uniconfig_manager import UniconfigManager


class L2VPNService(ServiceWorkflowsImpl):
    class L2VPN(WorkflowImpl):
        name: str = "Create_L2VPN_P2P_OC_uniconfig"
        version: int = 1
        description: str = "Create P2P L2VPN in uniconfig"
        labels: list[str] = ["DEMO", "L2VPN"]
        failure_workflow: str = "UC_TX_rollback"

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            node01: WorkflowInputField = WorkflowInputField(
                name="node01",
                frontend_default_value="IOS01",
                description="First node of P2P connection",
                type=FrontendWFInputFieldType.STRING,
            )

            node02: WorkflowInputField = WorkflowInputField(
                name="node02",
                frontend_default_value="IOS02",
                description="Second node of P2P connection",
                type=FrontendWFInputFieldType.STRING,
            )

            interface01: WorkflowInputField = WorkflowInputField(
                name="interface01",
                frontend_default_value="GigabitEthernet1",
                description="Customer facing service interface on first node",
                type=FrontendWFInputFieldType.STRING,
            )

            interface02: WorkflowInputField = WorkflowInputField(
                name="interface02",
                frontend_default_value="GigabitEthernet1",
                description="Customer facing service interface on second node",
                type=FrontendWFInputFieldType.STRING,
            )

            vcid: WorkflowInputField = WorkflowInputField(
                name="vcid",
                frontend_default_value="444",
                description="Virtual Circuit Identifier (globally unique)",
                type=FrontendWFInputFieldType.STRING,
            )

            zone: WorkflowInputField = WorkflowInputField(
                name="zone",
                frontend_default_value=UNICONFIG_URL_BASE,
                description="Uniconfig zone",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            response_body: str

        @staticmethod
        def _template(interface: str | None = "", remote_system: str | None = "") -> str:
            l2vpn_template = {
                "frinx-openconfig-network-instance:network-instance": [
                    {
                        "name": "conn1233",
                        "config": {"name": "conn1233", "type": "frinx-openconfig-network-instance-types:L2P2P"},
                        "connection-points": {
                            "connection-point": [
                                {
                                    "connection-point-id": "1",
                                    "config": {"connection-point-id": "1"},
                                    "endpoints": {
                                        "endpoint": [
                                            {
                                                "endpoint-id": "default",
                                                "config": {
                                                    "endpoint-id": "default",
                                                    "precedence": 0,
                                                    "type": "frinx-openconfig-network-instance-types:LOCAL",
                                                },
                                                "local": {"config": {"interface": interface}},
                                            }
                                        ]
                                    },
                                },
                                {
                                    "connection-point-id": "2",
                                    "config": {"connection-point-id": "2"},
                                    "endpoints": {
                                        "endpoint": [
                                            {
                                                "endpoint-id": "default",
                                                "config": {
                                                    "endpoint-id": "default",
                                                    "precedence": 0,
                                                    "type": "frinx-openconfig-network-instance-types:REMOTE",
                                                },
                                                "remote": {
                                                    "config": {
                                                        "remote-system": remote_system,
                                                        "virtual-circuit-identifier": "${workflow.input.vcid}",
                                                    }
                                                },
                                            }
                                        ]
                                    },
                                },
                            ]
                        },
                    }
                ]
            }
            return json.dumps(l2vpn_template, indent=4).replace('"', '"').replace("\n", "\r\n")

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            tx_start_1 = SimpleTask(
                name=UniconfigManager.CreateTransaction,
                task_reference_name="tx_start_1",
                input_parameters=SimpleTaskInputParameters(root=dict(uniconfig_url_base=workflow_inputs.zone.wf_input)),
            )

            uniconfig_sync_from_network = SimpleTask(
                name=UniconfigManager.SyncFromNetwork,
                task_reference_name="uniconfig_sync_from_network",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        node_ids=[workflow_inputs.node01.wf_input, workflow_inputs.node02.wf_input],
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                        uniconfig_server_id=tx_start_1.output_ref("uniconfig_server_id"),
                        uniconfig_url_base=workflow_inputs.zone.wf_input,
                    )
                ),
            )

            uniconfig_replace_config_with_oper = SimpleTask(
                name=UniconfigManager.ReplaceConfigWithOperational,
                task_reference_name="uniconfig_replace_config_with_oper",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        node_ids=[workflow_inputs.node01.wf_input, workflow_inputs.node02.wf_input],
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                    )
                ),
            )

            write_structured_device_data_on_first_node = SimpleTask(
                name=StructuredData.WriteStructuredData,
                task_reference_name="UNICONFIG_write_structured_device_data_on_first_node",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        node_id=workflow_inputs.node01.wf_input,
                        uri="/frinx-openconfig-network-instance:network-instances/network-instance=conn1233",
                        template=self._template(
                            interface=workflow_inputs.interface01.wf_input, remote_system="10.1.1.1"
                        ),
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                        uniconfig_server_id=tx_start_1.output_ref("uniconfig_server_id"),
                        uniconfig_url_base=workflow_inputs.zone.wf_input,
                    )
                ),
            )

            write_structured_device_data_on_second_node = SimpleTask(
                name=StructuredData.WriteStructuredData,
                task_reference_name="UNICONFIG_write_structured_device_data_on_second_node",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        node_id=workflow_inputs.node02.wf_input,
                        uri="/frinx-openconfig-network-instance:network-instances/network-instance=conn1233",
                        template=self._template(
                            interface=workflow_inputs.interface02.wf_input, remote_system="10.2.2.2"
                        ),
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                        uniconfig_server_id=tx_start_1.output_ref("uniconfig_server_id"),
                        uniconfig_url_base=workflow_inputs.zone.wf_input,
                    )
                ),
            )

            dry_run_commit = SimpleTask(
                name=UniconfigManager.DryRunCommit,
                task_reference_name="UNICONFIG_dry_run_commit",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                        uniconfig_server_id=tx_start_1.output_ref("uniconfig_server_id"),
                        uniconfig_url_base=workflow_inputs.zone.wf_input,
                    )
                ),
            )

            commit = SimpleTask(
                name=UniconfigManager.CommitTransaction,
                task_reference_name="UNICONFIG_commit",
                input_parameters=SimpleTaskInputParameters(
                    root=dict(
                        transaction_id=tx_start_1.output_ref("transaction_id"),
                        uniconfig_server_id=tx_start_1.output_ref("uniconfig_server_id"),
                        uniconfig_url_base=workflow_inputs.zone.wf_input,
                    )
                ),
            )

            # TODO improve error handling in commit and make decision based on this error
            post_to_slack_decision = DecisionCaseValueTask(
                name="slack_decision",
                task_reference_name="slack_decision",
                decision_cases=dict(
                    error=[
                        SubWorkflowTask(
                            name="Post_to_Slack",
                            task_reference_name="post_to_slack_completed",
                            input_parameters=SubWorkflowInputParameters(
                                root=dict(
                                    slack_webhook_id="T02BFFVUQ/B04MQ2PRWQ1/xw9pWOAm0e4OMPfPxmrI1Jbp",
                                    message_text=commit.output_ref("output.errors"),
                                )
                            ),
                            sub_workflow_param=SubWorkflowFromDefParam(
                                name=PostToSlackService.PostToSlackV1,
                            ),
                        )
                    ],
                ),
                default_case=[
                    SubWorkflowTask(
                        name="Post_to_Slack",
                        task_reference_name="post_to_slack_failed",
                        input_parameters=SubWorkflowInputParameters(
                            root=dict(
                                slack_webhook_id="T02BFFVUQ/B04MQ2PRWQ1/xw9pWOAm0e4OMPfPxmrI1Jbp",
                                message_text="Configuration attempt succeeded!",
                            )
                        ),
                        sub_workflow_param=SubWorkflowFromDefParam(
                            name=PostToSlackService.PostToSlackV1,
                        ),
                    )
                ],
                input_parameters=DecisionCaseValueTaskInputParameters(
                    case_value_param=commit.output_ref("output.errors")
                ),
            )

            self.tasks = [
                tx_start_1,
                uniconfig_sync_from_network,
                uniconfig_replace_config_with_oper,
                write_structured_device_data_on_first_node,
                write_structured_device_data_on_second_node,
                dry_run_commit,
                commit,
                post_to_slack_decision,
            ]
