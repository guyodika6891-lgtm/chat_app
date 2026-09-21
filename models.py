from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_seen = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    rooms = db.relationship('Room', backref='creator', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='author', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Room {self.name}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)  # ← nullable for media-only messages
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    # Media fields (NEW)
    media_type = db.Column(db.String(20), nullable=True)   # 'image', 'audio', 'video', 'voice'
    media_filename = db.Column(db.String(255), nullable=True)
    media_original_name = db.Column(db.String(255), nullable=True)
    media_size = db.Column(db.Integer, nullable=True)      # in bytes

    def __repr__(self):
        return f'<Message by {self.author.username}>'