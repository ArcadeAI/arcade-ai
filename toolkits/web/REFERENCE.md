# Web Toolkit


|             |                |
|-------------|----------------|
| Name        | web |
| Package     | arcade_web |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | LLM tools for web-related tasks  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| ScrapeUrl | Scrape a URL using Firecrawl and return the data in specified formats. |
| CrawlWebsite | Crawl a website using Firecrawl. If the crawl is asynchronous, then returns the crawl ID. |
| GetCrawlStatus | Get the status of a Firecrawl 'crawl' that is either in progress or recently completed. |
| GetCrawlData | Get the data of a Firecrawl 'crawl' that is either in progress or recently completed. |
| CancelCrawl | Cancel an asynchronous crawl job that is in progress using the Firecrawl API. |
| MapWebsite | Map a website from a single URL to a map of the entire website. |


### ScrapeUrl
Scrape a URL using Firecrawl and return the data in specified formats.

#### Parameters
- `url`*(string, required)* URL to scrape
- `formats`*(array, optional)* Formats to retrieve. Defaults to ['markdown']., Valid values are 'markdown', 'html', 'rawHtml', 'links', 'screenshot', 'screenshot@fullPage'
- `only_main_content`*(boolean, optional)* Only return the main content of the page excluding headers, navs, footers, etc.
- `include_tags`*(array, optional)* List of tags to include in the output
- `exclude_tags`*(array, optional)* List of tags to exclude from the output
- `wait_for`*(integer, optional)* Specify a delay in milliseconds before fetching the content, allowing the page sufficient time to load.
- `timeout`*(integer, optional)* Timeout in milliseconds for the request

---

### CrawlWebsite
Crawl a website using Firecrawl. If the crawl is asynchronous, then returns the crawl ID.
If the crawl is synchronous, then returns the crawl data.

#### Parameters
- `url`*(string, required)* URL to crawl
- `exclude_paths`*(array, optional)* URL patterns to exclude from the crawl
- `include_paths`*(array, optional)* URL patterns to include in the crawl
- `max_depth`*(integer, optional)* Maximum depth to crawl relative to the entered URL
- `ignore_sitemap`*(boolean, optional)* Ignore the website sitemap when crawling
- `limit`*(integer, optional)* Limit the number of pages to crawl
- `allow_backward_links`*(boolean, optional)* Enable navigation to previously linked pages and enable crawling sublinks that are not children of the 'url' input parameter.
- `allow_external_links`*(boolean, optional)* Allow following links to external websites
- `webhook`*(string, optional)* The URL to send a POST request to when the crawl is started, updated and completed.
- `async_crawl`*(boolean, optional)* Run the crawl asynchronously

---

### GetCrawlStatus
Get the status of a Firecrawl 'crawl' that is either in progress or recently completed.

#### Parameters
- `crawl_id`*(string, required)* The ID of the crawl job

---

### GetCrawlData
Get the data of a Firecrawl 'crawl' that is either in progress or recently completed.

#### Parameters
- `crawl_id`*(string, required)* The ID of the crawl job

---

### CancelCrawl
Cancel an asynchronous crawl job that is in progress using the Firecrawl API.

#### Parameters
- `crawl_id`*(string, required)* The ID of the asynchronous crawl job to cancel

---

### MapWebsite
Map a website from a single URL to a map of the entire website.

#### Parameters
- `url`*(string, required)* The base URL to start crawling from
- `search`*(string, optional)* Search query to use for mapping
- `ignore_sitemap`*(boolean, optional)* Ignore the website sitemap when crawling
- `include_subdomains`*(boolean, optional)* Include subdomains of the website
- `limit`*(integer, optional)* Maximum number of links to return
