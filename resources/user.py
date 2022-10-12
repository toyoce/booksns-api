from blocklist import BLOCKLIST
from db import db
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_restful import Resource, reqparse
from models.book import BookModel
from models.bookrecord import BookrecordModel
from models.user import UserModel
from werkzeug.security import check_password_hash, generate_password_hash


class User(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("withRecords", type=int, default=0)

    def get(self, user_id):
        withRecords = User.parser.parse_args()["withRecords"]

        user = {"user_id": user_id}

        if withRecords:
            bookrecords = (
                db.session.query(
                    BookrecordModel.isbn,
                    BookrecordModel.user_id,
                    BookrecordModel.star,
                    BookrecordModel.comment,
                    BookModel.title,
                    BookModel.img,
                )
                .join(BookModel, BookrecordModel.isbn == BookModel.isbn)
                .filter(BookrecordModel.user_id == user_id)
                .all()
            )
            user["bookrecords"] = [
                {
                    "isbn": br.isbn,
                    "user_id": br.user_id,
                    "star": br.star,
                    "comment": br.comment,
                    "title": br.title,
                    "img": br.img,
                }
                for br in bookrecords
            ]

        return user, 200


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", required=True)
    parser.add_argument("password", required=True)

    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_user_id(data["user_id"]):
            return {"message": "A user with that username already exists."}, 400

        try:
            user = UserModel(data["user_id"], generate_password_hash(data["password"]))
            user.save_to_db()
        except:
            return {"message": "An error occurred saving the user to the database"}, 500

        return {"message": "User created successfully."}, 201


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", required=True)
    parser.add_argument("password", required=True)

    def post(self):
        data = UserLogin.parser.parse_args()

        user = UserModel.find_by_user_id(data["user_id"])

        if user and check_password_hash(user.password, data["password"]):
            access_token = create_access_token(identity=user.user_id, fresh=True)
            refresh_token = create_refresh_token(user.user_id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        return {"message": "Invalid credentials!"}, 401


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()
        BLOCKLIST.add(jti)
        return {"message": "User <id={}> successfully logged out.".format(user_id)}, 200


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200
