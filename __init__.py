import re
import string
from queue import Queue
from typing import List, Optional, Tuple
from urllib.parse import quote
from datetime import datetime
import locale

from calibre import browser
from calibre.ebooks.metadata import check_isbn
from calibre.ebooks.metadata.book.base import Metadata
from calibre.ebooks.metadata.sources.base import Option, Source, fixauthors
from calibre.utils.config_base import tweaks
from calibre.utils.date import parse_only_date
from calibre.utils.logging import Log
from lxml import html

class DLsiteMetadata(Source):
    name = "DLsite Metadata"
    author = "volition"
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    description = _("Downloads metadata and covers from DLsite")

    capabilities = frozenset(("identify", "cover"))
    touched_fields = frozenset(
        (
            "title",
            "authors",
            "comments",
            "publisher",
            "pubdate",
            "languages",
            "series",
            "tags",
            "identifier:dlsite",
        )
    )
    has_html_comments = True
    supports_gzip_transfer_encoding = True

    BASE_URL = "https://www.dlsite.com"

    COUNTRIES = {
        "ja_JP": _("日本語"),
        "en_US": _("English"),
        "zh_CN": _("简体中文"),
        "zh_TW": _("繁體中文"),
        "ko_KR": _("한국어"),
        "es_ES": _("Español"),
        "de_DE": _("Deutsch"),
        "fr_FR": _("Français"),
        "id_ID": _("Bahasa Indonesia"),
        "it_IT": _("Italiano"),
        "pt_BR": _("Português"),
        "sv_SE": _("Svenska"),
        "th_TH": _("ภาษาไทย"),
        "vi_VN": _("Tiếng Việt"),
    }

    TRANSLATIONS = {
        "ja_JP": {
            "Author1": "著者",
            "Publisher": "出版社名",
            "Circle": "サークル名",
            "Label": "レーベル",
            "Release-date": "販売日",
            "format": "%Y年%m月%d日",
            "Author2": "作者",
            "Series-name": "シリーズ名",
            "Event": "イベント",
            "Comic-Market": "コミックマーケット",
            "Genre": "ジャンル"
        },
        "en_US": {
            "Author1": "Author",
            "Publisher": "Publisher",
            "Circle": "Circle",
            "Label": "Label",
            "Release-date": "Release date",
            "format": "%b/%d/%Y",
            "Author2": "Author",
            "Series-name": "Series Name",
            "Event": "Event",
            "Comic-Market": "Comic Market ",
            "Genre": "Genre"
        },
        "zh_CN": {
            "Author1": "作者",
            "Publisher": "出版社名",
            "Circle": "社团名",
            "Label": "标签",
            "Release-date": "贩卖日",
            "format": "%Y年%m月%d日",
            "Author2": "作者",
            "Series-name": "系列名",
            "Event": "活动",
            "Comic-Market": "CM（ComicMarket）",
            "Genre": "分类"
        },
        "zh_TW": {
            "Author1": "作者",
            "Publisher": "出版社名",
            "Circle": "社團名",
            "Label": "品牌",
            "Release-date": "販賣日",
            "format": "%Y年%m月%d日",
            "Author2": "作者",
            "Series-name": "系列名",
            "Event": "活動",
            "Comic-Market": "CM（ComicMarket）",
            "Genre": "分類"
        },
        "ko_KR": {
            "Author1": "저자",
            "Publisher": "출판사명",
            "Circle": "서클명",
            "Label": "라벨",
            "Release-date": "판매일",
            "format": "%Y년 %m월 %d일",
            "Author2": "저자",
            "Series-name": "시리즈명",
            "Event": "이벤트",
            "Comic-Market": "코믹마켓 ",
            "Genre": "장르"
        },
        "es_ES": {
            "Author1": "Autor",
            "Publisher": "Editor",
            "Circle": "Círculo",
            "Label": "Etiqueta",
            "Release-date": "Lanzamiento",
            "format": "%m/%d/%Y",
            "Author2": "Autor",
            "Series-name": "Serie",
            "Event": "Evento",
            "Comic-Market": "Mercado de Cómics ",
            "Genre": "Género"
        },
        "de_DE": {
            "Author1": "Autor",
            "Publisher": "Herausgeber",
            "Circle": "Kreis",
            "Label": "Label",
            "Release-date": "Veröffentlicht",
            "format": "%d/%m/%Y",
            "Author2": "Autor",
            "Series-name": "Serie",
            "Event": "Event",
            "Comic-Market": "コミックマーケット",
            "Genre": "Genre"
        },
        "fr_FR": {
            "Author1": "Auteur",
            "Publisher": "1%",
            "Circle": "1%",
            "Label": "Label",
            "Release-date": "Date de sortie",
            "format": "%d/%m/%Y",
            "Author2": "Auteur",
            "Series-name": "Série",
            "Event": "Événement",
            "Comic-Market": "Comic Market ",
            "Genre": "Genre"
        },
        "id_ID": {
            "Author1": "Pengarang",
            "Publisher": "Nama Penerbit",
            "Circle": "Nama Circle",
            "Label": "Label",
            "Release-date": "Tanggal rilis",
            "format": "%d/%m/%Y",
            "Author2": "Penulis",
            "Series-name": "Nama seri",
            "Event": "Event",
            "Comic-Market": "Komiket ",
            "Genre": "Genre"
        },
        "it_IT": {
            "Author1": "autore",
            "Publisher": ":casa editrice nome",
            "Circle": ":Circolo nome",
            "Label": "Etichetta",
            "Release-date": "Data di rilascio",
            "format": "%d/%m/%Y",
            "Author2": "Autore",
            "Series-name": "Serie",
            "Event": "Evento.",
            "Comic-Market": "コミックマーケット",
            "Genre": "Genere"
        },
        "pt_BR": {
            "Author1": "Autor",
            "Publisher": "Editora pessoa(s)",
            "Circle": "Círculo pessoa(s)",
            "Label": "Selo",
            "Release-date": "Lançamento",
            "format": "%d/%m/%Y",
            "Author2": "Autor",
            "Series-name": "Série",
            "Event": "Evento",
            "Comic-Market": "コミックマーケット",
            "Genre": "Gênero"
        },
        "sv_SE": {
            "Author1": "Författare",
            "Publisher": "Utgivare",
            "Circle": "Cirkel",
            "Label": "Label",
            "Release-date": "Utgivningsdatum",
            "format": "%d/%m/%Y",
            "Author2": "Författare",
            "Series-name": "Serier",
            "Event": "Händelse",
            "Comic-Market": "コミックマーケット",
            "Genre": "Genre"
        },
        "th_TH": {
            "Author1": "ผู้เขียน",
            "Publisher": "สำนักพิมพ์ คน",
            "Circle": "เซอร์เคิล คน",
            "Label": "ค่ายเพลง",
            "Release-date": "วันที่ขาย",
            "format": "%d/%m/%Y",
            "Author2": "ผู้เขียน",
            "Series-name": "ชื่อซีรี่ส์",
            "Event": "อีเวนต์",
            "Comic-Market": "コミックマーケット",
            "Genre": "ประเภท"
        },
        "vi_VN": {
            "Author1": "Tác giả",
            "Publisher": "Nhà xuất bản Tên",
            "Circle": "Nhóm Tên",
            "Label": "Nhãn dán",
            "Release-date": "Ngày phát hành",
            "format": "%d/%m/%Y",
            "Author2": "Tác giả",
            "Series-name": "Bộ truyện",
            "Event": "Sự kiện",
            "Comic-Market": "コミックマーケット",
            "Genre": "Thể loại"
        },
    }

    options = (
        Option(
            "country",
            "choices",
            "日本語",
            _("DLsite country store to use"),
            _("Metadata from DLsite will be fetched from this store"),
            choices=COUNTRIES,
        ),
        Option(
            "num_matches",
            "number",
            1,
            _("Number of matches to fetch"),
            _(
                "How many possible matches to fetch metadata for. If applying metadata in bulk, "
                "there is no use setting this above 1. Otherwise, set this higher if you are "
                "having trouble matching a specific book."
            ),
        ),
        Option(
            "title_blacklist",
            "string",
            "",
            _("Blacklist words in the title"),
            _("Comma separated words to blacklist"),
        ),
        Option(
            "tag_blacklist",
            "string",
            "",
            _("Blacklist tags"),
            _("Comma separated tags to blacklist"),
        ),
        Option(
            "remove_leading_zeroes",
            "bool",
            False,
            _("Remove leading zeroes"),
            _("Remove leading zeroes from numbers in the title"),
        ),
    )

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)

    def get_book_url(self, identifiers) -> Optional[Tuple]:
        product_id = identifiers.get("dlsite", None)
        if product_id:
            return ("product_id", product_id, f"{self.BASE_URL}/books/work/=/product_id/{product_id}?locale={self.prefs['country']}")
        return None

    def get_cached_cover_url(self, identifiers) -> Optional[str]:
        product_id = identifiers.get("dlsite", None)

        if product_id is not None:
            return self.cached_identifier_to_cover_url(product_id)

        return None

    def identify(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
    ) -> None:
        log.info(f"DLsiteMetadata::identify: title: {title}, authors: {authors}, identifiers: {identifiers}")

        product_id = identifiers.get("dlsite", None)
        urls = []

        if product_id:
            log.info(f"DLsiteMetadata::identify: Getting metadata with product_id: {product_id}")
            # product_id searches will (sometimes) redirect to the product page
            url = f"{self.BASE_URL}/books/work/=/product_id/{product_id}?locale={self.prefs['country']}"
            product_id_urls = self._get_webpage(url, log, timeout)
            if product_id_urls:
                urls.append(url)
                log.info(f"DLsiteMetadata::identify: Getting metadata with url: {url}")
        else:
            query = self._generate_query(title, authors)
            log.info(f"DLsiteMetadata::identify: Searching with query: {query}")

            if query:
                urls.extend(self._perform_query(query, log, timeout))

        index = 0
        for url in urls:
            log.info(f"DLsiteMetadata::identify: Looking up metadata with url: {url} index: {index}")
            try:
                metadata = self._lookup_metadata(url, log, timeout)
            except Exception as e:
                log.error(f"DLsiteMetadata::identify: Got exception looking up metadata: {e}")
                return

            if metadata:
                metadata.source_relevance = index
                if len(urls) != 1:
                    metadata.isbn = metadata.identifiers['dlsite']
                result_queue.put(metadata)
            else:
                log.info("DLsiteMetadata::identify:: Could not find matching book")
            index += 1
        return

    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
        get_best_cover=False,
    ) -> None:
        cover_url = self.get_cached_cover_url(identifiers)
        if not cover_url:
            log.info("DLsiteMetadata::download_cover: No cached url found, running identify")
            res_queue = Queue()
            self.identify(log, res_queue, abort, title, authors, identifiers, timeout)
            if res_queue.empty():
                log.error("DLsiteMetadata::download_cover: Could not identify book")
                return

            metadata = res_queue.get()
            cover_url = self.get_cached_cover_url(metadata)
        if not cover_url:
            log.error("DLsiteMetadata::download_cover: Could not find cover")

        br = self._get_browser()
        try:
            cover = br.open_novisit(cover_url, timeout=timeout).read()
        except Exception as e:
            log.error(f"DLsiteMetadata::download_cover: Got exception while opening cover url: {e}")
            return

        result_queue.put((self, cover))

    def _get_search_url(self, search_str: str) -> str:
        return f"{self.BASE_URL}/maniax/fsr/=/language/jp/sex_category%5B0%5D/male/keyword/{quote(search_str)}"

    def _generate_query(self, title: str, authors: list[str]) -> str:
        # Remove leading zeroes from the title if configured
        # DLsite search doesn't do a great job of matching numbers
        title = " ".join(
            x.lstrip("0") if self.prefs["remove_leading_zeroes"] else x
            for x in self.get_title_tokens(title, strip_joiners=False, strip_subtitle=False)
        )

        if authors:
            for author in authors:
                title += " " + author

        return title

    def _get_browser(self) -> browser:
        br: browser = self.browser
        br.set_header(
            "User-Agent",
            "Mozilla/5.0 (Linux; Android 8.0.0; VTR-L29; rv:63.0) Gecko/20100101 Firefox/63.0",
        )
        return br

    # Returns [lxml html element, is search result]
    def _get_webpage(self, url: str, log: Log, timeout: int) -> Tuple[Optional[html.Element], bool]:
        br = self._get_browser()
        try:
            resp = br.open_novisit(url, timeout=timeout)
            tree = html.fromstring(resp.read())
            is_search = "/keyword" in resp.geturl()
            return (tree, is_search)
        except Exception as e:
            log.error(f"DLsiteMetadata::_get_webpage: Got exception while opening url: {e}")
            return (None, False)

    # Returns a list of urls that match our search
    def _perform_query(self, query: str, log: Log, timeout: int) -> list[str]:
        url = self._get_search_url(query)
        log.info(f"DLsiteMetadata::identify: Searching for book with url: {url}")

        tree, is_search = self._get_webpage(url, log, timeout)
        if tree is None:
            log.info(f"DLsiteMetadata::_lookup_metadata: Could not get url: {url}")
            return []

        # Query redirected straight to product page
        if not is_search:
            return [url]

        results = self._get_search_matches(tree, log)

        i = 1

        while len(results) < self.prefs["num_matches"] and i < self.prefs["num_matches"]:
            url = self._get_search_url(query)
            tree, is_search = self._get_webpage(url, log, timeout)
            assert tree and is_search
            results.extend(self._get_search_matches(tree, log))
            i += 1

        return results[: self.prefs["num_matches"]]

    def _get_search_matches(self, page: html.Element, log: Log) -> List[str]:
        try:
            if len(page.xpath("//div[@id='search_result_list']")):
                log.info("DLsiteMetadata::_get_search_matches: Detected new search page")
                result_elements = page.xpath("//div[@class='multiline_truncate']/a")
                return [x.get("href") for x in result_elements]
        
        except Exception as e:
            log.error(f"DLsiteMetadata::_get_webpage: Got exception while opening matches: {e}")
            return []

    # Given the url for a book, parse and return the metadata
    def _lookup_metadata(self, url: str, log: Log, timeout: int) -> Optional[Metadata]:
        tree, is_search = self._get_webpage(url, log, timeout)
        if tree is None or is_search:
            log.info(f"DLsiteMetadata::_lookup_metadata: Could not get url: {url}")
            return None

        title_elements = tree.xpath("//li[@class='topicpath_item'][last()]/a/span")
        title = title_elements[0].text.strip()
        log.info(f"DLsiteMetadata::_lookup_metadata: Got title: {title}")

        metadata = Metadata(title)
        metadata.identifiers = { 'dlsite': url.rsplit('/', 1)[-1].split('.')[0].split('?')[0]}
        log.info(f"DLsiteMetadata::_lookup_metadata: Got identifiers: {metadata.identifiers}")
        tags = []

        locale.setlocale(locale.LC_TIME, f"{self.prefs['country']}.UTF-8")

        book_maker_elements = tree.xpath("//table[@id='work_maker']/tr")
        if book_maker_elements:
            log.info(f"DLsiteMetadata::_lookup_metadata: Got book_maker_elements")
            for x in book_maker_elements:
                descriptor = x.xpath("th")[0].text.strip()
                if descriptor == self.TRANSLATIONS[self.prefs['country']]['Author1']:
                    authors_elements = x.xpath("td/a")
                    metadata.authors = fixauthors([x.text for x in authors_elements])
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got authors: {metadata.authors}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Publisher']:
                    metadata.publisher = x.xpath("//span/a")[0].text
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got publisher: {metadata.publisher}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Circle']:
                    tags.append("group." + x.xpath("//span/a")[0].text)
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got group: {tags}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Label']:
                    tags.append("label." + x.xpath("//span/a")[0].text)
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got label: {tags}")

        book_details_elements = tree.xpath("//table[@id='work_outline']/tr")
        if book_details_elements:
            log.info(f"DLsiteMetadata::_lookup_metadata: Got book_details_elements")
            for x in book_details_elements:
                descriptor = x.xpath("th")[0].text.strip()
                if descriptor == self.TRANSLATIONS[self.prefs['country']]['Release-date']:
                    pubdate = x.xpath("td/a")[0].text
                    metadata.pubdate = datetime.strptime(pubdate, self.TRANSLATIONS[self.prefs['country']]['format'])
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got pubdate: {metadata.pubdate}")
                if descriptor == self.TRANSLATIONS[self.prefs['country']]['Author2']:
                    authors_elements = x.xpath("td/a")
                    metadata.authors = fixauthors([x.text for x in authors_elements])
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got authors: {metadata.authors}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Series-name']:
                    metadata.series = x.xpath("td/a")[0].text
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got series: {metadata.series}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Event']:
                    event = x.xpath("//span[@class='icon_EVT']/a")[0].text.replace(self.TRANSLATIONS[self.prefs['country']]['Comic-Market'], "C")
                    tags.append(f"event.{event}")
                    log.info(f"DLsiteMetadata::_lookup_metadata: Got event: {event}")
                elif descriptor == self.TRANSLATIONS[self.prefs['country']]['Genre']:
                    tags_elements = x.xpath("//div[@class='main_genre']/a")
                    if tags_elements:
                        # Calibre doesnt like commas in tags
                        for x in tags_elements:
                            tags.append("genre." + x.text)
                        log.info(f"DLsiteMetadata::_lookup_metadata: Got tags: {tags}")

        if tags:
            metadata.tags = [x.replace(',', ' ') for x in tags]

        synopsis_elements = tree.xpath("//div[@class='work_parts_area']")
        if synopsis_elements:
            metadata.comments = html.tostring(synopsis_elements[0], method="html")
            log.info(f"DLsiteMetadata::_lookup_metadata: Got comments: {metadata.comments}")

        cover_elements = tree.xpath("//picture/source/img")
        if cover_elements:
            cover_url = "https:" + cover_elements[0].get("srcset")
            self.cache_identifier_to_cover_url(metadata.identifiers['dlsite'], cover_url)
            log.info(f"DLsiteMetadata::_lookup_metadata: Got cover: {cover_url}")

        blacklisted_title = self._check_title_blacklist(title, log)
        if blacklisted_title:
            log.info(f"DLsiteMetadata::_lookup_metadata: Hit blacklisted word(s) in the title: {blacklisted_title}")
            return None

        blacklisted_tags = self._check_tag_blacklist(metadata.tags, log)
        if blacklisted_tags:
            log.info(f"DLsiteMetadata::_lookup_metadata: Hit blacklisted tag(s): {blacklisted_tags}")
            return None

        return metadata

    # Returns the set of words in the title that are also blacklisted
    def _check_title_blacklist(self, title: str, log: Log) -> set[str]:
        if not self.prefs["title_blacklist"]:
            return None

        blacklisted_words = {x.strip().lower() for x in self.prefs["title_blacklist"].split(",")}
        log.info(f"DLsiteMetadata::_check_title_blacklist: blacklisted title words: {blacklisted_words}")
        # Remove punctuation from title string
        title_str = title.translate(str.maketrans("", "", string.punctuation))
        return blacklisted_words.intersection(title_str.lower().split(" "))

    # Returns the set of tags that are also blacklisted
    def _check_tag_blacklist(self, tags: set[str], log: Log) -> set[str]:
        if not self.prefs["tag_blacklist"]:
            return None

        blacklisted_tags = {x.strip().lower() for x in self.prefs["tag_blacklist"].split(",")}
        log.info(f"DLsiteMetadata::_check_tag_blacklist: blacklisted tags: {blacklisted_tags}")
        return blacklisted_tags.intersection({x.lower() for x in tags})
