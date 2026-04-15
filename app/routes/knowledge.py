from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Article
from app.forms import ArticleForm

knowledge_bp = Blueprint('knowledge', __name__)

# Просмотр всех статей
@knowledge_bp.route('/')
@login_required
def list_articles():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('knowledge/list.html', articles=articles)

# Создание новой статьи (Только для админов)
@knowledge_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role == 'employee':
        flash('Только сотрудники поддержки могут добавлять статьи.', 'danger')
        return redirect(url_for('knowledge.list_articles'))
        
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id
        )
        db.session.add(article)
        db.session.commit()
        flash('Статья успешно добавлена в Базу знаний!', 'success')
        return redirect(url_for('knowledge.list_articles'))
        
    return render_template('knowledge/form.html', form=form)

# Удаление статьи (Только для админов)
@knowledge_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role == 'employee':
        return redirect(url_for('knowledge.list_articles'))
        
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash('Статья удалена.', 'info')
    return redirect(url_for('knowledge.list_articles'))