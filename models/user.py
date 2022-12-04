from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(102), nullable=False)
    avatar = db.Column(db.String(50))

    def __init__(self, user_id, password):
        self.user_id = user_id
        self.password = password

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
