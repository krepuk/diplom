from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Ticket

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'support':
        # Статистика для поддержки
        open_tickets = Ticket.query.filter_by(status='Новая', category=current_user.department).count()
        my_in_progress = Ticket.query.filter_by(assignee_id=current_user.id, status='В работе').count()
        
        # Считаем выполненные (Решена или Закрыта) для конкретного саппорта
        completed_tickets = Ticket.query.filter(
            Ticket.assignee_id == current_user.id,
            Ticket.status.in_(['Решена', 'Закрыта'])
        ).count()
    else:
        # Статистика для работника
        open_tickets = Ticket.query.filter_by(creator_id=current_user.id, status='Новая').count()
        my_in_progress = Ticket.query.filter_by(creator_id=current_user.id, status='В работе').count()
        
        # Считаем выполненные заявки работника
        completed_tickets = Ticket.query.filter(
            Ticket.creator_id == current_user.id,
            Ticket.status.in_(['Решена', 'Закрыта'])
        ).count()
    
    return render_template('dashboard.html', 
                           open_tickets=open_tickets, 
                           my_in_progress=my_in_progress,
                           completed_tickets=completed_tickets)