from typing import Optional
from fastapi import FastAPI
import sqlite3
from mybible import Module

app = FastAPI()
module = Module("RST+.SQLite3")

@app.get("/books")
def books():
    books = module.books()
    return {
        "response": {
            "count": len(books),
            "items": [
                {
                    "id": book.book_number(),
                    "short_name": book.short_name(),
                    "long_name": book.long_name()
                } for book in books
            ]
        }
    }