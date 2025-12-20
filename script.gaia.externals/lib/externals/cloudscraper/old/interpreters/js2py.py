from __future__ import absolute_import

# GAIA
#import externals.js2py as js2py
try: import externals.js2py.new as js2py
except: import externals.js2py.old as js2py

import logging
import base64

from . import JavaScriptInterpreter

from .encapsulated import template
from .jsunfuck import jsunfuck

# ------------------------------------------------------------------------------- #


class ChallengeInterpreter(JavaScriptInterpreter):

    # ------------------------------------------------------------------------------- #

    def __init__(self):
        super(ChallengeInterpreter, self).__init__('js2py')

    # ------------------------------------------------------------------------------- #

    def eval(self, body, domain):

        jsPayload = template(body, domain)

        if js2py.eval_js('(+(+!+[]+[+!+[]]+(!![]+[])[!+[]+!+[]+!+[]]+[!+[]+!+[]]+[+[]])+[])[+!+[]]') == '1':
            logging.warning('WARNING - Please upgrade your js2py https://github.com/PiotrDabkowski/Js2Py, applying work around for the meantime.')
            jsPayload = jsunfuck(jsPayload)

        def atob(s):
            return base64.b64decode('{}'.format(s)).decode('utf-8')

        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        result = context.eval(jsPayload)

        return result


# ------------------------------------------------------------------------------- #

ChallengeInterpreter()
