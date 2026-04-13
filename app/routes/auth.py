from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required

from app import db
from app.models import User
from app.forms import LoginForm, CreateUserForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('main.dashboard'))
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    # Запрещаем доступ обычным работникам
    if current_user.role == 'employee':
        flash('У вас нет прав для доступа к этой странице.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = CreateUserForm()
    
    # Настраиваем доступные роли для создания
    if current_user.role == 'superadmin':
        form.role.choices = [('employee', 'Работник (Сотрудник)'), ('support', 'Админ (Поддержка)')]
    elif current_user.role == 'support':
        form.role.choices = [('employee', 'Работник (Сотрудник)')]
        # ВАЖНО: Если создает обычный админ, мы программно удаляем поле department, 
        # чтобы оно не ломало проверку формы из-за своей скрытности
        del form.department

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            role=form.role.data,
            # Если поле department не было удалено строкой выше - берем его значение
            department=form.department.data if hasattr(form, 'department') and form.role.data == 'support' else None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Пользователь {user.username} успешно создан!', 'success')
        return redirect(url_for('main.dashboard'))
    
    # Если форма отправлена, но есть ошибки (например, занят email)
    elif request.method == 'POST':
        flash('Форма не отправлена! Проверьте красные поля ниже.', 'danger')
        
    return render_template('auth/create_user.html', form=form)