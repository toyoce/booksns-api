from db import db


class LikeModel(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    bookreview_id = db.Column(db.Integer, db.ForeignKey("bookreviews.id"))
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"))

    def __init__(self, bookreview_id, user_id):
        self.bookreview_id = bookreview_id
        self.user_id = user_id

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
