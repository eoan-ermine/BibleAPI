from typing import List
from fastapi import FastAPI, Depends, Query, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import sqlite3
from mybible import Module

app = FastAPI()
module = Module("RST+.SQLite3")


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


@app.get("/verse", response_model=VerseOut)
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


@app.get("/chapter", response_model=ChapterOut)
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
