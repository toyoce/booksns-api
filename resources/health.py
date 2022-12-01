from flask_restful import Resource


class Health(Resource):
    def get(self):
        return {"message": "Health check OK"}, 200
