from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.logging.root_logger import logger
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
        sum: int

    def execute(self, worker_input: WorkerInput) -> TaskResult[WorkerOutput]:
        result = worker_input.num_a + worker_input.num_b

        logger.info(f"This is an INFO message from the root_logger, result of addition is '{result}'")
        logger.debug("This is a DEBUG message from the root_logger")
        logger.warning("This is a WARNING message from the root_logger")

        return TaskResult(
            status=TaskResultStatus.COMPLETED,
            logs=["SUM worker completed successfully", "You can include some logs here as a list."],
            output=self.WorkerOutput(sum=result)
        )


class DivisionFailureWorker(WorkerImpl):
    class WorkerDefinition(TaskDefinition):
        name: str = "division_failure_worker"
        description: str = "Attempt to divide a number, but intentional failure due to division by zero."
        labels: ListAny = ["TEST"]
        timeout_seconds: int = 60
        response_timeout_seconds: int = 60

    # class ExecutionProperties(TaskExecutionProperties):
    #     pass_task_error_to_task_output: bool = True
    #     pass_task_error_to_task_output_path: str = 'result.error'
    #     transform_string_to_json_valid: bool = True


    class WorkerInput(TaskInput):
        ...

    class WorkerOutput(TaskOutput):
        output: float

    def execute(self, worker_input: WorkerInput) -> TaskResult[WorkerOutput]:

        logger.info("Attempting division by zero for demonstration purposes.")
        x = 42 / 0

        return TaskResult(
            status=TaskResultStatus.COMPLETED,
            logs=["Unexpected success; should not have reached this point :O"],
            output=self.WorkerOutput(output=x)
        )
