from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VisType(Enum):
    mail = "mail"
    plot = "plot"


@dataclass
class Config:
    username: Optional[str]
    token: Optional[str]
    api_root: str
    ignore_ssl_warn: bool
    profile: Optional[str]
    is_cli: bool