import sqlite3
from mybible import Module
from pathlib import Path

filename = input()
module = Module(filename)
info = module.info()

conn = sqlite3.connect("Registry.SQLite3")
cur = conn.cursor()

query = "INSERT INTO modules(filename, description, detailed_info, language, region) VALUES (?, ?, ?, ?, ?)"
cur.execute(query,
    (Path(filename).stem, info.get("description"), info.get("detailed_info"), info.get("language"), info.get("region"))
)
conn.commit()
