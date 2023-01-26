"""
Scraper V3
This version DOES NOT support client side rendering.
"""
import asyncio
import uuid

import httpx
import readability
from bs4 import BeautifulSoup
from ebooklib import epub
from readability import Document

from typing import TypedDict
from typing import List

from typing_extensions import NotRequired

# urls to scrape
URLS = [
    'https://meidea-translation.blogspot.com/2020/11/volume-1-prologue.html',
    'https://meidea-translation.blogspot.com/2020/11/maydare-volume-1-chapter-1-makia-and.html',
    # 'https://meidea-translation.blogspot.com/2020/11/maydare-volume-1-chapter-1-makia-and_14.html',
    # 'https://meidea-translation.blogspot.com/2020/11/maydare-volume-1-chapter-1-makia-and_21.html#more',
    # 'https://meidea-translation.blogspot.com/2020/11/maydare-volume-1-chapter-2-salt-forest.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-2-salt-forest.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-2-salt-forest_9.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-3-night-of.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-3-night-of_23.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-3-night-of_27.html',
    # 'https://meidea-translation.blogspot.com/2020/12/maydare-volume-1-chapter-3-night-of_29.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-4-lune-ruschia.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-4-lune-ruschia_5.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-4-lune-ruschia_8.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-4-lune-ruschia_15.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-5-entrance.html',
    # 'https://meidea-translation.blogspot.com/2021/01/maydare-volume-1-chapter-5-entrance_27.html',
    # 'https://meidea-translation.blogspot.com/2021/02/maydare-volume-1-chapter-6-spirit.html',
    # 'https://meidea-translation.blogspot.com/2021/02/maydare-volume-1-chapter-6-spirit_6.html',
    # 'https://meidea-translation.blogspot.com/2021/02/maydare-volume-1-chapter-6-spirit_12.html',
    # 'https://meidea-translation.blogspot.com/2021/02/maydare-volume-1-chapter-7-search-for.html',
    # 'https://meidea-translation.blogspot.com/2021/02/maydare-volume-1-chapter-7-search-for_28.html',
    # 'https://meidea-translation.blogspot.com/2021/03/maydare-volume-1-chapter-7-search-for.html',
    # 'https://meidea-translation.blogspot.com/2021/03/maydare-volume-1-chapter-8-potions.html',
    # 'https://meidea-translation.blogspot.com/2021/03/maydare-volume-1-chapter-8-potions_27.html',
    # 'https://meidea-translation.blogspot.com/2021/03/maydare-volume-1-chapter-8-potions_30.html',
    # 'https://meidea-translation.blogspot.com/2021/04/maydare-volume-1-chapter-9-potions.html',
    # 'https://meidea-translation.blogspot.com/2021/04/maydare-volume-1-chapter-9-potions_13.html',
    # 'https://meidea-translation.blogspot.com/2021/04/maydare-volume-1-chapter-9-potions_14.html',
    # 'https://meidea-translation.blogspot.com/2021/04/maydare-volume-1-chapter-10-ball-part-1.html',
    # 'https://meidea-translation.blogspot.com/2021/04/maydare-volume-1-chapter-10-ball-part-2.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-chapter-11-descendant.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-chapter-11-descendant_3.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-chapter-11-descendant_10.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-chapter-12-unfolding.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-chapter-12-unfolding_24.html',
    # 'https://meidea-translation.blogspot.com/2021/05/maydare-volume-1-behind-scenes-tanaka.html'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36',
    'referer': ""
}


async def get_page(client: httpx.AsyncClient, url: str, reader_mode=True):
    print(f'Downloading page at {url}')
    r = await client.get(url)

    if r.status_code != 200:
        print(f'[ERROR] Status code: {r.status_code}')
        return

    if reader_mode:
        doc = Document(r.content)
        print(doc.title())
        return url, doc

    soup = BeautifulSoup(r.text, 'html.parser')
    return url, soup


async def scrap(urls: List[str]):
    tasks = []

    # limit connections so server will not unexpectedly close connection
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits) as client:
        for url in urls:
            print(f'Loading page at {url}.')
            task = asyncio.create_task(get_page(client, url))
            tasks.append(task)

        success = await asyncio.gather(*tasks)
    return success


def epub_add_items(book: epub.EpubBook, items: List):
    if not items:
        return
    for i in items:
        book.add_item(i)


def create_epub(title="", authors: List[str] = None, lang="", identifier=str(uuid.uuid4()),
                chapters: List[epub.EpubHtml] = None, items: List[epub.EpubItem] = None):

    book = epub.EpubBook()
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(lang)

    for author in authors:
        book.add_author(author)

    epub_add_items(book, chapters)
    epub_add_items(book, items)

    toc = [epub.Link(chapter.file_name, chapter.title, chapter.id) for chapter in chapters]
    book.toc = toc

    book.spine = ['nav'] + [] if chapters is None else chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    return book


def to_safe_filename(unsafe_string):
    safe_string = ''.join([c for c in unsafe_string if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
    safe_string = safe_string.replace(' ', '_')
    return safe_string


def create_epub_html(title: str, content: str, lang="") -> epub.EpubHtml:
    c = epub.EpubHtml(title=title,
                      file_name=f"{to_safe_filename(title)}.xhtml",
                      lang=lang)
    c.set_content(content)
    return c


async def main():
    pages = await scrap(URLS)
    print("pages", pages)
    chapters = [create_epub_html(p.title(), p.summary(), "en") for _, p in pages]

    book = create_epub("Maydare", ["author"], chapters=chapters)
    epub.write_epub('test.epub', book)

if __name__ == "__main__":
    asyncio.run(main())

"""
loop = asyncio.get_event_loop()

tasks = [
    asyncio.async(func_normal()),
    asyncio.async(func_infinite())]

done, _ = loop.run_until_complete(asyncio.wait(tasks))
for fut in done:
    print("return value is {}".format(fut.result()))
loop.close()
"""
