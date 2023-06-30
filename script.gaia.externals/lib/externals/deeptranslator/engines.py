__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from externals.deeptranslator.base import BaseTranslator

__engines__ = {
    translator.__name__.replace("Translator", "").lower(): translator
    for translator in BaseTranslator.__subclasses__()
}
