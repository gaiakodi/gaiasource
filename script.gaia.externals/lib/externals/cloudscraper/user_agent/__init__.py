import json
import os
import random
import re
import sys
import ssl

from collections import OrderedDict

# ------------------------------------------------------------------------------- #

# Gaia
#import xbmcgui
GaiaCloudscraperAgents = None

class User_Agent():

    # ------------------------------------------------------------------------------- #

    def __init__(self, *args, **kwargs):
        self.headers = None
        self.cipherSuite = []
        self.loadUserAgent(*args, **kwargs)

    # ------------------------------------------------------------------------------- #

    def filterAgents(self, user_agents):
        filtered = {}

        if self.mobile:
            if self.platform in user_agents['mobile'] and user_agents['mobile'][self.platform]:
                filtered.update(user_agents['mobile'][self.platform])

        if self.desktop:
            if self.platform in user_agents['desktop'] and user_agents['desktop'][self.platform]:
                filtered.update(user_agents['desktop'][self.platform])

        return filtered

    # ------------------------------------------------------------------------------- #

    def tryMatchCustom(self, user_agents):
        for device_type in user_agents['user_agents']:
            for platform in user_agents['user_agents'][device_type]:
                for browser in user_agents['user_agents'][device_type][platform]:
                    if re.search(re.escape(self.custom), ' '.join(user_agents['user_agents'][device_type][platform][browser])):
                        self.headers = user_agents['headers'][browser]
                        self.headers['User-Agent'] = self.custom
                        self.cipherSuite = user_agents['cipherSuite'][browser]
                        return True
        return False

    # ------------------------------------------------------------------------------- #

    def loadUserAgent(self, *args, **kwargs):
        self.browser = kwargs.pop('browser', None)

        self.platforms = ['linux', 'windows', 'darwin', 'android', 'ios']
        self.browsers = ['chrome', 'firefox']

        if isinstance(self.browser, dict):
            self.custom = self.browser.get('custom', None)
            self.platform = self.browser.get('platform', None)
            self.desktop = self.browser.get('desktop', True)
            self.mobile = self.browser.get('mobile', True)
            self.browser = self.browser.get('browser', None)
        else:
            self.custom = kwargs.pop('custom', None)
            self.platform = kwargs.pop('platform', None)
            self.desktop = kwargs.pop('desktop', True)
            self.mobile = kwargs.pop('mobile', True)

        if not self.desktop and not self.mobile:
            sys.tracebacklimit = 0
            raise RuntimeError("Sorry you can't have mobile and desktop disabled at the same time.")

        # Gaia
        #with open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r') as fp:
        #    user_agents = json.load(
        #        fp,
        #        object_pairs_hook=OrderedDict
        #    )
        global GaiaCloudscraperAgents
        if GaiaCloudscraperAgents is None:
			# Do not set the global property. For some reason this can cause a deadlock if this is called from multiple threads or processes.
            #property = 'GaiaCloudscraperAgents'
            #user_agents = xbmcgui.Window(10000).getProperty(property)
            user_agents = None
            if not user_agents:
                #fp = open(os.path.join(os.path.dirname(__file__), 'browsers.json'), 'r') # Does not work on Android (Nvidia Shield).

                import xbmcvfs

                path = None
                if not path:
                    try: path = os.path.join(os.path.dirname(__file__), 'browsers.json')
                    except: pass
                if not path:
                    try: path = os.path.join(xbmcvfs.translatePath('special://home'), 'addons', 'script.gaia.externals', 'lib', 'externals', 'cloudscraper', 'user_agent', 'browsers.json')
                    except: pass

                if path:
                    if not user_agents:
                        try:
                            fp = open(path, 'r')
                            user_agents = fp.read()
                            fp.close()
                        except: pass
                    if not user_agents:
                        try:
                            fp = xbmcvfs.File(path)
                            user_agents = fp.read()
                            fp.close()
                        except: pass

                # Fallback if file reading failed.
                if not user_agents:
                    user_agents = '{"headers":{"chrome":{"User-Agent":null,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9","Accept-Encoding":"gzip, deflate, br"},"firefox":{"User-Agent":null,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.5","Accept-Encoding":"gzip, deflate, br"}},"cipherSuite":{"chrome":["TLS_AES_128_GCM_SHA256","TLS_AES_256_GCM_SHA384","TLS_CHACHA20_POLY1305_SHA256","ECDHE-ECDSA-AES128-GCM-SHA256","ECDHE-RSA-AES128-GCM-SHA256","ECDHE-ECDSA-AES256-GCM-SHA384","ECDHE-RSA-AES256-GCM-SHA384","ECDHE-ECDSA-CHACHA20-POLY1305","ECDHE-RSA-CHACHA20-POLY1305","ECDHE-RSA-AES128-SHA","ECDHE-RSA-AES256-SHA","AES128-GCM-SHA256","AES256-GCM-SHA384","AES128-SHA","AES256-SHA","DES-CBC3-SHA"],"firefox":["TLS_AES_128_GCM_SHA256","TLS_CHACHA20_POLY1305_SHA256","TLS_AES_256_GCM_SHA384","ECDHE-ECDSA-AES128-GCM-SHA256","ECDHE-RSA-AES128-GCM-SHA256","ECDHE-ECDSA-CHACHA20-POLY1305","ECDHE-RSA-CHACHA20-POLY1305","ECDHE-ECDSA-AES256-GCM-SHA384","ECDHE-RSA-AES256-GCM-SHA384","ECDHE-ECDSA-AES256-SHA","ECDHE-ECDSA-AES128-SHA","ECDHE-RSA-AES128-SHA","ECDHE-RSA-AES256-SHA","DHE-RSA-AES128-SHA","DHE-RSA-AES256-SHA","AES128-SHA","AES256-SHA","DES-CBC3-SHA"]},"user_agents":{"desktop":{"windows":{"chrome":["Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3739.0 Safari/537.36 Edg/75.0.109.0","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.66 Safari/537.36","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3788.1 Safari/537.36"],"firefox":["Mozilla/5.0 (Windows NT 6.1; rv:67.0) Gecko/20100101 Firefox/67.0","Mozilla/5.0 (Windows NT 6.1; WOW64; rv:67.0) Gecko/20100101 Firefox/67.0","Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0","Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0","Mozilla/5.0 (Windows NT 10.0; WOW64; rv:67.0) Gecko/20100101 Firefox/67.0"]},"linux":{"chrome":["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.112 Safari/537.36 OPT/1.16.62","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.136 Safari/537.36","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"],"firefox":["Mozilla/5.0 (X11; Linux i686; rv:60.9) Gecko/20100101 Goanna/4.1 Firefox/60.9 PaleMoon/28.2.0","Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0","Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0","Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0","Mozilla/5.0 (X11; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0"]},"darwin":{"chrome":["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.28 Safari/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3783.0 Safari/537.36"],"firefox":["Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:66.0) Gecko/20100101 Firefox/66.0","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:66.0) Gecko/20100101 Firefox/66.0","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:67.0) Gecko/20100101 Firefox/67.0","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:67.0) Gecko/20100101 Firefox/67.0"]}},"mobile":{"android":{"chrome":["Mozilla/5.0 (Linux; Android 9; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36","Mozilla/5.0 (Linux; Android 6.0.1; VS500PP) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.61 Mobile Safari/537.36","Mozilla/5.0 (Linux; Android 8.0.0; SM-J737V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.92 Mobile Safari/537.36","Mozilla/5.0 (Linux; Android 8.0.0; moto e5 cruise) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.28 Mobile Safari/537.36","Mozilla/5.0 (Linux; Android 8.1.0; QS5509A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.28 Mobile Safari/537.36"],"firefox":["Mozilla/5.0 (Android 9; Mobile; rv:66.0) Gecko/66.0 Firefox/66.0","Mozilla/5.0 (Android 4.4.2; Tablet; rv:67.0) Gecko/67.0 Firefox/67.0","Mozilla/5.0 (Android 8.1.0; Mobile; rv:67.0) Gecko/67.0 Firefox/67.0","Mozilla/5.0 (Android 7.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0","Mozilla/5.0 (Android 7.1.1; Tablet; rv:68.0) Gecko/68.0 Firefox/68.0"]},"ios":{"chrome":["Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.4592.513 Mobile Safari/537.36","Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.1914.847 Mobile Safari/537.36","Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.4712.445 Mobile Safari/537.36","Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.7982.469 Mobile Safari/537.36","Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.1502.79 Mobile Safari/537.36"],"firefox":[]}}}}'

                #xbmcgui.Window(10000).setProperty(property, user_agents.encode('utf-8'))
            GaiaCloudscraperAgents = json.loads(user_agents, object_pairs_hook = OrderedDict)
        user_agents = GaiaCloudscraperAgents

        if self.custom:
            if not self.tryMatchCustom(user_agents):
                self.cipherSuite = [
                    ssl._DEFAULT_CIPHERS,
                    '!AES128-SHA',
                    '!ECDHE-RSA-AES256-SHA',
                ]
                self.headers = OrderedDict([
                    ('User-Agent', self.custom),
                    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
                    ('Accept-Language', 'en-US,en;q=0.9'),
                    ('Accept-Encoding', 'gzip, deflate, br')
                ])
        else:
            if self.browser and self.browser not in self.browsers:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry "{self.browser}" browser is not valid, valid browsers are [{", ".join(self.browsers)}].')

            if not self.platform:
                self.platform = random.SystemRandom().choice(self.platforms)

            if self.platform not in self.platforms:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry the platform "{self.platform}" is not valid, valid platforms are [{", ".join(self.platforms)}]')

            filteredAgents = self.filterAgents(user_agents['user_agents'])

            if not self.browser:
                # has to be at least one in there...
                while not filteredAgents.get(self.browser):
                    self.browser = random.SystemRandom().choice(list(filteredAgents.keys()))

            if not filteredAgents[self.browser]:
                sys.tracebacklimit = 0
                raise RuntimeError(f'Sorry "{self.browser}" browser was not found with a platform of "{self.platform}".')

            self.cipherSuite = user_agents['cipherSuite'][self.browser]
            self.headers = user_agents['headers'][self.browser]

            self.headers['User-Agent'] = random.SystemRandom().choice(filteredAgents[self.browser])

        if not kwargs.get('allow_brotli', False) and 'br' in self.headers['Accept-Encoding']:
            self.headers['Accept-Encoding'] = ','.join([
                encoding for encoding in self.headers['Accept-Encoding'].split(',') if encoding.strip() != 'br'
            ]).strip()
