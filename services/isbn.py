"""ISBN validation and bounded, fault-tolerant book lookups."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
import re
import unicodedata
import os
import requests

_cache = OrderedDict()
_lock = Lock()


def normalize_isbn(value):
    isbn = re.sub(r"[\s-]", "", unicodedata.normalize("NFKC", str(value or ""))).upper()
    if re.fullmatch(r"\d{9}[\dX]", isbn):
        digits = [int(c) if c != "X" else 10 for c in isbn]
        if sum((10 - i) * n for i, n in enumerate(digits)) % 11:
            raise ValueError("ISBNのチェック桁が正しくありません")
        prefix = "978" + isbn[:9]
        return prefix + str((-sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(prefix))) % 10)
    if re.fullmatch(r"97[89]\d{10}", isbn):
        if sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(isbn)) % 10 == 0:
            return isbn
    raise ValueError("有効なISBN-10またはISBN-13を入力してください")


def _json(url, params):
    response = requests.get(url, params=params, timeout=(2, 3),
                            headers={"User-Agent": "SedoriStockApp/1.0 (ISBN lookup)"})
    response.raise_for_status()
    return response.json()


def openbd(isbn):
    result = _json("https://api.openbd.jp/v1/get", {"isbn": isbn})
    if not result or not result[0]:
        return None
    book = result[0].get("summary", {})
    return {"title": book.get("title"), "publisher": book.get("publisher"),
            "c_code": book.get("cno"), "source": "openBD"}


def google(isbn):
    params = {"q": "isbn:" + isbn, "maxResults": 5}
    if os.getenv("GOOGLE_BOOKS_API_KEY"):
        params["key"] = os.environ["GOOGLE_BOOKS_API_KEY"]
    result = _json("https://www.googleapis.com/books/v1/volumes", params)
    for item in result.get("items", []):
        book = item.get("volumeInfo", {})
        for identifier in book.get("industryIdentifiers", []):
            try:
                match = normalize_isbn(identifier.get("identifier")) == isbn
            except ValueError:
                continue
            if match:
                return {"title": book.get("title"), "publisher": book.get("publisher"),
                        "genre": next(iter(book.get("categories", [])), ""), "source": "Google Books"}
    return None


def openlibrary(isbn):
    key = "ISBN:" + isbn
    book = _json("https://openlibrary.org/api/books", {"bibkeys": key, "format": "json", "jscmd": "data"}).get(key)
    if not book:
        return None
    publishers = book.get("publishers", [])
    return {"title": book.get("title"), "publisher": publishers[0].get("name") if publishers else "",
            "source": "Open Library"}


PROVIDERS = (openbd, google, openlibrary)


def lookup(isbn):
    with _lock:
        cached = _cache.get(isbn)
        if cached and cached[0] > monotonic():
            _cache.move_to_end(isbn)
            return cached[1], cached[2]
    errors = []
    for provider in PROVIDERS:
        try:
            book = provider(isbn)
            if book and book.get("title"):
                book["isbn"] = isbn
                with _lock:
                    _cache[isbn] = (monotonic() + 3600, book, 200)
                    if len(_cache) > 512:
                        _cache.popitem(last=False)
                return book, 200
        except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError, IndexError):
            errors.append(provider.__name__)
    return {"message": "書誌APIに接続できません。手入力で登録できます。" if errors else
            "書誌情報が見つかりません。タイトルを手入力して登録できます。", "isbn": isbn}, 503 if errors else 404
