import logging
import sys
from typing import List

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret


API_PREFIX = "/service"

JWT_TOKEN_PREFIX = "Token"  # noqa: S105 在做用户校验时，需要把这个前缀加上，并加空格
VERSION = "1.0.0"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret)

PROJECT_NAME: str = config("PROJECT_NAME", default="IOS Device Management")
ALLOWED_HOSTS: List[str] = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=""
)
