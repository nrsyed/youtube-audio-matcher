from concurrent.futures import ThreadPoolExecutor
import os
import re
import time
import pdb

import bs4
import selenium.webdriver


def get_videos_page_url(url):
    """
    Get the videos page URL from a YouTube channel/user URL. See
    https://support.google.com/youtube/answer/6180214?hl=en

    Returns:
        URL for videos page if valid URL, else None.
    """
    expr = r"^.*(/(c(hannel)?|u(ser)?)/[a-zA-Z0-9-_]+)"
    match = re.match(expr, url)

    if match:
        videos_page_path = match.groups()[0]
        return f"https://www.youtube.com{videos_page_path}/videos"
    return None


def _get_source(url, init_wait_time=2, scroll_wait_time=0.5):
    """
    Get source for the page at `url` by scrolling to the end of the page.

    Args:
        url (str): URL for webpage.
        init_wait_time (float): Initial wait time (in seconds) for page load.
        scroll_wait_time (float): Subsequent wait time (in seconds) for
            page scrolls.
    """
    # TODO: incorporate timeout
    # TODO: hide browser window
    driver = selenium.webdriver.Chrome()
    driver.get(url)
    time.sleep(init_wait_time)

    source = None
    scroll_by = 5000
    while source != driver.page_source:
        source = driver.page_source
        driver.execute_script(f"window.scrollBy(0, {scroll_by});")
        time.sleep(scroll_wait_time)
    driver.quit()
    return source


def get_source(urls, init_wait_time=2, scroll_wait_time=0.5, max_workers=None):
    """
    Threaded wrapper for _get_source() that takes a list of URLs, concurrently
    fetches the page source of each URL, and returns the page source(s).

    Args:
        urls (List[str]): A list of page URLs.

    Returns:
        A list containing the page source for each input URL.
    """
    thread_pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []
    for url in urls:
        futures.append(
            thread_pool.submit(
                _get_source, url, init_wait_time=init_wait_time,
                scroll_wait_time=scroll_wait_time
            )
        )
    thread_pool.shutdown()
    source_list = [future.result() for future in futures]
    return source_list


if __name__ == "__main__":
    urls = [
        "https://www.youtube.com/channel/UCmSynKP6bHIlBqzBDpCeQPA/featured",
        "www.youtube.com/c/GlitchxCity/featured",
        "https://www.youtube.com/c/creatoracademy/",
        #"https://www.youtube.com/user/CAVEMAN2019/morestuff",
        #"https://www.youtube.com/u/dummy/okiedokie",
    ]

    urls = [get_videos_page_url(url) for url in urls]
    print(urls)
    sources = get_source(urls)
    breakpoint()
