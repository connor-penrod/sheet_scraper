import scrapy
from scrapy.http import Request, FormRequest
from scrapy.spiders.init import InitSpider
from urllib.request import urlopen
import json
import os
import pprint


class IMSLPSpider(InitSpider):
    name = "imslp"
    
    def __init__(self):
        super().__init__()
        self.start_url = "https://imslp.org/wiki/Category:Chopin%2C_Fr%C3%A9d%C3%A9ric"
        self.base = "https://imslp.org"
        self.base_EU = "http://imslp.eu"
        self.pieces_checked = []
        self.subpages_checked = []
        self.pdfs_checked = []
        self.disclaimers_checked = []
        self.download_pages_reached = 0
        self.pp = pprint.PrettyPrinter(width=41, compact=True)
        self.proxy = 'https://34.73.124.65:3128'
        
    def init_request(self):
        """This function is called before crawling starts."""
        
        proxy_res = urlopen('https://api.getproxylist.com/proxy?allowsHttps=1&minDownloadSpeed=10000')
        proxy_res_body = proxy_res.read()
        json_res = json.loads(proxy_res_body.decode('utf-8'))
        self.proxy = "https://" + str(json_res['ip']) + ":" + str(json_res['port'])
        self.proxy = "https://34.73.124.65:3128"
        #print("Using proxy: " + self.proxy)
        #print("Uptime: " + str(json_res['uptime']))
        #print("DL Speed: " + str(json_res['downloadSpeed']))
        return Request(url=self.start_url, callback=self.start_parse)
  
    def start_parse(self, response):
        print("Starting parse...")
        #page = response.url.split("/")[-2]
        selectors = response.css("#catcolp1-0 > ul > li > a")
        for selector in selectors:
            url = selector.xpath("@href").get()
            title = selector.xpath("@title").get()
            #print(title)
            if 'Berceuse' in title:
                self.pieces_checked.append(title)
                next_page = response.urljoin(self.base + url)
                request = scrapy.Request(next_page, callback=self.route_request)
                request.meta['title'] = title
                request.meta['proxy'] = self.proxy
                yield request
            
    def route_request(self, response):
        if 'pdf' in response.url and 'linkhandler' not in response.url:
            self.pdfs_checked.append(response.meta['title'])
            print("Parsing PDF.")
            filename = response.meta['title']
            directory = "./extracted_sheets" + "_" + "chopin"
            
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(directory + "/" + filename + ".pdf", 'wb+') as f:
                f.write(response.body)
            return
        
        if "General Information" in response.body.decode("utf-8"):
            print("Routing to subpage handler.")
            self.subpages_checked.append(response.meta['title'])
            print("Parsing subpage: " + response.meta['title'])
            url = response.css("#tabScore1 > div > div > div > p > b > a").xpath("@href").get()
            if url is None:
                print("No subpage url found...")
            else:
                print("URL: " + url)
            
            next_page = response.urljoin(url)
            request = scrapy.Request(next_page, callback=self.route_request)
            request.meta['title'] = response.meta['title']
            request.meta['proxy'] = self.proxy
            print("Sending subpage request")
            yield request
        elif "IMSLP-EU Server" in response.body.decode("utf-8"):
            print("Routing to affiliation disclaimer handler.")
            url = response.css("td > center > a").xpath("@href").get()
            full_url = self.base_EU + url
            next_page = response.urljoin(full_url)
            print("Next page: " + next_page)
            request = scrapy.Request(next_page, callback=self.route_request)
            request.meta['title'] = response.meta['title']
            request.meta['proxy'] = self.proxy
            yield request
        elif "IMSLP needs your help" in response.body.decode("utf-8"):
            print("Routing to download page")
            self.download_pages_reached += 1            
            try:
                url = response.css("#sm_dl_wait").xpath("@data-id").get()
            except Exception as e:
                print(response.url)
                raise e
            next_page = response.urljoin(url)
            request = scrapy.Request(next_page, callback=self.route_request)
            request.meta['title'] = response.meta['title']
            request.meta['proxy'] = self.proxy
            yield request
        elif "IMSLP makes no guarantee that the files provided for download, viewing or streaming on IMSLP are public domain" in response.body.decode('utf-8'):
            print("Routing to disclaimer handler.")
            url = response.css("#wiki-outer-body > div > div > center > a").xpath("@href").get()
            if url is None:
                print("No disclaimer url found...")
            else:
                print("Disclaimer URL: " + url)
            
            next_page = response.urljoin(url)
            request = scrapy.Request(next_page, callback=self.route_request)
            request.meta['title'] = response.meta['title']
            request.meta['proxy'] = self.proxy
            print("Sending disclaimer request")
            yield request
        else:
            print("\nsomething else: " + response.url + "\n")        
        
        
    def check_and_handle_disclaimer(self, response):
        pass
      
    
    
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
        print("\nException: " + str(exception) + "\n")
        return None
        
        