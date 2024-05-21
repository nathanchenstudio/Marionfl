# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
from scrapy.exporters import CsvItemExporter


class JsonPipeline:
    def open_spider(self, spider):
        self.file = open(f'{spider.settings.get("DATA_FILE_PATH")}/{spider.name}.json', 'w')
        self.file.write('[\n')
        self.start = True
        self.duplicate_filter = set()

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        if item['Permit #'] not in self.duplicate_filter:
            if not self.start:
                line = f",\n{json.dumps(item, indent=4)}"
            else:
                self.start = False
                line = f"{json.dumps(item, indent=4)}"
            self.file.write(line)
            self.duplicate_filter.add(item['Permit #'])
        return item


class CSVPipeline:
    def open_spider(self, spider):
        file_path = f'{spider.settings.get("DATA_FILE_PATH")}/{spider.name}.csv'
        self.file = open(file_path, 'wb')
        self.exporter = CsvItemExporter(self.file, include_headers_line=True, encoding='utf-8')
        # self.exporter.fields_to_export = ['...']
        self.exporter.start_exporting()
        self.duplicate_filter = set()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        if item['Permit #'] not in self.duplicate_filter:
            self.exporter.export_item(item)
            self.duplicate_filter.add(item['Permit #'])
        return item
