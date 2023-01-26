import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

from readability import Document
from bs4 import BeautifulSoup
import re
from ebooklib import epub
import uuid
import urllib
import requests
from urllib.parse import urlparse
import zipfile

from PIL import Image
import base64
from io import BytesIO

DRIVER_PATH = 'chromedriver_win32/chromedriver.exe'  # ENSURE chromedriver version matches chrome version
CHROME = ''
BRAVE = 'C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe'


# urls to scrape (more will be added if AUTO_ADVANCE is True)
urls = [
    'https://dobelyuwai.wordpress.com/2021/03/24/to-be-a-power-in-the-shadows-ln-v4-prologue-part-1/'
]

html_files = []
saved_images = []

AUTO_ADVANCE = True  # if true, bot will try to find the link to the next chapter in the current chapter
USE_HEADER = True  # if true, bot will try to find header (title of each chapter) in html body
USE_SHORT_TITLE = False  # if true, bot will use the shorten webpage title instead of the full webpage title as header
ADD_HEADER_TO_BODY = False  # if true, the header will be added to the body (set to false if body already has header)
USE_SELENIUM = False

# TITLE = 'Kidnapped Dragons WN'
# AUTHORS = ['Yuzu']

TITLE = 'To Be a Power in the Shadows! (LN) V4 - Unofficial Translation'
AUTHORS = ['Aizawa Daisuke']
LANGUAGE = 'en'


def main():
    start_time = time.time()

    # get directory ready for images
    if not os.path.isdir('Images/'):
        os.mkdir('Images/')

    if len(urls) != 0:
        driver = create_driver()
        for i, url in enumerate(urls):
            print(f'[Message] Loading {url}')
            html = get_clean_page(url, driver)
            html_files.append(html)
            print(f'[Message] Parsed as {html["header"]}')

    else:
        print('[ERROR] No source provided!')
        return

    epub_filename = generate_epub()

    # add images to .epub file
    '''
    epub_zip = zipfile.ZipFile(epub_filename, 'a')
    for img in saved_images:
        epub_zip.write(img['filename'], 'Epub/' + img['filename'])
    '''

    # clean directory used for images
    for f in os.listdir('Images/'):
        os.unlink('Images/' + f)
    os.rmdir('Images/')

    elapse = round(time.time() - start_time, 2)
    print(f'[Message] Scraping finished in {elapse} seconds. Epub saved as {to_safe_filename(TITLE)}.epub')


def to_safe_filename(unsafe_string):
    safe_string = ''.join([c for c in unsafe_string if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
    safe_string = safe_string.replace(' ', '_')
    return safe_string


def generate_epub():
    book = epub.EpubBook()

    # set metadata
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(TITLE)
    book.set_language(LANGUAGE)

    for author in AUTHORS:
        book.add_author(author)
        # book.add_author('Danko Bananko', file_as='Gospodin Danko Bananko', role='ill', uid='coauthor')

    toc = []
    chapters = []

    # create cover page
    cover = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang=LANGUAGE)
    cover.content = f'<h1>{TITLE}</h1><br><br>'
    for author in AUTHORS:
        cover.content += f'<hr>{author}</h4>'

    book.add_item(cover)
    chapters.append(cover)
    toc.append(epub.Link('cover' + '.xhtml', 'Cover', 'id_cover'))

    # TODO
    for img in saved_images:
        img_item = epub.EpubImage()
        img_item.file_name = img['filename']
        img_item.id = img['id']
        img_item.content = img['image']
        book.add_item(img_item)

    # add nov(TOC) to right after cover
    chapters.append('nav')

    # add all chapters
    for i, html in enumerate(html_files):
        # create chapter
        chapter = epub.EpubHtml(title=html['header'], file_name=to_safe_filename(html['header']) + '.xhtml', lang='hr')
        chapter.content = html['page']

        # add chapter
        book.add_item(chapter)

        chapters.append(chapter)
        toc.append(epub.Link(to_safe_filename(html['header']) + '.xhtml', html['header'], f'id_{i}'))

    # define Table Of Contents
    book.toc = toc

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    # add CSS file
    book.add_item(nav_css)

    # basic spine
    book.spine = chapters

    # write to the file
    epub.write_epub(f'{to_safe_filename(TITLE)}.epub', book, {})

    # return filename
    return f'{to_safe_filename(TITLE)}.epub'


def get_clean_page(url, driver):
    if USE_SELENIUM:
        source = get_page_with_selenium(url, driver)
    else:
        source = get_page(url)

    doc = Document(source)

    # print('[TITLE]' + doc.title())
    # print(doc.summary())
    soup = BeautifulSoup(doc.summary(), 'html.parser')

    # convert img src to base64
    images = soup.find_all('img')
    for image in images:
        src = image.get('src')

        # get file name
        parsed_src = urlparse(src)
        filename = os.path.basename(parsed_src.path)

        # get format
        img_format = src.split('?')[0].split('.')[len(src.split('.')) - 1]
        img_format = img_format.upper()
        if img_format == 'JPG':
            img_format = 'JPEG'

        '''
        Original base64 Image Storage
        
        # get image
        im = Image.open(requests.get(src, stream=True).raw)

        # image to base64
        buffered = BytesIO()
        im.save(buffered, save_all=True, format=img_format.lower())

        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        image['src'] = 'data:image/' + img_format + ';base64,' + img_str
        print(f'[Message] Converted image source from {src} to base64')
        '''

        '''
        New Item Type Storage
        '''
        buffered = BytesIO()
        urllib.request.urlretrieve(src, 'Images/' + filename)
        img_id = str(uuid.uuid4())
        saved_images.append({'id': img_id, 'filename': 'Images/' + filename, 'image': open('Images/' + filename, 'rb').read()})
        image['src'] = 'Images/' + filename
        image['id'] = img_id

        # remove all other src
        image['srcset'] = ''

    headers = soup.find_all(re.compile('^h[1-6]$'))

    # find next and prev button for chapters
    anchors = soup.find_all('a')

    # do auto advance if true and remove next and prev button for chapters
    for anchor in anchors:
        text = anchor.get_text()
        if 'next' in text.lower():
            next_anchor = anchor
            if AUTO_ADVANCE:
                urls.append(next_anchor.get('href'))
            next_anchor.decompose()
        elif 'prev' in text.lower():
            prev_anchor = anchor
            prev_anchor.decompose()

    if USE_HEADER and len(headers) == 1:
        header = headers[0].get_text()
    elif USE_SHORT_TITLE:
        header = doc.short_title()
    else:
        header = doc.title()

    if ADD_HEADER_TO_BODY:
        new_html_string = f'<h2>{header}</h2>{soup.prettify()}'
        soup = BeautifulSoup(new_html_string, 'html.parser')

    return {'header': header, 'page': soup.prettify()}


def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')  # Last I checked this was necessary.
    # options.add_argument('--enable-features=ReaderMode')
    options.binary_location = BRAVE
    driver_path = DRIVER_PATH
    driver = webdriver.Chrome(options=options, executable_path=driver_path)
    return driver


def get_page_with_selenium(url, driver):
    driver.get(url)

    try:
        html = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'html'))
        )

    except EC.WebDriverException:
        print(f'[ERROR] Failed to locate main body!')

    return html.get_attribute('innerHTML')


def get_page(url):
    page = urllib.request.urlopen(url).read()

    soup = BeautifulSoup(page, 'html.parser')

    # remove all scripts from dom
    scripts = soup.find_all('script')
    for script in scripts:
        script.decompose()

    # remove all link(ref) from dom
    links = soup.find_all('link')
    for link in links:
        link.decompose()

    return soup.prettify()


if __name__ == '__main__':
    main()
