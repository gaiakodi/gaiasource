from __future__ import unicode_literals

from externals.js2py.new.internals.conversions import *
from externals.js2py.new.internals.func_utils import *


class ConsoleMethods:
    def log(this, args):
        x = ' '.join(to_string(e) for e in args)
        print(x)
        return undefined
