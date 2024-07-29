from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.type_aliases import ListAny
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl


class SumWorker(WorkerImpl):
    class WorkerDefinition(TaskDefinition):
        name: str = "SUM_int"
        description: str = "Sum two numbers together"
        labels: ListAny = ["TEST"]
        timeout_seconds: int = 60
        response_timeout_seconds: int = 60

    class WorkerInput(TaskInput):
        num_a: int
        num_b: int

    class WorkerOutput(TaskOutput):
        output: int

    def execute(self, worker_input: WorkerInput) -> TaskResult[WorkerOutput]:
        result = worker_input.num_a + worker_input.num_b

        return TaskResult(
            status=TaskResultStatus.COMPLETED,
            logs=["SUM worker invoked successfully"],
            output=self.WorkerOutput(output=result)
        )
