from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Ticket
from app.forms import TicketForm

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            creator_id=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Заявка успешно создана!', 'success')
        return redirect(url_for('tickets.list_tickets'))
    return render_template('tickets/create.html', form=form)

@tickets_bp.route('/list')
@login_required
def list_tickets():
    if current_user.role == 'support':
        # Поддержка видит новые заявки своей области и те, которые они взяли в работу
        tickets = Ticket.query.filter(
            (Ticket.category == current_user.department) & 
            ((Ticket.status == 'Новая') | (Ticket.assignee_id == current_user.id))
        ).order_by(Ticket.created_at.desc()).all()
    else:
        # Работник видит только свои заявки
        tickets = Ticket.query.filter_by(creator_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets/list.html', tickets=tickets)

@tickets_bp.route('/<int:id>')
@login_required
def detail(id):
    ticket = Ticket.query.get_or_404(id)
    return render_template('tickets/detail.html', ticket=ticket)

@tickets_bp.route('/take/<int:id>', methods=['POST'])
@login_required
def take_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    if current_user.role != 'support':
        flash('У вас нет прав для принятия заявок.', 'danger')
        return redirect(url_for('tickets.detail', id=ticket.id))
        
    if ticket.assignee_id is not None:
        flash('Эту заявку уже забрал другой сотрудник!', 'warning')
        return redirect(url_for('tickets.list_tickets'))
        
    ticket.assignee_id = current_user.id
    ticket.status = 'В работе'
    db.session.commit()
    flash('Вы приняли заявку в работу.', 'success')
    return redirect(url_for('tickets.detail', id=ticket.id))

@tickets_bp.route('/status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    ticket = Ticket.query.get_or_404(id)
    new_status = request.form.get('status')
    
    # Права: саппорт может менять на "Решена", а создатель на "Закрыта"
    if new_status in ['Решена', 'Закрыта']:
        ticket.status = new_status
        db.session.commit()
        flash(f'Статус заявки изменен на "{new_status}".', 'success')
        
    return redirect(url_for('tickets.detail', id=ticket.id))