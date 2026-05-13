from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# ИНИЦИАЛИЗАЦИЯ РАСШИРЕНИЙ
# SQLAlchemy — ORM для работы с базой данных
db = SQLAlchemy()
migrate = Migrate()

# Flask-Login — управление сессиями пользователей
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Куда перенаправлять неавторизованных
login_manager.login_message = "Пожалуйста, войдите для доступа к этой странице."


def create_app(config_class=Config):
    """
    Фабрика приложений Flask.
    Создаёт и конфигурирует экземпляр приложения.
    """
    app = Flask(__name__)
    
    # Загрузка конфигурации из объекта Config 
    app.config.from_object(config_class)

    # ПОДКЛЮЧЕНИЕ РАСШИРЕНИЙ К ПРИЛОЖЕНИЮ
    db.init_app(app)          # Привязка БД
    migrate.init_app(app, db) # Привязка миграций
    login_manager.init_app(app) # Привязка системы логина

    # ИМПОРТ И РЕГИСТРАЦИЯ BLUEPRINTS
    from app.routes.auth import auth_bp          # Аутентификация (логин, логаут, регистрация)
    from app.routes.main import main_bp          # Главная страница, дашборд
    from app.routes.tickets import tickets_bp    # Заявки (CRUD + статусы)
    from app.routes.knowledge import knowledge_bp # База знаний (статьи)

    # Регистрация Blueprint'ов с указанием URL-префиксов (кроме auth и main)
    app.register_blueprint(auth_bp)                      # URL: /login, /logout и т.д.
    app.register_blueprint(main_bp)                      # URL: /, /dashboard
    app.register_blueprint(tickets_bp, url_prefix='/tickets')  # URL: /tickets/...
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge') # URL: /knowledge/...

    return app