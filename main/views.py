# All required imports
from django.views.generic import ListView
import requests
from bs4 import BeautifulSoup

# Index class (index = homepage for a website). Use the generic view ListView (django stuff)
class Index(ListView):
    
    # Override some of ListView's variables (django stuff)
    queryset = []
    context_object_name = "items"
    template_name = "main/index.html"
  
    # 2. Pass queryset to templates (django stuff)
    def get_context_data(self, *args, **kwargs):
        
        # Get, set, and return context (django stuff)
        context = super(Index, self).get_context_data(*args, **kwargs)
        context['queryset'] = self.queryset
        return context
    
    # 1. Get search form data, scrape results and pass it to queryset (django stuff)
    def get_queryset(self):
        
        # Base structure for the url we are going to search on ebay. Take users input and put them in {item}, {price_low}, and {price_high}. (django stuff)
        base_url = "https://www.ebay.com/sch/parser.html?_from=R40&_nkw={item}&_ipg=25"
        prices_url = "&_udlo={price_low}&_udhi={price_high}"
        
        # Get the text we typed into the search bar and price range bars (django stuff)
        item = self.request.GET.get('item')
        price_low = self.request.GET.get('from')
        price_high = self.request.GET.get('to')
        
        # If we are requesting a webpage, and a search item was given (both needed to tell eBay to give us a search result page) (django stuff)
        if self.request.method == 'GET' and item:
            
            # Construct (django stuff)
            item = "+".join(item.split())
            if price_low and price_high:
                url = (base_url + prices_url).format(item=item,price_low=price_low,price_high=price_high)
            else:
                url = base_url.format(item=item)
                
            # Create a Scraper object and run it (django stuff)
            scraper = Scraper(base_url=url)
            app = scraper.run()
            
            # Return the data we just scraped, so django can display it in the web app (django stuff)
            return app

        
# Scraper class
class Scraper(Index):
    
    # Constructor
    def __init__(self, base_url=None):
        super(Scraper, self).__init__()
        
        # Set the url we need to search
        self.base_url = base_url
        
        # Clear the queryset (if any is leftover from last time)
        self.queryset[:] = []

    # Start scraping the webpage of the url we constructed
    def run(self):
        try:
            # Create beautiful soup object with make_soup method (bs = BeautifulSoup)
            bs = self.make_soup(self.base_url)
            
            # If we didn't get an error
            if not bs.get('error'):
                
                # Scrape for the whole list of search result items. I'll call them "item-wrapper divs" (item-wrapper div = a search result listing on ebay)
                rows = bs.find_all('div', class_="s-item__wrapper")[:10]
                
                # Now loop through all of those items in the list, and scrape each of those individually
                for parser in rows:
                    self.parse_rows(parser)
                    
            # Error
            else:
                print(bs['error'])
                
        # Handle the error        
        except Exception as error:
            print(error)
            
        # We have scraped everything, so return the data
        return self.queryset
    
    # 3. Parse soup from make_soup method
    def parse_rows(self, parser):
        
        # Get name of item
        name = parser.find('h3', class_="s-item__title")
        if name:
            name = name.text
        else:
            name = ' '
            
        # Get link to the item's details page (the link we go to if we clicked on it)
        link = parser.find('a', class_="s-item__link")
        if link:
            link = link.get('href')
        else:
            link = ' '
            
        # Get secondary info on item (like "BRAND NEW")
        condition = parser.find('span', class_="SECONDARY_INFO")
        if condition:
            condition = condition.text
            
        # 
        price = parser.find('span', class_="s-item__price")
        if price:
            price = price.text
        else:
            price = ' '
            
        # 
        image = parser.find('img', class_="s-item__image-img").get('src')
        if image == 'https://ir.ebaystatic.com/cr/v/c1/s_1x2.gif':
            soup = self.make_soup(link)
            image = soup.find('img', {'id': "icImg"}).get('src')
            
        # 
        self.queryset.append(dict(name=name,link=link,condition=condition,price=price,image=image))

    # Make soup method (create beautiful soup object from our webpage)
    def make_soup(self, url):
        
        # Headers that eBay requires when doing a search get-request
        headers = {'Accept': '*/*',
                   'Accept-Encoding': 'gzip, deflate, sdch',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Cache-Control': 'max-age=0',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        
        # Request the url from eBay
        page = requests.get(url, headers=headers, timeout=15)
        
        # Ensure we have a success and create the beautiful soup object of the webpage (now ready for scraping)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "lxml")
        
        # Else return error
        else:
            soup = {'error': "We got status code %s" % page.status_code}
        
        # Return the beautiful soup object (now ready for scraping)
        return soup
