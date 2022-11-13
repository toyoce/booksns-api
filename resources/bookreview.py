from datetime import datetime

from db import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookreview import BookreviewModel
from models.like import LikeModel


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
                BookreviewModel.updated_at,
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
    parser_get = reqparse.RequestParser()
    parser_get.add_argument("isbn", location="args")
    parser_get.add_argument("user_id", location="args")

    parser_post = reqparse.RequestParser()
    parser_post.add_argument("isbn", required=True)
    parser_post.add_argument("title", required=True)
    parser_post.add_argument("author", default="")
    parser_post.add_argument("description", default="")
    parser_post.add_argument("img", default="")
    parser_post.add_argument("url", default="")
    parser_post.add_argument("star", type=int, required=True)
    parser_post.add_argument("comment", default="")

    @jwt_required(optional=True)
    def get(self):
        data = BookreviewList.parser_get.parse_args()
        isbn = data["isbn"]
        user_id = data["user_id"]
        current_user_id = get_jwt_identity() or ""

        if not (isbn or user_id):
            return {"message": "isbn or user_id is required"}, 400

        if isbn and user_id:
            return {"message": "Cannot specify both isbn and user_id"}, 400

        if isbn:
            bookreviews = self.get_bookreviews_for_isbn(isbn, current_user_id)
        elif user_id:
            bookreviews = self.get_bookreviews_for_user_id(user_id, current_user_id)

        return {"bookreviews": bookreviews}, 200

    def get_bookreviews_for_isbn(self, isbn, current_user_id):
        fbr = (
            db.session.query(BookreviewModel)
            .filter(BookreviewModel.isbn == isbn)
            .subquery()
        )

        bookreviews = (
            db.session.query(
                fbr.c.id,
                db.func.max(fbr.c.user_id).label("user_id"),
                db.func.max(fbr.c.star).label("star"),
                db.func.max(fbr.c.comment).label("comment"),
                db.func.max(fbr.c.updated_at).label("updated_at"),
                db.func.sum(db.case((LikeModel.user_id != None, 1), else_=0)).label(
                    "like_count"
                ),
                db.func.sum(
                    db.case((LikeModel.user_id == current_user_id, 1), else_=0)
                ).label("my_like"),
            )
            .outerjoin(LikeModel, fbr.c.id == LikeModel.bookreview_id)
            .group_by(fbr.c.id)
            .all()
        )

        bookreviews = [
            {
                "id": br.id,
                "user_id": br.user_id,
                "star": int(br.star),
                "comment": br.comment,
                "updated_at": br.updated_at.isoformat(),
                "like_count": int(br.like_count),
                "my_like": int(br.my_like),
            }
            for br in bookreviews
        ]

        return bookreviews

    def get_bookreviews_for_user_id(self, user_id, current_user_id):
        fbr = (
            db.session.query(BookreviewModel)
            .filter(BookreviewModel.user_id == user_id)
            .subquery()
        )

        agg = (
            db.session.query(
                fbr.c.id,
                db.func.max(fbr.c.isbn).label("isbn"),
                db.func.max(fbr.c.star).label("star"),
                db.func.max(fbr.c.comment).label("comment"),
                db.func.max(fbr.c.updated_at).label("updated_at"),
                db.func.sum(db.case((LikeModel.user_id != None, 1), else_=0)).label(
                    "like_count"
                ),
                db.func.sum(
                    db.case((LikeModel.user_id == current_user_id, 1), else_=0)
                ).label("my_like"),
            )
            .outerjoin(LikeModel, fbr.c.id == LikeModel.bookreview_id)
            .group_by(fbr.c.id)
            .subquery()
        )

        bookreviews = (
            db.session.query(
                agg.c.id,
                agg.c.isbn,
                BookModel.title,
                BookModel.img,
                agg.c.star,
                agg.c.comment,
                agg.c.updated_at,
                agg.c.like_count,
                agg.c.my_like,
            )
            .join(BookModel, agg.c.isbn == BookModel.isbn)
            .all()
        )

        bookreviews = [
            {
                "id": br.id,
                "isbn": br.isbn,
                "title": br.title,
                "img": br.img,
                "star": int(br.star),
                "comment": br.comment,
                "updated_at": br.updated_at.isoformat(),
                "like_count": int(br.like_count),
                "my_like": int(br.my_like),
            }
            for br in bookreviews
        ]

        return bookreviews

    @jwt_required()
    def post(self):
        data = BookreviewList.parser_post.parse_args()
        user_id = get_jwt_identity()

        existing_bookreview = (
            db.session.query(BookreviewModel)
            .filter(BookreviewModel.isbn == data["isbn"])
            .filter(BookreviewModel.user_id == user_id)
            .first()
        )

        if existing_bookreview:
            return {"message": "Cannot review the same book twice."}, 400

        if not BookModel.find_by_isbn(data["isbn"]):
            book = BookModel(
                data["isbn"],
                data["title"],
                data["author"],
                data["description"],
                data["img"],
                data["url"],
            )
            db.session.add(book)

        bookreview = BookreviewModel(
            data["isbn"], user_id, data["star"], data["comment"]
        )
        db.session.add(bookreview)
        db.session.commit()

        return {"message": "Bookreview created successfully"}, 201
