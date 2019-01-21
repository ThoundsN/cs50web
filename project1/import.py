import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    db.excute(" CREATE TABLE users(id SERIAL PRIMARY KEY,username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    db.excute(" CREATE TABLE books(id SERIAL PRIMARY KEY,isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")
    db.excute(" CREATE TABLE reviews(isbn VARCHAR NOT NULL,review VARCHAR NOT NULL, username VARCHAR NOT NULL, rating INTEGER NOT NULL)")


    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year":year})
        print(f"Added book {isbn} {title} {author} {year} ")
    db.commit()

if __name__ == "__main__":
    main()
