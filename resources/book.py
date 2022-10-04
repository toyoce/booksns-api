from db import db
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookrecord import BookrecordModel


class Book(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("title", required=True)
    parser.add_argument("author")
    parser.add_argument("description")
    parser.add_argument("img")

    def get(self, isbn):
        book = BookModel.find_by_isbn(isbn)
        if book:
            return book.json(), 200
        return {"message": "Book not found."}, 404

    def delete(self, isbn):
        book = BookModel.find_by_isbn(isbn)
        if book:
            book.delete_from_db()
            return {"message": "Book deleted."}, 200
        return {"message": "Book not found."}, 404

    def put(self, isbn):
        data = Book.parser.parse_args()

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


class HighlyRatedBookList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("topn", type=int, default=6)

    def get(self):
        topn = HighlyRatedBookList.parser.parse_args()["topn"]

        aggregated = (
            db.session.query(
                BookrecordModel.isbn, db.func.avg(BookrecordModel.star).label("star")
            )
            .group_by(BookrecordModel.isbn)
            .subquery("aggregated")
        )
        bookrecords = (
            db.session.query(aggregated, BookModel.img)
            .filter(aggregated.c.isbn == BookModel.isbn)
            .order_by(db.desc(aggregated.c.star))
            .limit(topn)
            .all()
        )

        bookrecords = [
            {"isbn": br.isbn, "img": br.img, "star": br.star} for br in bookrecords
        ]
        return {"bookrecords": bookrecords}, 200
