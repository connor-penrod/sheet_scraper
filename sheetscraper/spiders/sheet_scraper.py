import scrapy
from scrapy.http import Request, FormRequest
from scrapy.contrib.spiders.init import InitSpider


class AnimenzSheetSpider(InitSpider):
    name = "animenz_sheets"
    login_url = 'https://sheet.host/account/login'
    start_url = 'https://sheet.host/user/animenz/sheets'
    
    def __init__(self):
        super().__init__()
        self.count = 0
    
    def init_request(self):
        """This function is called before crawling starts."""
        return Request(url=self.login_url, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        return scrapy.FormRequest.from_response(
            response,
            formdata={'login': '<username>', 'password': '<password>'},
            callback=self.check_login_response
        )

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        #if "Hi Herman" in response.body:
        #    self.log("Successfully logged in. Let's start crawling!")
        #    # Now the crawling can begin..
        #    return self.initialized()
        #else:
        #    self.log("Bad times :(")
            # Something went wrong, we couldn't log in, so nothing happens.
        if "You have successfully logged in" in response.body.decode("utf-8"):
            return Request(url=self.start_url, callback=self.start_parse)
        else:
            self.log("Couldn't log in.")
        
  
    def start_parse(self, response):
        #page = response.url.split("/")[-2]
        urls = response.css('a').xpath('@href').getall()
        valid_urls = [valid_url for valid_url in urls if (len(valid_url.split("/")) >= 2 and valid_url.split("/")[-2] == "sheet")]
        for url in valid_urls:
            next_page = response.urljoin(url)
            yield scrapy.Request(next_page, callback=self.parse_subpage)
    def parse_subpage(self, response):
        title = response.css("div.sheet-header > h2 > span").xpath("@content").get()
        download_links = [link for link in response.css('a').xpath('@href').getall() if len(link.split("/")) >= 4 and link.split("/")[-4] == "sheet"]
        for link in download_links:
            print(link)
            next_page = response.urljoin(link)
            request = scrapy.Request(next_page, callback=self.download_pdf)
            request.meta['title'] = title
            yield request
        
    def download_pdf(self, response, *args):
        filename = response.meta['title']
        self.count += 1
        with open("extracted_sheets/" + filename + ".pdf", 'wb+') as f:
            f.write(response.body)
        