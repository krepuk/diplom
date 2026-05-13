from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Article
from app.forms import ArticleForm

knowledge_bp = Blueprint('knowledge', __name__)

# Маршрут для просмотра всех статей (доступен всем авторизованным)
@knowledge_bp.route('/')
@login_required
def list_articles():
    # Сортировка от новых к старым
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('knowledge/list.html', articles=articles)

# Маршрут для создания новой статьи
@knowledge_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Проверка роли
    if current_user.role == 'employee':
        flash('Только сотрудники поддержки могут добавлять статьи.', 'danger')
        return redirect(url_for('knowledge.list_articles'))
        
    form = ArticleForm()
    # Валидация формы при POST-запросе
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id  # Привязка статьи к текущему автору
        )
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('knowledge.list_articles'))
        
    return render_template('knowledge/form.html', form=form)

# Маршрут для удаления статьи 
@knowledge_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role == 'employee':
        return redirect(url_for('knowledge.list_articles'))
    
    # Автоматически возвращает 404, если статья не найдена
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('knowledge.list_articles'))
