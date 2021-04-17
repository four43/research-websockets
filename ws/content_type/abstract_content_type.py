import re
from abc import ABCMeta, abstractmethod
from typing import Optional, Type


class AbstractContentType(metaclass=ABCMeta):
    """
    A mapping to convert between content types

    Mirrors pydantic's `parse_*()` functionality: https://pydantic-docs.helpmanual.io/usage/models/
    """

    @classmethod
    def from_example_docstring(cls) -> Optional[str]:
        doc_string = getattr(cls, cls._from_method().__name__).__doc__
        breakpoint()

    @classmethod
    def to_example_docstring(cls, concrete_type: Type['AbstractContentType']) -> Optional[str]:
        doc_string = getattr(concrete_type, cls._to_method().__name__).__doc__
        if doc_string is not None:
            doc_text_matches = re.search(r"FastAPI Example Response:\n(.+)\n\n?", doc_string)
            if doc_text_matches is not None:
                return doc_text_matches.group(1).strip()

    @classmethod
    @abstractmethod
    def _from_method(cls):
        pass

    @classmethod
    @abstractmethod
    def _to_method(cls):
        pass
