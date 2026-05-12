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
    category_data = {}
    priority_data = {}
    support_load = {}
    total_by_category = {}
    avg_resolve_time = "0 ч."

    if current_user.role == 'superadmin':
        open_tickets = Ticket.query.filter_by(status='Новая').count()
        my_in_progress = Ticket.query.filter_by(status='В работе').count()
        completed_tickets = Ticket.query.filter(Ticket.status.in_(['Решена', 'Закрыта'])).count()

        cat_stats = db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
        category_data = {c: count for c, count in cat_stats}

        prio_stats = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        priority_data = {p: count for p, count in prio_stats}

        load_stats = db.session.query(User.username, func.count(Ticket.id))\
            .join(Ticket, Ticket.assignee_id == User.id)\
            .filter(Ticket.status == 'В работе')\
            .group_by(User.username).all()
        support_load = {u: count for u, count in load_stats}

        resolved = Ticket.query.filter(Ticket.closed_at.isnot(None)).all()
        if resolved:
            total_sec = sum((t.closed_at - t.created_at).total_seconds() for t in resolved)
            avg_resolve_time = f"{(total_sec / len(resolved)) / 3600:.1f} ч."

        all_time_stats = db.session.query(Ticket.category, func.count(Ticket.id))\
            .group_by(Ticket.category).order_by(func.count(Ticket.id).desc()).all()
        total_by_category = {cat: count for cat, count in all_time_stats}

    elif current_user.role == 'support':
        open_tickets = Ticket.query.filter_by(status='Новая', category=current_user.department).count()
        my_in_progress = Ticket.query.filter_by(assignee_id=current_user.id, status='В работе').count()
        completed_tickets = Ticket.query.filter(Ticket.assignee_id == current_user.id, Ticket.status.in_(['Решена', 'Закрыта'])).count()
    else:
        open_tickets = Ticket.query.filter_by(creator_id=current_user.id, status='Новая').count()
        my_in_progress = Ticket.query.filter_by(creator_id=current_user.id, status='В работе').count()
        completed_tickets = Ticket.query.filter(Ticket.creator_id == current_user.id, Ticket.status.in_(['Решена', 'Закрыта'])).count()

    return render_template('dashboard.html', 
                           open_tickets=open_tickets, 
                           my_in_progress=my_in_progress,
                           completed_tickets=completed_tickets,
                           category_data=category_data,
                           priority_data=priority_data,
                           support_load=support_load,
                           avg_resolve_time=avg_resolve_time, 
                           total_by_category=total_by_category)