"""
Microsoft Office documents parser.
OLE2 files are also used by many other programs to store data.

Informations:
* wordole.c of AntiWord program (v0.35)
  Copyright (C) 1998-2003 A.J. van Os
  Released under GNU GPL
  http://www.winfield.demon.nl/
* File gsf-infile-msole.c of libgsf library (v1.14.0)
  Copyright (C) 2002-2004 Jody Goldberg (jody@gnome.org)
  Released under GNU LGPL 2.1
  http://freshmeat.net/projects/libgsf/
* PDF from AAF Association
  Copyright (C) 2004 AAF Association
  Copyright (C) 1991-2003 Microsoft Corporation
  http://www.aafassociation.org/html/specs/aafcontainerspec-v1.0.1.pdf

Author: Victor Stinner
Creation: 2006-04-23
"""

from externals.hachoir.parser import HachoirParser
from externals.hachoir.field import (
    FieldSet, ParserError, SeekableFieldSet, RootSeekableFieldSet,
    UInt8, UInt16, UInt32, UInt64, TimestampWin64, Enum,
    Bytes, NullBytes, String, CustomFragment)
from externals.hachoir.core.text_handler import filesizeHandler
from externals.hachoir.core.endian import LITTLE_ENDIAN
from externals.hachoir.parser.common.win32 import GUID
from externals.hachoir.parser.misc.msoffice import PROPERTY_NAME, RootEntry, RawParser

MIN_BIG_BLOCK_LOG2 = 6   # 512 bytes
MAX_BIG_BLOCK_LOG2 = 14  # 64 kB

# Number of items in DIFAT
NB_DIFAT = 109


class SECT(UInt32):
    UNUSED = 0xFFFFFFFF   # -1
    END_OF_CHAIN = 0xFFFFFFFE   # -2
    BFAT_SECTOR = 0xFFFFFFFD   # -3
    DIFAT_SECTOR = 0xFFFFFFFC   # -4
    SPECIALS = set((END_OF_CHAIN, UNUSED, BFAT_SECTOR, DIFAT_SECTOR))

    special_value_name = {
        UNUSED: "unused",
        END_OF_CHAIN: "end of a chain",
        BFAT_SECTOR: "BFAT sector (in a FAT)",
        DIFAT_SECTOR: "DIFAT sector (in a FAT)",
    }

    def __init__(self, parent, name, description=None):
        UInt32.__init__(self, parent, name, description)

    def createDisplay(self):
        val = self.value
        return SECT.special_value_name.get(val, str(val))


class Property(FieldSet):
    TYPE_ROOT = 5
    TYPE_NAME = {
        1: "storage",
        2: "stream",
        3: "ILockBytes",
        4: "IPropertyStorage",
        5: "root"
    }
    DECORATOR_NAME = {
        0: "red",
        1: "black",
    }
    static_size = 128 * 8

    def createFields(self):
        bytes = self.stream.readBytes(self.absolute_address, 4)
        if bytes == b"\0R\0\0":
            charset = "UTF-16-BE"
        else:
            charset = "UTF-16-LE"
        yield String(self, "name", 64, charset=charset, truncate="\0")
        yield UInt16(self, "namelen", "Length of the name")
        yield Enum(UInt8(self, "type", "Property type"), self.TYPE_NAME)
        yield Enum(UInt8(self, "decorator", "Decorator"), self.DECORATOR_NAME)
        yield SECT(self, "left")
        yield SECT(self, "right")
        yield SECT(self, "child", "Child node (valid for storage and root types)")
        yield GUID(self, "clsid", "CLSID of this storage (valid for storage and root types)")
        yield NullBytes(self, "flags", 4, "User flags")
        yield TimestampWin64(self, "creation", "Creation timestamp(valid for storage and root types)")
        yield TimestampWin64(self, "lastmod", "Modify timestamp (valid for storage and root types)")
        yield SECT(self, "start", "Starting SECT of the stream (valid for stream and root types)")
        if self["/header/bb_shift"].value == 9:
            yield filesizeHandler(UInt32(self, "size", "Size in bytes (valid for stream and root types)"))
            yield NullBytes(self, "padding", 4)
        else:
            yield filesizeHandler(UInt64(self, "size", "Size in bytes (valid for stream and root types)"))

    def createDescription(self):
        name = self["name"].display
        size = self["size"].display
        return "Property: %s (%s)" % (name, size)


class DIFat(SeekableFieldSet):

    def __init__(self, parent, name, db_start, db_count, description=None):
        SeekableFieldSet.__init__(self, parent, name, description)
        self.start = db_start
        self.count = db_count

    def createFields(self):
        for index in range(NB_DIFAT):
            yield SECT(self, "index[%u]" % index)

        difat_sect = self.start
        index = NB_DIFAT
        entries_per_sect = self.parent.sector_size // 32 - 1
        for ctr in range(self.count):
            # this is relative to real DIFAT start
            self.seekBit(NB_DIFAT * SECT.static_size +
                         self.parent.sector_size * difat_sect)
            for sect_index in range(entries_per_sect):
                yield SECT(self, "index[%u]" % (index + sect_index))
            index += entries_per_sect
            next = SECT(self, "difat[%u]" % ctr)
            yield next
            difat_sect = next.value


class Header(FieldSet):
    static_size = 68 * 8

    def createFields(self):
        yield GUID(self, "clsid", "16 bytes GUID used by some apps")
        yield UInt16(self, "ver_min", "Minor version")
        yield UInt16(self, "ver_maj", "Major version")
        yield Bytes(self, "endian", 2, "Endian (\\xfe\\xff for little endian)")
        yield UInt16(self, "bb_shift", "Log, base 2, of the big block size")
        yield UInt16(self, "sb_shift", "Log, base 2, of the small block size")
        yield NullBytes(self, "reserved[]", 6, "(reserved)")
        yield UInt32(self, "csectdir", "Number of SECTs in directory chain for 4 KB sectors (version 4)")
        yield UInt32(self, "bb_count", "Number of Big Block Depot blocks")
        yield SECT(self, "bb_start", "Root start block")
        yield NullBytes(self, "transaction", 4, "Signature used for transactions (must be zero)")
        yield UInt32(self, "threshold", "Maximum size for a mini stream (typically 4096 bytes)")
        yield SECT(self, "sb_start", "Small Block Depot start block")
        yield UInt32(self, "sb_count")
        yield SECT(self, "db_start", "First block of DIFAT")
        yield UInt32(self, "db_count", "Number of SECTs in DIFAT")


# Header (ole_id, header, difat) size in bytes
HEADER_SIZE = 64 + Header.static_size + NB_DIFAT * SECT.static_size


class SectFat(FieldSet):

    def __init__(self, parent, name, start, count, description=None):
        FieldSet.__init__(self, parent, name, description, size=count * 32)
        self.count = count
        self.start = start

    def createFields(self):
        for i in range(self.start, self.start + self.count):
            yield SECT(self, "index[%u]" % i)


class OLE2_File(HachoirParser, RootSeekableFieldSet):
    PARSER_TAGS = {
        "id": "ole2",
        "category": "misc",
        "file_ext": (
            "db",                        # Thumbs.db
            "doc", "dot",                # Microsoft Word
            "ppt", "ppz", "pps", "pot",  # Microsoft Powerpoint
            "xls", "xla",                # Microsoft Excel
            "msi",                       # Windows installer
        ),
        "mime": (
            "application/msword",
            "application/msexcel",
            "application/mspowerpoint",
        ),
        "min_size": 512 * 8,
        "description": "Microsoft Office document",
        "magic": ((b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1", 0),),
    }
    endian = LITTLE_ENDIAN

    def __init__(self, stream, **args):
        RootSeekableFieldSet.__init__(
            self, None, "root", stream, None, stream.askSize(self))
        HachoirParser.__init__(self, stream, **args)

    def close(self):
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def validate(self):
        if self["ole_id"].value != b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
            return "Invalid magic"
        if self["header/ver_maj"].value not in (3, 4):
            return "Unknown major version (%s)" % self["header/ver_maj"].value
        if self["header/endian"].value not in (b"\xFF\xFE", b"\xFE\xFF"):
            return "Unknown endian (%s)" % self["header/endian"].raw_display
        if not(MIN_BIG_BLOCK_LOG2 <= self["header/bb_shift"].value <= MAX_BIG_BLOCK_LOG2):
            return "Invalid (log 2 of) big block size (%s)" % self["header/bb_shift"].value
        if self["header/bb_shift"].value < self["header/sb_shift"].value:
            return "Small block size (log2=%s) is bigger than big block size (log2=%s)!" \
                % (self["header/sb_shift"].value, self["header/bb_shift"].value)
        return True

    def createFields(self):
        # Signature
        yield Bytes(self, "ole_id", 8, "OLE object signature")

        header = Header(self, "header")
        yield header

        # Configure values
        self.sector_size = (8 << header["bb_shift"].value)
        self.fat_count = header["bb_count"].value
        self.items_per_bbfat = self.sector_size // SECT.static_size
        self.ss_size = (8 << header["sb_shift"].value)
        self.items_per_ssfat = self.items_per_bbfat

        # Read DIFAT (one level of indirection)
        yield DIFat(self, "difat", header["db_start"].value, header["db_count"].value, "Double Indirection FAT")

        # Read FAT (one level of indirection)
        yield from self.readBFAT()

        # Read SFAT
        yield from self.readSFAT()

        # Read properties
        chain = self.getChain(self["header/bb_start"].value)
        prop_per_sector = self.sector_size // Property.static_size
        self.properties = []
        for block in chain:
            self.seekBlock(block)
            for index in range(prop_per_sector):
                property = Property(self, "property[]")
                yield property
                self.properties.append(property)

        # Parse first property
        for index, property in enumerate(self.properties):
            if index == 0:
                name, parser = 'root', RootEntry
            else:
                try:
                    name, parser = PROPERTY_NAME[property["name"].value]
                except LookupError:
                    name = property.name + "content"
                    parser = RawParser
            yield from self.parseProperty(property, name, parser)

    def parseProperty(self, property, name_prefix, parser=RawParser):
        if not property["size"].value:
            return
        if property["size"].value < self["header/threshold"].value and name_prefix != 'root':
            return
        name = "%s[]" % name_prefix
        first = None
        previous = None
        size = 0
        fragment_group = None
        chain = self.getChain(property["start"].value)
        while True:
            try:
                block = next(chain)
                contiguous = False
                if first is None:
                    first = block
                    contiguous = True
                if previous is not None and block == (previous + 1):
                    contiguous = True
                if contiguous:
                    previous = block
                    size += self.sector_size
                    continue
            except StopIteration:
                block = None
            if first is None:
                break
            self.seekBlock(first)
            desc = "Big blocks %s..%s (%s)" % (
                first, previous, previous - first + 1)
            desc += " of %s bytes" % (self.sector_size // 8)
            field = CustomFragment(
                self, name, size, parser, desc, fragment_group)
            if not fragment_group:
                fragment_group = field.group
                fragment_group.args["ole2"] = field.root
                fragment_group.args["datasize"] = property["size"].value
                fragment_group.args["ole2name"] = property["name"].value
            yield field
            if block is None:
                break
            first = block
            previous = block
            size = self.sector_size

    def getChain(self, start, use_sfat=False):
        if use_sfat:
            fat = self.ss_fat
            items_per_fat = self.items_per_ssfat
            err_prefix = "SFAT chain"
        else:
            fat = self.bb_fat
            items_per_fat = self.items_per_bbfat
            err_prefix = "BFAT chain"
        block = start
        block_set = set()
        previous = block
        while block != SECT.END_OF_CHAIN:
            if block in SECT.SPECIALS:
                raise ParserError("%s: Invalid block index (0x%08x), previous=%s" % (
                    err_prefix, block, previous))
            if block in block_set:
                raise ParserError("%s: Found a loop (%s=>%s)" %
                                  (err_prefix, previous, block))
            block_set.add(block)
            yield block
            previous = block
            index = block // items_per_fat
            try:
                block = fat[index]["index[%u]" % block].value
            except LookupError:
                break

    def readBFAT(self):
        self.bb_fat = []
        start = 0
        count = self.items_per_bbfat
        for index, block in enumerate(self.array("difat/index")):
            block = block.value
            if block == SECT.UNUSED:
                break

            desc = "FAT %u/%u at block %u" % \
                (1 + index, self["header/bb_count"].value, block)

            self.seekBlock(block)
            field = SectFat(self, "bbfat[]", start, count, desc)
            yield field
            self.bb_fat.append(field)

            start += count

    def readSFAT(self):
        chain = self.getChain(self["header/sb_start"].value)
        start = 0
        self.ss_fat = []
        count = self.items_per_ssfat
        for index, block in enumerate(chain):
            self.seekBlock(block)
            field = SectFat(self, "sfat[]",
                            start, count,
                            "SFAT %u/%u at block %u" %
                            (1 + index, self["header/sb_count"].value, block))
            yield field
            self.ss_fat.append(field)
            start += count

    def createContentSize(self):
        max_block = 0
        for fat in self.array("bbfat"):
            for entry in fat:
                block = entry.value
                if block not in SECT.SPECIALS:
                    max_block = max(block, max_block)
        if max_block in SECT.SPECIALS:
            return None
        else:
            return HEADER_SIZE + (max_block + 1) * self.sector_size

    def seekBlock(self, block):
        self.seekBit(HEADER_SIZE + block * self.sector_size)
