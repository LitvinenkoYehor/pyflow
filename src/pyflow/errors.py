class WorkflowValidationError(ValueError):
    """Niepoprawna definicja zadania lub workflow."""


class TaskExecutionError(RuntimeError):
    """Zadanie zakończyło się błędem podczas wykonania.

    Oryginalny wyjątek jest dostępny jako ``original`` oraz ``__cause__``.
    """

    def __init__(self, task_name: str, original: BaseException) -> None:
        super().__init__(
            f"Zadanie '{task_name}' zakończyło się błędem: "
            f"{type(original).__name__}: {original}"
        )
        self.task_name = task_name
        self.original = original