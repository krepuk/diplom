from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Новое поле
    phone = db.Column(db.String(20), nullable=False)                # Новое поле
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='employee') # employee, support, superadmin
    department = db.Column(db.String(50)) # IT, 1C, HR (только для support)

    # Связи
    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.creator_id', backref='creator', lazy='dynamic')
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assignee_id', backref='assignee', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Новая')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)