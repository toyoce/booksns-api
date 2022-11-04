import os

import requests
from db import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookreview import BookreviewModel


class Book(Resource):
    def get(self, isbn):
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

            return book, 200

        return {"message": "Book not found."}, 404


class BookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("keyword", location="args", required=True)

    @jwt_required(optional=True)
    def get(self):
        keyword = BookList.parser.parse_args()["keyword"]
        user_id = get_jwt_identity()

        r = requests.get(
            os.getenv("RAKUTEN_BOOKS_API_URL"),
            params={
                "applicationId": os.getenv("RAKUTEN_APPLICATION_ID"),
                "formatVersion": 2,
                "elements": "title,author,isbn,largeImageUrl",
                "title": keyword,
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

        if user_id:
            res = (
                db.session.query(BookreviewModel.isbn)
                .filter(BookreviewModel.user_id == user_id)
                .all()
            )
            existing_isbns = [r.isbn for r in res]
            books = [b for b in books if b["isbn"] not in existing_isbns]

        return {"books": books}, 200


class HighlyRatedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", location="args", type=int, default=6)

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
    parser.add_argument("topn", location="args", type=int, default=6)

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
