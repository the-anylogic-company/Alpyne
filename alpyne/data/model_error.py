from pprint import pformat
from typing import Dict, Union


class ModelError(Exception):
    """
    Custom exception class to provide specific, Alpyne-relevant information.
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