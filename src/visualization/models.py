import base64
import hashlib
from uuid import uuid4

from pydantic import BaseModel, Field


class FigureArtifact(BaseModel, frozen=True):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    media_type: str = "image/svg+xml"
    payload_base64: str
    sha256: str
    provenance: tuple[str, ...] = ("matplotlib",)
    epistemic_status: str = "exploratory"
    limitations: tuple[str, ...] = ("Provided plotting arrays are not bound to an admitted measurement.",)

    @classmethod
    def from_svg(cls, title: str, svg: bytes) -> "FigureArtifact":
        return cls(title=title,payload_base64=base64.b64encode(svg).decode("ascii"),sha256=hashlib.sha256(svg).hexdigest())
