from pprint import pformat
from typing import Dict, Union


class NotAFieldException(Exception):
    """
    Custom exception class, used when the user attempts to get/set non-existent fields in one of the custom dictionary types which reference one of the spaces defined in the sim's schema/RL experiment.
    """
    def __init__(self, cls: type, valid_names: list[str], attempted_name: str):
        super().__init__(f"'{attempted_name}' not in {cls.__name__} spec; options: {valid_names}")


class ExitException(Exception):
    """
    Custom exception class to throw when the user wants to prematurely exit (e.g., via ctrl-c).
    """
    pass


class ModelError(Exception):
    """
    Custom exception class to provide specific, Alpyne-relevant information when receiving an error from the partner application.
    """
    def __init__(self, status=None, error=None, message=None, path=""):
        self.status = status
        self.error = error

        self.message = message if isinstance(message, str) else (message or bytes()).decode()
        self.path = path

    def __str__(self):
        return f"ModelError[path={self.path}, status={self.status}, error={self.error}, msg={pformat(self.message)}]"

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_json(json_data: Dict[str, Union[str, bytes, None]]):
        return ModelError(
            message=json_data.get("message"),
            status=json_data.get("status"),
            error=json_data.get("error"),
            path=json_data.get("path"))
