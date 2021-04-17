import random
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel

from ws.content_type.text_html import HttpContentTextHtml
from ws.content_type.text_plain import HttpContentTextPlain


class ThingColor(Enum):
    """
    An plain english representation of a color for our thing
    """
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    BLACK = "black"
    ORANGE = "orange"
    PURPLE = "purple"


class ThingType(Enum):
    """
    What type of thing we have
    """
    CAR = "car"
    DOG = "dog"
    HOUSE = "house"
    SIGN = "sign"
    BIKE = "bike"


class Thing(BaseModel, HttpContentTextPlain, HttpContentTextHtml):
    id: str
    color: ThingColor
    type: ThingType
    created: datetime

    def http_text_plain(self) -> str:
        """
        Outputs plain text for the resource

        FastAPI Example Response:
            Thing a which is a green car created at 2021-04-17T15:01:14.498166+00:00.

        Other documentation...
        """
        return f"Thing {self.id} which is a {self.color.value} {self.type.value} created at {self.created.isoformat()}."

    @classmethod
    def from_http_text_plain(cls, content: str):
        raise NotImplementedError("Creating this object via text/plain content-type isn't available.")

    def http_text_html(self) -> str:
        """
        Outputs the in Thing as an HTML summary

        FastAPI Example Response:
            <html><body><h1>Thing a which is a <span style="color:purple">purple dog</span> created at 2021-04-17T15:09:55.941456+00:00.</body></html>
        """
        return f"<html><body>" \
               f"<h1>Thing {self.id} which is a " \
               f"<span style=\"color:{self.color.value}\">{self.color.value} {self.type.value}</span> " \
               f"created at {self.created.isoformat()}." \
               f"</body></html>"

    @classmethod
    def from_http_text_plain(cls, content: str):
        raise NotImplementedError("Creating this object via text/plain content-type isn't available.")

    @classmethod
    def new_random(cls, id_: str) -> 'Thing':
        return cls(
            id=id_,
            color=random.choice(list(ThingColor)),
            type=random.choice(list(ThingType)),
            created=datetime.utcnow().replace(tzinfo=timezone.utc)
        )
