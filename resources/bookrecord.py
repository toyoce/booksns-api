from db import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookrecord import BookrecordModel


class Bookrecord(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("star", type=int, required=True)
    parser.add_argument("comment", default="")

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()

        bookrecord = BookrecordModel.find_by_id(id)

        if not bookrecord:
            return {"message": "Bookrecord not found"}, 404

        if user_id != bookrecord.user_id:
            return {"message": "Cannot delete another user's review"}, 403

        bookrecord.delete_from_db()
        return {"message": "Bookrecord deleted."}, 200

    @jwt_required()
    def put(self, id):
        data = Bookrecord.parser.parse_args()
        user_id = get_jwt_identity()

        bookrecord = BookrecordModel.find_by_id(id)

        if not bookrecord:
            return {"message": "Bookrecord not found"}, 404

        if user_id != bookrecord.user_id:
            return {"message": "Cannot update another user's review"}, 403

        bookrecord.star = data["star"]
        bookrecord.comment = data["comment"]

        bookrecord.save_to_db()

        return bookrecord.json(), 200


class BookrecordList(Resource):
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
        data = BookrecordList.parser.parse_args()
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

        bookrecord = BookrecordModel(
            data["isbn"], user_id, data["star"], data["comment"]
        )
        db.session.add(bookrecord)
        db.session.commit()

        return {"message": "Bookrecord created successfully"}, 201
