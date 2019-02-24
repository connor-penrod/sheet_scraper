import scrapy
from scrapy.http import Request, FormRequest
from scrapy.spiders.init import InitSpider
import os
import pprint


class IMSLPSpider(InitSpider):
    name = "imslp"
    
    
    def __init__(self):
        super().__init__()
        self.start_url = "https://imslp.org/wiki/Category:Chopin%2C_Fr%C3%A9d%C3%A9ric"
        self.base = "https://imslp.org"
        self.pieces_checked = []
        self.subpages_checked = []
        self.pdfs_checked = []
        self.disclaimers_checked = []
        self.download_pages_reached = 0
        self.pp = pprint.PrettyPrinter(width=41, compact=True)
    
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.start_url, callback=self.start_parse)
  
    def start_parse(self, response):
        print("Starting parse...")
        #page = response.url.split("/")[-2]
        selectors = response.css("#catcolp1-0 > ul > li > a")
        for selector in selectors:
            url = selector.xpath("@href").get()
            title = selector.xpath("string(.)").get()
            self.pieces_checked.append(title)
            next_page = response.urljoin(self.base + url)
            request = scrapy.Request(next_page, callback=self.parse_subpage)
            request.meta['title'] = title
            yield request
    def parse_subpage(self, response):
        self.subpages_checked.append(response.meta['title'])
        print("Parsing subpage: " + response.meta['title'])
        url = response.css("#tabScore1 > div > div > div > p > b > a").xpath("@href").get()
        #title = url.split("/")[-1]
        
        next_page = response.urljoin(url)
        request = scrapy.Request(next_page, callback=self.check_and_handle_disclaimer)
        request.meta['title'] = response.meta['title']
        yield request
        
    def check_and_handle_disclaimer(self, response):
    
        print("Checking disclaimer...")
        if "pdf" in response.url:
            print("Identified PDF.")
            self.download_pdf(response)
        elif "IMSLP makes no guarantee that the files provided for download" in response.body.decode("utf-8"):
            print("Identified disclaimer.")
            self.disclaimers_checked.append(response.meta['title'])
            dl_url = response.css("center > a").xpath("@href").get()
            next_page = response.urljoin(self.base + dl_url)
            request = scrapy.Request(next_page, callback=self.parse_download_page)
            request.meta['title'] = response.meta['title']
            yield request
        else:
            print("Identified download page.")
            self.parse_download_page(response)
        
        
    def parse_download_page(self, response):
        if "pdf" in response.url:
            self.download_pdf(response)
            return
    
        self.download_pages_reached += 1
    
        print("Parsing download page.")
        
        try:
            url = response.css("#sm_dl_wait").xpath("@data-id").get()
        except Exception as e:
            print(response.url)
            raise e
        next_page = response.urljoin(url)
        request = scrapy.Request(next_page, callback=self.download_pdf)
        request.meta['title'] = response.meta['title']
        yield request
    
    def download_pdf(self, response):
        self.pdfs_checked.append(response.meta['title'])
        print("Parsing PDF.")
        filename = response.meta['title']
        directory = "./extracted_sheets" + "_" + "chopin"
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(directory + "/" + filename + ".pdf", 'wb+') as f:
            f.write(response.body)
    
    def closed(self, reason):
        print(len(self.pieces_checked))
        print(len(self.subpages_checked))
        print(len(self.disclaimers_checked))
        print(self.download_pages_reached)
        print(len(self.pdfs_checked))
        self.pp.pprint(self.pieces_checked)
        self.pp.pprint(self.subpages_checked)
        self.pp.pprint(self.disclaimers_checked)
        self.pp.pprint(self.pdfs_checked)
            
    def response_is_ban(self, request, response):
        #print("BANNED?" + str(b'site ripping' in response.body))
        return b'site ripping' in response.body

    def exception_is_ban(self, request, exception):
        return None
        
        