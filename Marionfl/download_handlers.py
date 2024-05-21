import traceback
import scrapy
from curl_cffi import requests
from scrapy.core.downloader.handlers.http import HTTPDownloadHandler
from scrapy.crawler import Crawler
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from twisted.internet import threads
from twisted.internet.defer import Deferred


class FakeBrowserDownloadHandler(HTTPDownloadHandler):

    def __init__(self, crawler: Crawler) -> None:
        super().__init__(settings=crawler.settings, crawler=crawler)
        self.retry_times = crawler.settings.get('RETRY_TIMES')
        self.timeout = crawler.settings.get('DOWNLOAD_TIMEOUT')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def download_request(self, request: scrapy.Request, spider: scrapy.Spider) -> Deferred:
        return threads.deferToThread(self._download, request)

    def _download(self, request: scrapy.Request):
        # if b'User-Agent' in request.headers:
        #     request.headers.pop(b'User-Agent')
        proxy = request.meta.get('proxy')
        if proxy:
            proxies = {"https": proxy, 'http': proxy}
        else:
            proxies = None

        with requests.Session() as session:
            for _ in range(5):
                try:
                    response: requests.Response = session.request(
                        method=request.method,
                        url=request.url,
                        headers={x.decode(): request.headers[x].decode() for x in request.headers},
                        cookies=request.cookies,
                        data=request.body,
                        impersonate="chrome110",
                        allow_redirects=True,
                        proxies=proxies,
                        timeout=self.timeout,
                        verify=True
                    )
                except:
                    traceback.print_exc()
                else:
                    break

        headers = Headers(response.headers)
        if b'Content-Encoding' in headers:
            del headers[b'Content-Encoding']
        respcls = responsetypes.from_args(
            headers=headers, url=response.url, body=response.content
        )
        return respcls(
            url=str(response.url),
            status=response.status_code,
            headers=headers,
            body=response.content,
            request=request,
        )
