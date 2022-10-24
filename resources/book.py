import os

import requests
from db import db
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookreview import BookreviewModel


class Book(Resource):
    parser_get = reqparse.RequestParser()
    parser_get.add_argument("withReviews", type=int, default=0)

    parser_put = reqparse.RequestParser()
    parser_put.add_argument("title", required=True)
    parser_put.add_argument("author")
    parser_put.add_argument("description")
    parser_put.add_argument("img")

    def get(self, isbn):
        withReviews = Book.parser_get.parse_args()["withReviews"]

        agg = (
            db.session.query(
                BookreviewModel.isbn,
                db.func.avg(BookreviewModel.star).label("star"),
                db.func.count().label("reviewCount"),
            )
            .filter(BookreviewModel.isbn == isbn)
            .group_by(BookreviewModel.isbn)
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
                "star": float(book.star) if book.star else 0,
                "reviewCount": book.reviewCount if book.reviewCount else 0,
            }

            if withReviews:
                bookreviews = (
                    db.session.query(BookreviewModel)
                    .filter(BookreviewModel.isbn == isbn)
                    .all()
                )
                book["bookreviews"] = [br.json() for br in bookreviews]

            return book, 200

        r = requests.get(
            os.getenv("RAKUTEN_BOOKS_API_URL"),
            params={
                "applicationId": os.getenv("RAKUTEN_APPLICATION_ID"),
                "formatVersion": 2,
                "elements": "title,author,isbn,itemCaption,largeImageUrl",
                "isbn": isbn,
                "hits": 1,
            },
        )

        if r.status_code == 200 and "Items" in r.json().keys():
            book = r.json()["Items"][0]
            book = {
                "isbn": book["isbn"],
                "title": book["title"],
                "author": book["author"],
                "description": book["itemCaption"],
                "img": book["largeImageUrl"],
                "star": 0,
                "reviewCount": 0,
            }

            if withReviews:
                book["bookreviews"] = []

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
        books = [
            {
                "isbn": b["isbn"],
                "title": b["title"],
                "author": b["author"],
                "img": b["largeImageUrl"],
            }
            for b in books
        ]
        return {"books": books}, 200


class HighlyRatedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", type=int, default=6)

    def get(self):
        topn = HighlyRatedBookList.parser.parse_args()["topn"]

        agg = (
            db.session.query(
                BookreviewModel.isbn, db.func.avg(BookreviewModel.star).label("star")
            )
            .group_by(BookreviewModel.isbn)
            .subquery()
        )
        books = (
            db.session.query(agg, BookModel.img)
            .filter(agg.c.isbn == BookModel.isbn)
            .order_by(db.desc(agg.c.star))
            .limit(topn)
            .all()
        )

        books = [{"isbn": b.isbn, "img": b.img, "star": float(b.star)} for b in books]
        return {"books": books}, 200


class MostReviewedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", type=int, default=6)

    def get(self):
        topn = MostReviewedBookList.parser.parse_args()["topn"]

        agg = (
            db.session.query(BookreviewModel.isbn, db.func.count().label("reviewCount"))
            .group_by(BookreviewModel.isbn)
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
