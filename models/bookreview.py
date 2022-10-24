from datetime import datetime

from db import db


class BookreviewModel(db.Model):
    __tablename__ = "bookreviews"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), db.ForeignKey("books.isbn"))
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"))
    star = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, isbn, user_id, star, comment):
        self.isbn = isbn
        self.user_id = user_id
        self.star = star
        self.comment = comment
        self.updated_at = datetime.now()

    def json(self):
        return {
            "id": self.id,
            "isbn": self.isbn,
            "user_id": self.user_id,
            "star": self.star,
            "comment": self.comment,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_isbn(cls, isbn):
        return cls.query.filter_by(isbn=isbn).all()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
