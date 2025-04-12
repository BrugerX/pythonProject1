DEPRECATED: Old Catawiki webscraper - Catawiki updated their website and this is no longer maintained.

I got the idea for building an auction house webscraper after dabbling with importing jewelry from Indian trading websites and selling it on Lauritz.com.
I couldn't find any reliable auction house webscrapers, so I decided to webscrape the biggest auction house I could find online; Catawiki.

There are two main scripts, both of which utilize a simple threaded priority job queue to:

A) Get active lots.
B) Continuously scrape lots in order to get information that disappears after the lot is closed.
C) Finalize lots once they're closed and moving them out of the queueing system.

 It was only meant for internal use, so understanding the lingo is dependent on having access to the design documents (UML, notes, etc.)
