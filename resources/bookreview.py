from datetime import datetime

from db import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookreview import BookreviewModel


class Bookreview(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("star", type=int, required=True)
    parser.add_argument("comment", default="")

    def get(self, id):
        bookreview = (
            db.session.query(
                BookreviewModel.id,
                BookreviewModel.isbn,
                BookModel.title,
                BookModel.author,
                BookModel.description,
                BookModel.img,
                BookreviewModel.user_id,
                BookreviewModel.star,
                BookreviewModel.comment,
                BookreviewModel.updated_at
            )
            .join(BookModel, BookreviewModel.isbn == BookModel.isbn)
            .filter(BookreviewModel.id == id)
            .first()
        )

        if not bookreview:
            return {"message": "Bookreview not found"}, 404

        bookreview = {
            "id": bookreview.id,
            "isbn": bookreview.isbn,
            "title": bookreview.title,
            "author": bookreview.author,
            "description": bookreview.description,
            "img": bookreview.img,
            "user_id": bookreview.user_id,
            "star": bookreview.star,
            "comment": bookreview.comment,
            "updated_at": bookreview.updated_at.isoformat(),
        }

        return bookreview, 200

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()

        bookreview = BookreviewModel.find_by_id(id)

        if not bookreview:
            return {"message": "Bookreview not found"}, 404

        if user_id != bookreview.user_id:
            return {"message": "Cannot delete another user's review"}, 403

        bookreview.delete_from_db()
        return {"message": "Bookreview deleted."}, 200

    @jwt_required()
    def put(self, id):
        data = Bookreview.parser.parse_args()
        user_id = get_jwt_identity()

        bookreview = BookreviewModel.find_by_id(id)

        if not bookreview:
            return {"message": "Bookreview not found"}, 404

        if user_id != bookreview.user_id:
            return {"message": "Cannot update another user's review"}, 403

        bookreview.star = data["star"]
        bookreview.comment = data["comment"]
        bookreview.updated_at = datetime.now()

        bookreview.save_to_db()

        return bookreview.json(), 200


class BookreviewList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("isbn", required=True)
    parser.add_argument("title", required=True)
    parser.add_argument("author", default="")
    parser.add_argument("description", default="")
    parser.add_argument("img", default="")
    parser.add_argument("star", type=int, required=True)
    parser.add_argument("comment", default="")

    @jwt_required()
    def post(self):
        data = BookreviewList.parser.parse_args()
        user_id = get_jwt_identity()

        if not BookModel.find_by_isbn(data["isbn"]):
            book = BookModel(
                data["isbn"],
                data["title"],
                data["author"],
                data["description"],
                data["img"],
            )
            db.session.add(book)

        bookreview = BookreviewModel(
            data["isbn"], user_id, data["star"], data["comment"]
        )
        db.session.add(bookreview)
        db.session.commit()

        return {"message": "Bookreview created successfully"}, 201
