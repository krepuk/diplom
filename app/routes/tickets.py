from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Ticket, Comment # <-- Добавили Comment
from app.forms import TicketForm, CommentForm # <-- Добавили CommentForm

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
            priority=form.priority.data, # <-- ДОБАВИЛИ ЭТУ СТРОЧКУ
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
    if current_user.role == 'superadmin':
        # Суперадмин видит ТОЛЬКО проблемные заявки (переоткрытые 3 и более раз)
        tickets = Ticket.query.filter(Ticket.reopen_count >= 3).order_by(Ticket.created_at.desc()).all()
    elif current_user.role == 'support':
        tickets = Ticket.query.filter(
            (Ticket.category == current_user.department) & 
            ((Ticket.status == 'Новая') | (Ticket.assignee_id == current_user.id))
        ).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(creator_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        
    return render_template('tickets/list.html', tickets=tickets)

@tickets_bp.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def detail(id):
    ticket = Ticket.query.get_or_404(id)
    form = CommentForm()

    # Обработка отправки комментария
    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            author_id=current_user.id,
            ticket_id=ticket.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен.', 'success')
        return redirect(url_for('tickets.detail', id=ticket.id))

    # Получаем все комментарии к этой заявке, отсортированные по дате (старые сверху)
    comments = ticket.comments.order_by(Comment.created_at.asc()).all()

    return render_template('tickets/detail.html', ticket=ticket, form=form, comments=comments)

@tickets_bp.route('/take/<int:id>', methods=['POST'])
@login_required
def take_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # --- НОВАЯ ЛОГИКА ДЛЯ СУПЕРАДМИНА ---
    if current_user.role == 'superadmin':
        if ticket.reopen_count >= 3:
            old_assignee = ticket.assignee.username if ticket.assignee else "Не назначен"
            ticket.assignee_id = current_user.id
            
            # Добавим системный комментарий в чат
            sys_comment = Comment(
                text=f"Суперадмин забрал заявку под свой контроль (предыдущий исполнитель: {old_assignee}).", 
                author_id=current_user.id, 
                ticket_id=ticket.id
            )
            db.session.add(sys_comment)
            db.session.commit()
            
            flash('Вы забрали проблемную заявку под свой контроль.', 'success')
            return redirect(url_for('tickets.detail', id=ticket.id))
        else:
            flash('Вы можете забирать только проблемные заявки (от 3 возвратов).', 'danger')
            return redirect(url_for('tickets.detail', id=ticket.id))
    # ------------------------------------

    # --- СТАРАЯ ЛОГИКА ДЛЯ ОБЫЧНОЙ ПОДДЕРЖКИ ---
    if current_user.role != 'support':
        flash('У вас нет прав для принятия обычных заявок.', 'danger')
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
    
    # Обычная смена статусов
    if new_status in ['Решена', 'Закрыта']:
        ticket.status = new_status
        db.session.commit()
        flash(f'Статус заявки изменен на "{new_status}".', 'success')
        
    # Логика ПЕРЕОТКРЫТИЯ заявки работником
    elif new_status == 'Переоткрыть':
        ticket.status = 'В работе'
        ticket.reopen_count += 1
        
        # Оставляем системный комментарий в чате
        system_msg = f"⚠️ Заявка переоткрыта пользователем. (Попытка {ticket.reopen_count})"
        if ticket.reopen_count >= 3:
            system_msg += " Внимание! Заявка передана на контроль Суперадмину."
            
        sys_comment = Comment(text=system_msg, author_id=current_user.id, ticket_id=ticket.id)
        db.session.add(sys_comment)
        db.session.commit()
        
        flash('Вы вернули заявку в работу.', 'warning')
        
    return redirect(url_for('tickets.detail', id=ticket.id))