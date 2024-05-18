
import requests
import re
import time
import psutil
import browser_cookie_3x as bc
from urllib.parse import urlencode

class AuthCookieError(Exception):
    pass

class PromptRejectedError(Exception):
    pass

class BingArt:
    browser_procs = {
        bc.chrome: 'chrome.exe',
        bc.yandex: 'browser.exe',
        bc.firefox: 'firefox.exe',
        bc.edge: 'msedge.exe',
        bc.opera: 'launcher.exe',
        bc.opera_gx: 'launcher.exe'
    }

    def __init__(self, auth_cookie_U, auto=False):
        self.session = requests.Session()
        self.base_url = 'https://www.bing.com/images/create'

        if auto:
            self.auth_cookie_U = self.get_auth_cookie_U()
        else:
            self.auth_cookie_U = auth_cookie_U

        self.headers = self._prepare_headers()

    def kill_proc(self, proc):
        for process in psutil.process_iter(['name']):
            if process.info['name'] == proc:
                try:
                    process.kill()
                except:
                    pass

    def scan_cookies(self, cookies):
        auth_cookie_U = None
        for cookie in cookies:
            if cookie.domain == '.bing.com':
                if cookie.name == '_U':
                    auth_cookie_U = cookie.value
        return auth_cookie_U

    def get_auth_cookie_U(self, after_check=False):
        for browser in self.browser_procs:
            try:
                cookies = browser()
                auth_cookie_U = self.scan_cookies(cookies)
                if auth_cookie_U:
                    return auth_cookie_U
            except PermissionError as e:
                if after_check:
                    self.kill_proc(self.browser_procs[browser])
                    cookies = browser()
                    auth_cookie_U = self.scan_cookies(cookies)
                    if auth_cookie_U:
                        return auth_cookie_U
            except Exception as e:
                pass
        if not after_check:
            return self.get_auth_cookie_U(True)
        raise AuthCookieError('Failed to fetch authentication cookie _U automatically.')

    def _prepare_headers(self):
        cookie_str = ''
        if self.auth_cookie_U:
            cookie_str += f'_U={self.auth_cookie_U};'

        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': self.base_url,
            'Accept-Language': 'en-US,en;q=0.9',
            'Cookie': cookie_str
        }

    def _get_balance(self):
        response = self.session.get(self.base_url)
        try:
            coins = int(re.search('bal" aria-label="(\d+) ', response.text).group(1))
        except AttributeError:
            raise AuthCookieError('Auth cookie failed!')
        return coins

    def _fetch_images(self, encoded_query, ID, IG):
        images = []
        while True:
            response = self.session.get(f'{self.base_url}/async/results/{ID}?{encoded_query}&IG={IG}&IID=images.as'.replace('&amp;nfy=1', ''))
            if 'text/css' in response.text:
                src_urls = re.findall(r'src="([^"]+)"', response.text)
                for src_url in src_urls:
                    if '?' in src_url:
                        clean_url = src_url.split('?')[0] + '?pid=ImgGn'
                        images.append({'url': clean_url})
                return images
            time.sleep(5)

    def generate_images(self, query):
        encoded_query = urlencode({'q': query})
        self.session.headers.update(self.headers)
        coins = self._get_balance()
        rt = '4' if coins > 0 else '3'
        creation_url = f'{self.base_url}?{encoded_query}&rt={rt}&FORM=GENCRE'

        response = self.session.post(creation_url, data={'q': query})
        try:
            ID = re.search(';id=([^"]+)"', response.text).group(1)
            IG = re.search('IG:"([^"]+)"', response.text).group(1)
        except AttributeError:
            raise PromptRejectedError('Error! Your prompt has been rejected for ethical reasons.')

        images = self._fetch_images(encoded_query, ID, IG)
        return {'images': images, 'prompt': query}

    def close_session(self):
        self.session.close()


auth_cookie_U = '1h2sgdG1mvoowi6WNwqCO6XzasAnsnDh59hY6Az0LDmjfKXMjFKpqw44XQ3J49NOxGshtKRGAz9HdWvUvNEFGmkTLIhCr0flBkd1sy55TJ5upuLLLPbCxdd0vnCM0Uz6W_P-9Adchhi0uZL3j6nnKrU7QEYaZIIcU6DEi8c1WxwXbDgMZpfI02JvyDKTAEVgVShhTZfkEmTZkmu499-nms77C6XWXTMiYAVbr-KMLrnE'

bing = BingArt(auth_cookie_U)
query = 'naruto'
result = bing.generate_images(query)
images = result['images']
prompt = result['prompt']
for image in images:
    print(image['url'])
bing.close_session()
