from db import db


class BookModel(db.Model):
    __tablename__ = "books"

    isbn = db.Column(db.String(13), primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(80))
    description = db.Column(db.String(600))
    img = db.Column(db.String(150))
    url = db.Column(db.String(150))

    def __init__(self, isbn, title, author, description, img, url):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.description = description
        self.img = img
        self.url = url

    def json(self):
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "img": self.img,
            "url": self.url,
        }

    @classmethod
    def find_by_isbn(cls, isbn):
        return cls.query.filter_by(isbn=isbn).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
