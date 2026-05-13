from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from app.models import Ticket, Comment
from app.forms import TicketForm, CommentForm 

tickets_bp = Blueprint('tickets', __name__)

#СОЗДАНИЕ ТИКЕТА
@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            priority=form.priority.data, 
            creator_id=current_user.id  
        )
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for('tickets.list_tickets'))
    return render_template('tickets/create.html', form=form)


#СПИСОК ТИКЕТОВ (РОЛЕВАЯ ФИЛЬТРАЦИЯ)
@tickets_bp.route('/list')
@login_required
def list_tickets():
    # Суперадмин: видит только "проблемные" тикеты (переоткрытые 3+ раза)
    if current_user.role == 'superadmin':
        tickets = Ticket.query.filter(Ticket.reopen_count >= 3).order_by(Ticket.created_at.desc()).all()
    
    # Сотрудник поддержки: тикеты своего отдела 
    elif current_user.role == 'support':
        tickets = Ticket.query.filter(
            (Ticket.category == current_user.department) & 
            ((Ticket.status == 'Новая') | (Ticket.assignee_id == current_user.id))
        ).order_by(Ticket.created_at.desc()).all()
    
    # Обычный пользователь: только свои тикеты
    else:
        tickets = Ticket.query.filter_by(creator_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        
    return render_template('tickets/list.html', tickets=tickets)


#ПОДРОБНОСТИ ТИКЕТА + КОММЕНТАРИИ 
@tickets_bp.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def detail(id):
    ticket = Ticket.query.get_or_404(id)
    form = CommentForm()

    # Обработка нового комментария
    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            author_id=current_user.id,
            ticket_id=ticket.id
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('tickets.detail', id=ticket.id))

    # Сортировка комментариев по возрастанию (старые сверху)
    comments = ticket.comments.order_by(Comment.created_at.asc()).all()

    return render_template('tickets/detail.html', ticket=ticket, form=form, comments=comments)


#ВЗЯТЬ ТИКЕТ В РАБОТУ
@tickets_bp.route('/take/<int:id>', methods=['POST'])
@login_required
def take_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Суперадмин: может забрать "проблемный" тикет (3+ переоткрытий)
    if current_user.role == 'superadmin':
        if ticket.reopen_count >= 3:
            old_assignee = ticket.assignee.username if ticket.assignee else "Не назначен"
            ticket.assignee_id = current_user.id
            
            # Системный комментарий 
            sys_comment = Comment(
                text=f"Суперадмин забрал заявку под свой контроль (предыдущий исполнитель: {old_assignee}).", 
                author_id=current_user.id, 
                ticket_id=ticket.id
            )
            db.session.add(sys_comment)
            db.session.commit()
            return redirect(url_for('tickets.detail', id=ticket.id))
        else:
            return redirect(url_for('tickets.detail', id=ticket.id))

    # Только поддержка может брать обычные тикеты
    if current_user.role != 'support':
        flash('У вас нет прав для принятия обычных заявок.', 'danger')
        return redirect(url_for('tickets.detail', id=ticket.id))
    
    # Защита от повторного назначения
    if ticket.assignee_id is not None:
        return redirect(url_for('tickets.list_tickets'))
        
    # Назначение и смена статуса
    ticket.assignee_id = current_user.id
    ticket.status = 'В работе'
    db.session.commit()
    return redirect(url_for('tickets.detail', id=ticket.id))


#ИЗМЕНЕНИЕ СТАТУСА ТИКЕТА
@tickets_bp.route('/status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    ticket = Ticket.query.get_or_404(id)
    new_status = request.form.get('status')
    
    # Окончательные статусы: фиксируем время закрытия
    if new_status in ['Решена', 'Закрыта']:
        ticket.status = new_status
        ticket.closed_at = datetime.utcnow() 
        db.session.commit()

    # Переоткрытие: увеличиваем счётчик, система фиксирует эскалацию
    elif new_status == 'Переоткрыть':
        ticket.status = 'В работе'
        ticket.reopen_count += 1
        
        system_msg = f"Заявка переоткрыта пользователем. (Попытка {ticket.reopen_count})"
        if ticket.reopen_count >= 3:
            system_msg += " Внимание! Заявка передана на контроль Суперадмину."
            
        sys_comment = Comment(text=system_msg, author_id=current_user.id, ticket_id=ticket.id)
        db.session.add(sys_comment)
        db.session.commit()
        
    return redirect(url_for('tickets.detail', id=ticket.id))