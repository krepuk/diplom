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
    priority = db.Column(db.String(20), default='Средний') 
    status = db.Column(db.String(20), default='Новая')
    
    # НОВОЕ ПОЛЕ: Счетчик переоткрытий
    reopen_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade='all, delete')

    @property
    def comment_count(self):
        return self.comments.count()

    def has_new_reply(self, current_user_id):
        last_comment = self.comments.order_by(Comment.created_at.desc()).first()
        if last_comment and last_comment.author_id != current_user_id:
            return True
        return False
    
    @property
    def comment_count(self):
        return self.comments.count()

    def has_new_reply(self, current_user_id):
        last_comment = self.comments.order_by(Comment.created_at.desc()).first()
        if last_comment and last_comment.author_id != current_user_id:
            return True
        return False
    
    # --- НОВЫЕ ФУНКЦИИ ---
    @property
    def comment_count(self):
        """Возвращает общее количество комментариев в заявке"""
        return self.comments.count()

    def has_new_reply(self, current_user_id):
        """Проверяет, написал ли последний комментарий КТО-ТО ДРУГОЙ"""
        # Ищем самый свежий комментарий
        last_comment = self.comments.order_by(Comment.created_at.desc()).first()
        
        # Если комментарий есть, и его автор НЕ тот, кто сейчас смотрит на экран
        if last_comment and last_comment.author_id != current_user_id:
            return True
        return False
    
# НОВЫЙ КЛАСС ДЛЯ КОММЕНТАРИЕВ
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    
    author = db.relationship('User', backref='comments')

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False) # Вопрос
    content = db.Column(db.Text, nullable=False)      # Ответ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Кто написал эту статью (связь с пользователем)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='articles_created')