from typing import List
from fastapi import FastAPI
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


@app.get("/books")
def books():
    books = module.books()
    return {"response": Books(
        count = len(books),
        items = [
            Book(id = book.book_number(), short_name = book.short_name(), long_name = book.long_name())
            for book in books
        ]
    )}
