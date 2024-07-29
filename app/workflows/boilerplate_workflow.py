from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.type_aliases import ListStr
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField

from app.workers.boilerplate_worker import SumWorker


class SumWorkflow(WorkflowImpl):
    name: str = "Sum_numbers"
    version: int = 1
    description: str = "Sum 2 int numbers together"
    labels: ListStr = ["TEST"]
    timeout_seconds: int = 60 * 5
    timeout_policy: TimeoutPolicy = TimeoutPolicy.TIME_OUT_WORKFLOW

    class WorkflowInput(WorkflowImpl.WorkflowInput):
        num_a: WorkflowInputField = WorkflowInputField(
            name="num_a",
            frontend_default_value=5,
            description="Number A",
            type=FrontendWFInputFieldType.INT,
        )

        num_b: WorkflowInputField = WorkflowInputField(
            name="num_b",
            frontend_default_value=3,
            description="Number B",
            type=FrontendWFInputFieldType.INT,
        )

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        sum: str

    def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:

        sum_task = SimpleTask(
            name=SumWorker,
            task_reference_name="sum",
            input_parameters=SimpleTaskInputParameters(
                root=dict(
                    num_a=workflow_inputs.num_a.wf_input,
                    num_b=workflow_inputs.num_b.wf_input
                )
            )
        )
        self.tasks = [
            sum_task
        ]

        self.output_parameters = self.WorkflowOutput(
            sum=sum_task.output_ref("sum")
        )
