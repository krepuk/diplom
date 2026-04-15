import os
from app import create_app, db
from app.models import User, Ticket, Article, Comment

app = create_app()

def setup_database():
    with app.app_context():
        db.create_all()
        
        if not User.query.first():
            print("База данных пуста. Создаю стартовых пользователей...")
            
            # 1. Суперадмин
            superadmin = User(username='boss', email='boss@corp.com', phone='+111', role='superadmin')
            superadmin.set_password('123')

            # 2. Обычный Админ (support)
            admin_it = User(username='admin_it', email='it@corp.com', phone='+222', role='support', department='IT')
            admin_it.set_password('123')

            # 3. Работник
            worker = User(username='worker1', email='worker@corp.com', phone='+333', role='employee')
            worker.set_password('123')
            
            db.session.add_all([superadmin, admin_it, worker])
            db.session.commit()
            
            print("Пользователи созданы!")
            print("Суперадмин: логин 'boss', пароль '123'")
            print("Админ: логин 'admin_it', пароль '123'")
            print("Работник: логин 'worker1', пароль '123'")

if __name__ == '__main__':
    setup_database()
    app.run(debug=True, host='0.0.0.0', port=5000)