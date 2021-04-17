from abc import ABCMeta, abstractmethod

from .abstract_content_type import AbstractContentType


class HttpContentTextPlain(AbstractContentType, metaclass=ABCMeta):
    """
    A mapping to convert between text/plain content types

    Mirrors pydantic's `parse_*()` functionality: https://pydantic-docs.helpmanual.io/usage/models/
    """

    @classmethod
    def _from_method(cls):
        return cls.from_http_text_plain

    @classmethod
    def _to_method(cls):
        return cls.http_text_plain

    @classmethod
    def from_http_text_plain(cls, content: str):
        return cls.from_http_text_plain(content)

    @abstractmethod
    def http_text_plain(self) -> str:
        return self.http_text_plain()
