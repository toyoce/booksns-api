from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "svg"}


class Avatar(Resource):
    @jwt_required()
    def put(self):
        if "avatar" not in request.files:
            return {"message": "'avatar' is required field"}, 400

        avatar_img = request.files["avatar"]

        if avatar_img.filename == "":
            return {"message": "File is not selected"}, 400

        ext = os.path.splitext(avatar_img.filename)[1][1:]

        if ext not in ALLOWED_EXTENSIONS:
            return {"message": f"'{ext}' is not allowed extension"}, 400

        user_id = get_jwt_identity()
        filename = f"{user_id}.{ext}"

        target_dir = os.path.join(os.getenv("UPLOAD_DIR"), "avatar")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        avatar_img.save(os.path.join(target_dir, filename))

        return {"message": "Avatar uploaded successfully"}, 201
