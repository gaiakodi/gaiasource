# Copyright 2023 parkminwoo, MIT License

import os
from externals.bardapi.core import Bard
from externals.bardapi.chat import ChatBard
from externals.bardapi.constants import (
    SESSION_HEADERS,
    ALLOWED_LANGUAGES,
    DEFAULT_LANGUAGE,
    SEPARATOR_LINE,
    USER_PROMPT,
)
#from externals.bardapi.core_async import BardAsync
from externals.bardapi.core_cookies import BardCookies

bard_api_key = os.environ.get("_BARD_API_KEY")

__all__ = [
    "BardAsync",
    "BardCookies",
    "Bard",
    "ChatBard",
    "BardAsync",
    "bard_api_key",
    "SESSION_HEADERS",
    "ALLOWED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "SEPARATOR_LINE",
    "USER_PROMPT",
]
__version__ = "0.1.21"
__author__ = "daniel park <parkminwoo1991@gmail.com>"
