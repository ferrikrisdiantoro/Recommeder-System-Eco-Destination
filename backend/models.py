from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Place(db.Model):
    __tablename__ = "places"
    id = db.Column(db.Integer, primary_key=True)
    place_name = db.Column(db.String(255), nullable=False)
    place_description = db.Column(db.Text, default="")
    category = db.Column(db.String(255), default="")
    city = db.Column(db.String(120), default="")
    address = db.Column(db.String(255), default="")
    price_num = db.Column(db.Float, default=0.0)
    price_str = db.Column(db.String(64), default="")
    rating_avg = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(500), default="")
    gallery1 = db.Column(db.String(500), default="")
    gallery2 = db.Column(db.String(500), default="")
    gallery3 = db.Column(db.String(500), default="")
    map_url = db.Column(db.String(500), default="")

class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
