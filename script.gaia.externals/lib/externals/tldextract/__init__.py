"""Export tldextract's public interface."""

from . import _version

# GAIA
#from .tldextract import TLDExtract, extract
from .tldextract import TLDExtract, extract, update

__version__: str = _version.version

__all__ = [
    "extract",
    "TLDExtract",
    "__version__",
]
