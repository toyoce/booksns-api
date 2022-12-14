from db import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse
from models.bookreview import BookreviewModel
from models.like import LikeModel


class LikeList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("bookreview_id", type=int, required=True)

    @jwt_required()
    def post(self):
        bookreview_id = LikeList.parser.parse_args()["bookreview_id"]
        user_id = get_jwt_identity()

        bookreview = BookreviewModel.find_by_id(bookreview_id)

        if not bookreview:
            return {"message": "Bookreview not found"}, 400

        if user_id == bookreview.user_id:
            return {"message": "Cannot like you own review."}, 400

        existing_like = (
            db.session.query(LikeModel)
            .filter(LikeModel.bookreview_id == bookreview_id)
            .filter(LikeModel.user_id == user_id)
            .first()
        )

        if existing_like:
            return {"message": "Cannot like the same bookreview twice."}, 400

        like = LikeModel(bookreview_id, user_id)
        like.save_to_db()

        return {"message": "Like created successfully."}, 200

    @jwt_required()
    def delete(self):
        bookreview_id = LikeList.parser.parse_args()["bookreview_id"]
        user_id = get_jwt_identity()

        like = (
            db.session.query(LikeModel)
            .filter(LikeModel.bookreview_id == bookreview_id)
            .filter(LikeModel.user_id == user_id)
            .first()
        )

        if not like:
            return {"message": "Like not found"}, 404

        if user_id != like.user_id:
            return {"message": "Cannot delete another user's like"}, 403

        like.delete_from_db()

        return {"message": "Like deleted."}, 200
