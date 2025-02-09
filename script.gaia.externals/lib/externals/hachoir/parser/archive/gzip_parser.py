"""
GZIP archive parser.

Author: Victor Stinner
"""

from externals.hachoir.parser import Parser
from externals.hachoir.field import (
    UInt8, UInt16, UInt32, Enum, TimestampUnix32,
    Bit, CString, SubFile,
    NullBits, Bytes, RawBytes)
from externals.hachoir.core.text_handler import textHandler, hexadecimal, filesizeHandler
from externals.hachoir.core.endian import LITTLE_ENDIAN
from externals.hachoir.parser.common.deflate import Deflate


class GzipParser(Parser):
    endian = LITTLE_ENDIAN
    PARSER_TAGS = {
        "id": "gzip",
        "category": "archive",
        "file_ext": ("gz",),
        "mime": ("application/x-gzip",),
        "min_size": 18 * 8,
        "magic_regex": (
            # (magic, compression=deflate, <flags>, <mtime>, )
            (b'\x1F\x8B\x08.{5}[\0\2\4\6][\x00-\x0D]', 0),
        ),
        "description": "gzip archive",
    }
    os_name = {
        0: "FAT filesystem",
        1: "Amiga",
        2: "VMS (or OpenVMS)",
        3: "Unix",
        4: "VM/CMS",
        5: "Atari TOS",
        6: "HPFS filesystem (OS/2, NT)",
        7: "Macintosh",
        8: "Z-System",
        9: "CP/M",
        10: "TOPS-20",
        11: "NTFS filesystem (NT)",
        12: "QDOS",
        13: "Acorn RISCOS",
    }
    COMPRESSION_NAME = {
        8: "deflate",
    }

    def validate(self):
        if self["signature"].value != b'\x1F\x8B':
            return "Invalid signature"
        if self["compression"].value not in self.COMPRESSION_NAME:
            return "Unknown compression method (%u)" % self["compression"].value
        if self["reserved[0]"].value != 0:
            return "Invalid reserved[0] value"
        if self["reserved[1]"].value != 0:
            return "Invalid reserved[1] value"
        if self["reserved[2]"].value != 0:
            return "Invalid reserved[2] value"
        return True

    def createFields(self):
        # Gzip header
        yield Bytes(self, "signature", 2, r"GZip file signature (\x1F\x8B)")
        yield Enum(UInt8(self, "compression", "Compression method"), self.COMPRESSION_NAME)

        # Flags
        yield Bit(self, "is_text", "File content is probably ASCII text")
        yield Bit(self, "has_crc16", "Header CRC16")
        yield Bit(self, "has_extra", "Extra informations (variable size)")
        yield Bit(self, "has_filename", "Contains filename?")
        yield Bit(self, "has_comment", "Contains comment?")
        yield NullBits(self, "reserved[]", 3)
        yield TimestampUnix32(self, "mtime", "Modification time")

        # Extra flags
        yield NullBits(self, "reserved[]", 1)
        yield Bit(self, "slowest", "Compressor used maximum compression (slowest)")
        yield Bit(self, "fastest", "Compressor used the fastest compression")
        yield NullBits(self, "reserved[]", 5)
        yield Enum(UInt8(self, "os", "Operating system"), self.os_name)

        # Optional fields
        if self["has_extra"].value:
            yield UInt16(self, "extra_length", "Extra length")
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra")
        if self["has_filename"].value:
            yield CString(self, "filename", "Filename", charset="ISO-8859-1")
        if self["has_comment"].value:
            yield CString(self, "comment", "Comment")
        if self["has_crc16"].value:
            yield textHandler(UInt16(self, "hdr_crc16", "CRC16 of the header"),
                              hexadecimal)

        if self._size is None:  # TODO: is it possible to handle piped input?
            raise NotImplementedError()

        # Read file
        size = (self._size - self.current_size) // 8 - 8  # -8: crc32+size
        if 0 < size:
            if self["has_filename"].value:
                filename = self["filename"].value
            else:
                for tag, filename in self.stream.tags:
                    if tag == "filename" and filename.endswith(".gz"):
                        filename = filename[:-3]
                        break
                else:
                    filename = None
            yield Deflate(SubFile(self, "file", size, filename=filename))

        # Footer
        yield textHandler(UInt32(self, "crc32",
                                 "Uncompressed data content CRC32"), hexadecimal)
        yield filesizeHandler(UInt32(self, "size", "Uncompressed size"))

    def createDescription(self):
        desc = "gzip archive"
        info = []
        if "filename" in self:
            info.append('filename "%s"' % self["filename"].value)
        if "size" in self:
            info.append("was %s" % self["size"].display)
        if self["mtime"].value:
            info.append(self["mtime"].display)
        return "%s: %s" % (desc, ", ".join(info))
