"""Top-level package for Deep Translator"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from externals.deeptranslator.chatgpt import ChatGptTranslator
from externals.deeptranslator.deepl import DeeplTranslator
from externals.deeptranslator.detection import batch_detection, single_detection
from externals.deeptranslator.google import GoogleTranslator
from externals.deeptranslator.libre import LibreTranslator
from externals.deeptranslator.linguee import LingueeTranslator
from externals.deeptranslator.microsoft import MicrosoftTranslator
from externals.deeptranslator.mymemory import MyMemoryTranslator
from externals.deeptranslator.papago import PapagoTranslator
from externals.deeptranslator.pons import PonsTranslator
from externals.deeptranslator.qcri import QcriTranslator
from externals.deeptranslator.yandex import YandexTranslator

__author__ = """Nidhal Baccouri"""
__email__ = "nidhalbacc@gmail.com"
__version__ = "1.9.1"

__all__ = [
    "GoogleTranslator",
    "PonsTranslator",
    "LingueeTranslator",
    "MyMemoryTranslator",
    "YandexTranslator",
    "MicrosoftTranslator",
    "QcriTranslator",
    "DeeplTranslator",
    "LibreTranslator",
    "PapagoTranslator",
    "ChatGptTranslator",
    "single_detection",
    "batch_detection",
]
