from typing import List
from fastapi import FastAPI, Depends, Query, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import sqlite3
from mybible import Module

app = FastAPI()
module = Module("RST+.SQLite3")


class VerseNotFoundException(Exception):
    def __init__(self):
        self.code = 101
        self.msg = "Verse not found"


@app.exception_handler(VerseNotFoundException)
def verse_not_found_exception_handler(_: Request, exc: VerseNotFoundException):
    return JSONResponse(
        status_code = 400,
        content = {"error_code": exc.code, "error_msg": exc.msg}
    )


class BookNotFoundException(Exception):
    def __init__(self):
        self.code = 201
        self.msg = "Book not found"


@app.exception_handler(BookNotFoundException)
def book_not_found_exception_handler(_: Request, exc: BookNotFoundException):
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
    return {"response": Books(
        count = len(books),
        items = [
            Book(id = book.book_number(), short_name = book.short_name(), long_name = book.long_name())
            for book in books
        ]
    )}


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


@app.get("/book", response_model=BookOut)
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