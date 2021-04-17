from abc import ABCMeta, abstractmethod

from .abstract_content_type import AbstractContentType


class HttpContentTextHtml(AbstractContentType, metaclass=ABCMeta):
    """
    A mapping to convert between text/html content types

    Mirrors pydantic's `parse_*()` functionality: https://pydantic-docs.helpmanual.io/usage/models/
    """

    @classmethod
    def _from_method(cls):
        return cls.from_http_text_html

    @classmethod
    def _to_method(cls):
        return cls.http_text_html

    @classmethod
    def from_http_text_html(cls, content: str):
        return cls.from_http_text_html(content)

    @abstractmethod
    def http_text_html(self) -> str:
        return self.http_text_html()
