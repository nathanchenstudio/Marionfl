import json
import re
import time
from urllib.parse import urljoin
import scrapy


class MarionflSpider(scrapy.Spider):
    name = 'marionfl'
    allowed_domains = ['marionfl.org', 'marioncountyfl.org']
    start_urls = [
        'https://www.marionfl.org/agencies-departments'
        '/departments-facilities-offices/building-safety/permit-inspections',
    ]
    input_id_names = {
        'IWDBEDIT1': 'Permit #',
        'IWDBMEMO1': 'Job Desc',
        'IWDBEDIT9': 'Expiration Date',
        'IWDBEDIT10': 'Last Inspection Request',
        'IWDBEDIT11': 'Last Inspection Result',
        'IWDBEDIT2': 'Permit Status',
        'IWDBEDIT12': 'Type',
        'IWDBEDIT3': 'Type2',
        'IWDBEDIT8': 'Issued Date',
        'IWDBEDIT4': 'Owner',
        'IWDBEDIT5': 'Address',
        'IWDBEDIT6': 'DBA',
        'IWDBEDIT7': 'CO Date',
        'IWDBEDIT13': 'Apply Date',
        'IWDBEDIT14': 'Parcel #',
    }

    def parse(self, response, **kwargs):
        iframe = response.xpath('//iframe[@name="I1"]/@src').get()
        yield scrapy.Request(iframe, callback=self.parse_permit_search)

    def parse_permit_search(self, response):
        # On the "Permit search" page now
        # Click the "By Permit, Parcel or Address" button
        payload = {}
        form = response.xpath('//form[@action]')
        action = urljoin(response.url, form.xpath('@action').get())
        for one in form.xpath('input'):
            key = one.xpath('@name').get()
            value = one.xpath('@value').get()
            payload[key] = value
        payload['IW_width'] = '1379'
        payload['IW_height'] = '403'
        payload['IW_dpr'] = '2'
        yield scrapy.FormRequest(
            action,
            formdata=payload,
            callback=self.parse_permit_button_phase1
        )

    def parse_permit_button_phase1(self, response):
        session_id = re.search(r'GAppID="(.*?)"', response.text)
        session_id = session_id.group(1)

        url = f'{response.url}$/callback?callback=BTNPERMITS.DoOnAsyncClick&x=153&y=33&which=0&modifiers='
        payload = {
            'BTNPERMITS': '',
            'IW_FormName': 'FrmStart',
            'IW_FormClass': 'TFrmStart',
            'IW_width': '1379',
            'IW_height': '403',
            'IW_Action': 'BTNPERMITS',
            'IW_ActionParam': '',
            'IW_Offset': '',
            'IW_SessionID_': session_id,
            'IW_TrackID_': '2',
            'IW_WindowID_': '',
            'IW_AjaxID': str(int(time.time()*1000.0))
        }
        yield scrapy.FormRequest(
            url,
            formdata=payload,
            callback=self.parse_permit_button_phase2,
            meta={'session_id': session_id}
        )

    def parse_permit_button_phase2(self, response):
        payload = re.search(r'", (.*?)\);', response.text)
        payload = json.loads(payload.group(1))
        for k, v in payload.items():
            if isinstance(v, int):
                payload[k] = str(v)

        url = re.search(r'IW.post\("(.*?)",', response.text)
        url = urljoin(response.url, url.group(1))
        yield scrapy.FormRequest(
            url,
            formdata=payload,
            callback=self.parse_permit_page
        )

    def parse_permit_page(self, response):
        # On the "Enter Permit" page now
        session_id = re.search(r'GAppID="(.*?)"', response.text)
        session_id = session_id.group(1)

        # Search a permit number
        url = f'{response.url}$/callback?callback=EDTPERMITNBR.DoOnAsyncChange'
        for permit_number in range(2022010000, 2022123199):
            payload = {
                'EDTPERMITNBR': str(permit_number),
                'IW_FormName': 'FrmMain',
                'IW_FormClass': 'TFrmMain',
                'IW_width': '1362',
                'IW_height': '620',
                'IW_Action': 'EDTPERMITNBR',
                'IW_ActionParam': '',
                'IW_Offset': '',
                'IW_SessionID_': session_id,
                'IW_TrackID_': '9',
                'IW_WindowID_': '',
                'IW_AjaxID': str(int(time.time() * 1000.0))
            }
            yield scrapy.FormRequest(
                url,
                formdata=payload,
                callback=self.parse_search_result_phase1,
                meta={'session_id': session_id, 'permit_number': permit_number}
            )

    def parse_search_result_phase1(self, response):
        url = response.xpath('//submit/text()').get()
        trackid = response.xpath('//trackid/text()').get()
        if not trackid:
            return
        url = f'{urljoin(response.url, url)}$/callback?callback=BTNGUESTLOGIN.DoOnAsyncClick&x=136&y=38&which=0&modifiers='
        payload = {
            'BTNGUESTLOGIN': '',
            'IW_FormName': 'FrmMain',
            'IW_FormClass': 'TFrmMain',
            'IW_width': '1362',
            'IW_height': '620',
            'IW_Action': 'BTNGUESTLOGIN',
            'IW_ActionParam': '',
            'IW_Offset': '',
            'IW_SessionID_': response.meta['session_id'],
            'IW_TrackID_': trackid,
            'IW_WindowID_': '',
            'IW_AjaxID': str(int(time.time() * 1000.0))
        }
        yield scrapy.FormRequest(
            url,
            formdata=payload,
            callback=self.parse_search_result_phase2,
            meta={'session_id': response.meta['session_id'],
                  'permit_number': response.meta['permit_number']}
        )

    def parse_search_result_phase2(self, response):
        if 'No matching permit # found!' in response.text:
            self.logger.info(f"No matching permit # found for {response.meta['permit_number']}")
            return

        url = response.url.split('$')[0]
        trackid = response.xpath('//trackid/text()').get()
        if not trackid:
            trackid = re.search(r'"IW_TrackID_": (\d+)}', response.text)
            if bool(trackid):
                trackid = trackid.group(1)
        if not trackid:
            return
        yield scrapy.FormRequest(
            urljoin(response.url, url),
            formdata={
                'IW_SessionID_': response.meta['session_id'],
                'IW_TrackID_': trackid
            },
            callback=self.parse_search_result_phase3,
            meta={'permit_number': response.meta['permit_number']}
        )

    def parse_search_result_phase3(self, response):
        result = {}
        for one in response.xpath('//form[@class="iw_default_submit_form"]//input[@type="text"] | '
                                  '//form[@class="iw_default_submit_form"]//textarea'):
            key = one.xpath('@id').get()
            if key not in self.input_id_names:
                continue
            value = one.xpath('@value').get()
            if not value:
                value = one.xpath('text()').get()
            result[self.input_id_names[key]] = value
        if result:
            yield result
        else:
            self.logger.warning(f"No matching permit # found for {response.meta['permit_number']}")


if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = CrawlerProcess(get_project_settings())
    process.crawl('marionfl')
    process.start()

