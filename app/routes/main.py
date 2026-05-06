from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ticket, User
from app import db
from sqlalchemy import func
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Инициализация переменных для графиков и времени
    category_data = {}
    avg_resolve_time = "0 ч."

    if current_user.role == 'superadmin':
        # 1. Глобальная статистика (все заявки системы)
        open_tickets = Ticket.query.filter_by(status='Новая').count()
        my_in_progress = Ticket.query.filter_by(status='В работе').count()
        completed_tickets = Ticket.query.filter(Ticket.status.in_(['Решена', 'Закрыта'])).count()

        # 2. Сбор данных для графика (количество заявок по типам/категориям)
        category_stats = db.session.query(
            Ticket.category, func.count(Ticket.id)
        ).group_by(Ticket.category).all()
        category_data = {cat: count for cat, count in category_stats}

        # 3. Расчет среднего времени решения (в часах)
        # Условие: считаем только те, где заполнено время закрытия
        resolved_tickets = Ticket.query.filter(Ticket.closed_at.isnot(None)).all()
        if resolved_tickets:
            total_seconds = sum((t.closed_at - t.created_at).total_seconds() for t in resolved_tickets)
            avg_hours = (total_seconds / len(resolved_tickets)) / 3600
            avg_resolve_time = f"{avg_hours:.1f} ч."

    elif current_user.role == 'support':
        # Статистика только для отдела поддержки
        open_tickets = Ticket.query.filter_by(status='Новая', category=current_user.department).count()
        my_in_progress = Ticket.query.filter_by(assignee_id=current_user.id, status='В работе').count()
        completed_tickets = Ticket.query.filter(
            Ticket.assignee_id == current_user.id,
            Ticket.status.in_(['Решена', 'Закрыта'])
        ).count()
    else:
        # Статистика только для конкретного работника
        open_tickets = Ticket.query.filter_by(creator_id=current_user.id, status='Новая').count()
        my_in_progress = Ticket.query.filter_by(creator_id=current_user.id, status='В работе').count()
        completed_tickets = Ticket.query.filter(
            Ticket.creator_id == current_user.id,
            Ticket.status.in_(['Решена', 'Закрыта'])
        ).count()
    priority_data = {}
    support_load = {}

    if current_user.role == 'superadmin':
        # Группировка по приоритетам
        priority_stats = db.session.query(
            Ticket.priority, func.count(Ticket.id)
        ).group_by(Ticket.priority).all()
        priority_data = {p: c for p, c in priority_stats}

        # Группировка по исполнителям (кто сколько заявок взял в работу)
        # Соединяем таблицу Ticket и User, чтобы получить имена
        load_stats = db.session.query(
            User.username, func.count(Ticket.id)
        ).join(Ticket, Ticket.assignee_id == User.id)\
         .filter(Ticket.status == 'В работе')\
         .group_by(User.username).all()
        support_load = {u: c for u, c in load_stats}   

    return render_template('dashboard.html', 
                           open_tickets=open_tickets, 
                           my_in_progress=my_in_progress,
                           completed_tickets=completed_tickets,
                           category_data=category_data,
                           avg_resolve_time=avg_resolve_time, priority_data=priority_data,
                           support_load=support_load)

    