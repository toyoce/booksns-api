from blocklist import BLOCKLIST
from db import db
from flask import jsonify
from flask_jwt_extended import (create_access_token, get_jwt, jwt_required,
                                set_access_cookies, unset_jwt_cookies)
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookreview import BookreviewModel
from models.user import UserModel
from werkzeug.security import check_password_hash, generate_password_hash


class User(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("withReviews", type=int, default=0)

    def get(self, user_id):
        withReviews = User.parser.parse_args()["withReviews"]

        user = {"user_id": user_id}

        if withReviews:
            bookreviews = (
                db.session.query(
                    BookreviewModel.id,
                    BookreviewModel.isbn,
                    BookreviewModel.user_id,
                    BookreviewModel.star,
                    BookreviewModel.comment,
                    BookreviewModel.updated_at,
                    BookModel.title,
                    BookModel.img,
                )
                .join(BookModel, BookreviewModel.isbn == BookModel.isbn)
                .filter(BookreviewModel.user_id == user_id)
                .all()
            )
            user["bookreviews"] = [
                {
                    "id": br.id,
                    "isbn": br.isbn,
                    "user_id": br.user_id,
                    "star": br.star,
                    "comment": br.comment,
                    "updated_at": br.updated_at.isoformat(),
                    "title": br.title,
                    "img": br.img,
                }
                for br in bookreviews
            ]

        return user, 200


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", required=True)
    parser.add_argument("password", required=True)

    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_user_id(data["user_id"]):
            return {"message": "A user with that user_id already exists."}, 409

        try:
            user = UserModel(data["user_id"], generate_password_hash(data["password"]))
            user.save_to_db()
        except:
            return {"message": "An error occurred saving the user to the database"}, 500

        response = jsonify({"message": "User created successfully"})
        access_token = create_access_token(identity=user.user_id)
        set_access_cookies(response, access_token)

        return response


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", required=True)
    parser.add_argument("password", required=True)

    def post(self):
        data = UserLogin.parser.parse_args()

        user = UserModel.find_by_user_id(data["user_id"])

        if user and check_password_hash(user.password, data["password"]):
            response = jsonify({"message": "Logged in successfully"})
            access_token = create_access_token(identity=user.user_id)
            set_access_cookies(response, access_token)

            return response

        return {"message": "Invalid credentials!"}, 401


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)

        response = jsonify({"message": "Logged out successfully"})
        unset_jwt_cookies(response)

        return response
