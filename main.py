from typing import List, Optional
from fastapi import FastAPI, Depends, Query, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse, RedirectResponse
import sqlite3
import mybible


class Module(BaseModel):
    id: str
    description: str
    origin: Optional[str]
    language: str
    region: Optional[str]


class Registry:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename, check_same_thread = False)
        self.cur = self.conn.cursor()

    def fetch(self, id: Optional[str] = None, language: Optional[str] = None, region: Optional[str] = None):
        clause = "AND ".join([f"{key} = ?" for key, value in [("id", id), ("language", language), ("region", region)] if value != None])
        parameters = [value for value in [id, language, region] if value != None]
        self.cur.execute(f"SELECT id, description, origin, language, region FROM modules {'WHERE ' + clause if clause else ''}", parameters)

        return [
            Module(id = id, description = description, origin = origin, language = language, region = region)
            for id, description, origin, language, region in self.cur.fetchall()
        ]

    def get(self, ids: List[str]):
        clause = f"id IN ({','.join(['?' for _ in range(len(ids))])})"
        query = f"SELECT id, description, origin, language, region FROM modules WHERE {clause}"
        self.cur.execute(query, ids)

        return [
            Module(id = id, description = description, origin = origin, language = language, region = region)
            for id, description, origin, language, region in self.cur.fetchall()
        ]

    def __del__(self):
        return self.conn.close()


app = FastAPI()
module = mybible.Module("RST+.SQLite3")
registry = Registry("Registry.SQLite3")

class APIException(Exception):
    pass


class VerseNotFoundException(APIException):
    def __init__(self):
        self.code = 101
        self.msg = "Verse not found"


class ChapterNotFoundException(APIException):
    def __init__(self):
        self.code = 301
        self.msg = "Chapter not found"


class BookNotFoundException(APIException):
    def __init__(self):
        self.code = 201
        self.msg = "Book not found"


@app.exception_handler(APIException)
def api_exception_handler(_: Request, exc: APIException):
    return JSONResponse(
        status_code = 400,
        content = {"error_code": exc.code, "error_msg": exc.msg}
    )

@app.get("/")
def docs_redirect():
    return RedirectResponse(url="/docs")


class Book(BaseModel):
    id: int
    short_name: str
    long_name: str

    class Config:
        schema_extra = {
            "example": {
                "id": 10,
                "short_name": "Быт",
                "long_name": "Бытие"
            }
        }


class Books(BaseModel):
    count: int
    items: List[Book]


@app.get("/books", response_model=Books)
def books():
    books = module.books()
    return Books(
        count = len(books),
        items = [
            Book(id = book.book_number(), short_name = book.short_name(), long_name = book.long_name())
            for book in books
        ]
    )


class BookIn:
    def __init__(self, id: int = Query(...)):
        self.id = id


class BookOut(BaseModel):
    id: int
    short_name: str
    long_name: str
    chapters: int

    class Config:
        schema_extra = {
            "example": {
                "id": 10,
                "short_name": "Быт",
                "long_name": "Быт",
                "chapters": 50
            }
        }


@app.get("/books.get", response_model=BookOut)
def book(req: BookIn = Depends()):
    id = req.id
    books = module.books()

    if books.contains(id):
        book = books.get(id)
        verses = module.verses()

        return BookOut(
                id = id, long_name = book.long_name(), short_name = book.short_name(),
                chapters = len(verses.get(id))
            )
    else:
        raise BookNotFoundException()


class VerseIn:
    def __init__(self, book: int = Query(...), chapter: int = Query(...), verse: int = Query(...)):
        self.book = book
        self.chapter = chapter
        self.verse = verse


class VerseOut(BaseModel):
    text: str

    class Config:
        schema_extra = {
            "example": {
                "text": "В начале сотворил Бог небо и землю."
            }
        }


@app.get("/verses.get", response_model=VerseOut)
def verse(req: VerseIn = Depends()):
    book, chapter, verse = req.book, req.chapter, req.verse
    verses = module.verses()

    if verses.contains(book, chapter, verse):
        return VerseOut(text = verses.get(book, chapter, verse).text())
    else:
        raise VerseNotFoundException()


class ChapterIn:
    def __init__(self, book_id: int = Query(...), chapter: int = Query(...)):
        self.book_id = book_id
        self.chapter = chapter


class ChapterOut(BaseModel):
    book_id: int
    chapter: int
    verses: int

    class Config:
        schema_extra = {
            "example": {
                "book_id": 10,
                "chapter": 1,
                "verses": 31
            }
        }


@app.get("/chapters.get", response_model=ChapterOut)
def chapter(req: ChapterIn = Depends()):
    book_id, chapter = req.book_id, req.chapter
    books = module.books()

    if books.contains(book_id):
        verses = module.verses()
        if verses.contains(book_id, chapter):
            return ChapterOut(
                book_id = book_id, chapter = chapter, verses = len(verses.get(book_id, chapter))
            )
        else:
            raise ChapterNotFoundException()
    else:
        raise BookNotFoundException()


class SearchModuleIn:
    def __init__(self, id: Optional[str] = None, language: Optional[str] = None, region: Optional[str] = None):
        self.id: Optional[str] = id
        self.language: Optional[str] = language
        self.region: Optional[str] = region


class SearchModuleOut(BaseModel):
    count: int
    items: List[Module]

    class Config:
        schema_extra = {
            "example": {
                "id": "RST+",
                "description": "Russian Synodal Bible",
                "origin": "The text is taken from the Open Bible project: https://openbibleproject.org. Public domain, no known copyrights on this text.",
                "language": "ru",
                "region": None
            }
        }


@app.get("/modules.search", response_model = SearchModuleOut)
def search_module(req: SearchModuleIn = Depends()):
    id, language, region = req.id, req.language, req.region
    result = registry.fetch(id, language, region)
    return SearchModuleOut(count = len(result), items = result)


class GetModuleIn:
    def __init__(self, ids: List[str] = Query(...)):
        self.ids: List[str] = ids


class GetModuleOut(BaseModel):
    count: int
    items: List[Module]


@app.get("/modules.get", response_model = GetModuleOut)
def get_module(req: GetModuleIn = Depends()):
    result = registry.get(req.ids)
    return GetModuleOut(count = len(result), items = result)
