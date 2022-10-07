from db import db
from flask_restful import Resource
from models.bookrecord import BookrecordModel


class BookrecordListPerBook(Resource):
    def get(self, isbn):
        bookrecords = (
            db.session.query(BookrecordModel).filter(BookrecordModel.isbn == isbn).all()
        )
        bookrecords = [br.json() for br in bookrecords]

        return {"bookrecords": bookrecords}, 200
