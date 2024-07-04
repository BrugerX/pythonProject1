import Browser
from utility.webscrapingUtil import maxIntElements,getLIDFromURL
import numpy as np

class MagazineOverview:

    def __init__(self,category,delaySeconds = 1):

        self.category = category
        self.delayTimeS = delaySeconds

        self.nrActivePages = None
        self.set_active_nr_pages()

        self.currentPage = 0
        self.scrapedLids = dict()
    def getDelayTime(self):
        return np.random.uniform(0,self.delayTimeS)

    def get_soup(self,pageNr):
        if (pageNr is None):
            return Browser.Browser.load_bs4(f"{Browser.CategoryOverview.getCategoryBaseURL()}{self.category}?sort=bidding_end_desc",delayTimeSeconds= self.getDelayTime())
        else:
            return Browser.Browser.load_bs4(f"{Browser.CategoryOverview.getCategoryBaseURL()}{self.category}?page={pageNr}", delayTimeSeconds= self.getDelayTime())

    def set_active_nr_pages(self):
        soup = self.get_soup(None)
        pageNrs= soup.find_all("a",{"class":"c-pagination__page-link c-link no-underline u-color-mid-gray"})
        self.nrActivePages = maxIntElements(pageNrs) #We get the highest page number

    def get_lids_from_page(self,pageNr):
        soup = self.get_soup(pageNr)
        lotCards = soup.find_all("a", {"class": "c-lot-card"})
        LIDs = []
        for card in lotCards:
            cardURL = card["href"]
            LIDs += [getLIDFromURL(cardURL)]
        return LIDs

    def __iter__(self):
        self.currentPage = 0
        return self

    def __next__(self):
        resultOfNext = self.get_lids_from_page(self.currentPage)
        self.currentPage += 1
        if(self.currentPage>self.nrActivePages):
            raise StopIteration

        return resultOfNext

    """
    
    @:return Return a list of LIDs of the given page
    """
    def __getitem__(self, item):
        return self.get_lids_from_page(item)

    def __len__(self):
        return self.nrActivePages


if __name__ == "__main__":
    testCategory = 599
    magazine = MagazineOverview(testCategory)
    print(magazine.nrActivePages)

    for idx,LIDs in enumerate(magazine):
        print(f"Lids nr {idx}: {LIDs}")
