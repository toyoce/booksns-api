import os

import requests
from db import db
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookrecord import BookrecordModel


class Book(Resource):
    parser_get = reqparse.RequestParser()
    parser_get.add_argument("withRecords", type=int, default=0)

    parser_put = reqparse.RequestParser()
    parser_put.add_argument("title", required=True)
    parser_put.add_argument("author")
    parser_put.add_argument("description")
    parser_put.add_argument("img")

    def get(self, isbn):
        withRecords = Book.parser_get.parse_args()["withRecords"]

        agg = (
            db.session.query(
                BookrecordModel.isbn,
                db.func.avg(BookrecordModel.star).label("star"),
                db.func.count().label("reviewCount"),
            )
            .filter(BookrecordModel.isbn == isbn)
            .group_by(BookrecordModel.isbn)
            .subquery()
        )
        book = (
            db.session.query(
                BookModel.isbn,
                BookModel.title,
                BookModel.author,
                BookModel.description,
                BookModel.img,
                agg.c.star,
                agg.c.reviewCount,
            )
            .outerjoin(agg, BookModel.isbn == agg.c.isbn)
            .filter(BookModel.isbn == isbn)
            .first()
        )

        if book:
            book = {
                "isbn": book.isbn,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "img": book.img,
                "star": book.star if book.star else 0,
                "reviewCount": book.reviewCount if book.reviewCount else 0,
            }

            if withRecords:
                bookrecords = (
                    db.session.query(BookrecordModel)
                    .filter(BookrecordModel.isbn == isbn)
                    .all()
                )
                book["bookrecords"] = [br.json() for br in bookrecords]

            return book, 200

        return {"message": "Book not found."}, 404

    def delete(self, isbn):
        book = BookModel.find_by_isbn(isbn)
        if book:
            book.delete_from_db()
            return {"message": "Book deleted."}, 200
        return {"message": "Book not found."}, 404

    def put(self, isbn):
        data = Book.parser_put.parse_args()

        book = BookModel.find_by_isbn(isbn)

        if book:
            book.title = data["title"]
            book.author = data["author"]
            book.description = data["description"]
            book.img = data["img"]
        else:
            book = BookModel(isbn, **data)

        book.save_to_db()

        return book.json(), 200


class BookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("keyword", required=True)

    def get(self):
        keyword = BookList.parser.parse_args()["keyword"]

        r = requests.get(
            os.getenv("RAKUTEN_BOOKS_API_URL"),
            params={
                "applicationId": os.getenv("RAKUTEN_APPLICATION_ID"),
                "formatVersion": 2,
                "elements": "title,author,isbn,largeImageUrl",
                "title": keyword,
                "hits": 10,
            },
        )
        books = r.json()["Items"]
        return {"books": books}, 200


class HighlyRatedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", type=int, default=6)

    def get(self):
        topn = HighlyRatedBookList.parser.parse_args()["topn"]

        agg = (
            db.session.query(
                BookrecordModel.isbn, db.func.avg(BookrecordModel.star).label("star")
            )
            .group_by(BookrecordModel.isbn)
            .subquery()
        )
        books = (
            db.session.query(agg, BookModel.img)
            .filter(agg.c.isbn == BookModel.isbn)
            .order_by(db.desc(agg.c.star))
            .limit(topn)
            .all()
        )

        books = [{"isbn": b.isbn, "img": b.img, "star": b.star} for b in books]
        return {"books": books}, 200


class MostReviewedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", type=int, default=6)

    def get(self):
        topn = MostReviewedBookList.parser.parse_args()["topn"]

        agg = (
            db.session.query(BookrecordModel.isbn, db.func.count().label("reviewCount"))
            .group_by(BookrecordModel.isbn)
            .subquery()
        )
        books = (
            db.session.query(agg, BookModel.img)
            .filter(agg.c.isbn == BookModel.isbn)
            .order_by(db.desc(agg.c.reviewCount))
            .limit(topn)
            .all()
        )

        books = [
            {"isbn": b.isbn, "img": b.img, "reviewCount": b.reviewCount} for b in books
        ]
        return {"books": books}, 200
