from typing import List
from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
import sqlite3
from mybible import Module

app = FastAPI()
module = Module("RST+.SQLite3")


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
                "response": {
                    "text": "В начале сотворил Бог небо и землю."
                }
            }
        }


@app.get("/verse")
def verse(req: VerseIn = Depends()):
    book, chapter, verse = req.book, req.chapter, req.verse
    verses = module.verses()

    if verses.contains(book, chapter, verse):
        return {
            "response": {
                "text": verses.get(book, chapter, verse).text()
            }
        }
    else:
        return {
            "error": errors[VERSE_NOT_FOUND]
        }


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
                "response": {
                    "id": 10,
                    "short_name": "Быт",
                    "long_name": "Быт",
                    "chapters": 50
                }
            }
        }


@app.get("/book")
def book(req: BookIn = Depends()):
    id = req.id
    books = module.books()

    if books.contains(id):
        book = books.get(id)
        verses = module.verses()

        return {
            "response": BookOut(
                id = id, long_name = book.long_name(), short_name = book.short_name(),
                chapters = len(verses.get(id))
            )
        }
    else:
        return {
            "error": errors[BOOK_NOT_FOUND]
        }
