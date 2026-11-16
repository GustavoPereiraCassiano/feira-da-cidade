import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import (Blueprint, render_template, redirect, url_for, flash, request,
                   current_app, send_from_directory, abort, session)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from .extensions import db, socketio
from .models import User, Category, Ad, Media, Conversation, Message, Sale
from .utils import save_media, money

main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
ads_bp = Blueprint("ads", __name__)
admin_bp = Blueprint("admin", __name__)
chat_bp = Blueprint("chat", __name__)

@main_bp.app_context_processor
def inject_globals():
    return {"money": money}

@main_bp.route("/")
def home():
    categories = Category.query.order_by(Category.name).all()
    groups = []
    for category in categories:
        items = Ad.query.filter_by(category_id=category.id, status="active").order_by(Ad.created_at.desc()).limit(6).all()
        if items:
            groups.append((category, items, Ad.query.filter_by(category_id=category.id, status="active").count() > 6))
    return render_template("home.html", groups=groups, categories=categories)

@main_bp.route("/buscar")
def search():
    term = request.args.get("q", "").strip()
    category_id = request.args.get("categoria", type=int)
    query = Ad.query.filter_by(status="active")
    if term:
        query = query.filter(or_(Ad.title.ilike(f"%{term}%"), Ad.description.ilike(f"%{term}%")))
    if category_id:
        query = query.filter_by(category_id=category_id)
    results = query.order_by(Ad.created_at.desc()).all()
    return render_template("search.html", ads=results, categories=Category.query.order_by(Category.name).all(), term=term, category_id=category_id)

@main_bp.route("/midia/<path:filename>")
def media_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not phone or not email or len(password) < 8:
            flash("Preencha todos os campos. A senha deve ter pelo menos 8 caracteres.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "danger")
        else:
            user = User(name=name, phone=phone, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("main.home"))
    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard") if user.role == "admin" else url_for("ads.mine"))
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("auth/login.html")

@auth_bp.route("/sair", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))

@auth_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def profile():
    if current_user.role != "seller":
        abort(403)
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash("Este e-mail já está em uso.", "danger")
        else:
            current_user.name = request.form.get("name", "").strip()
            current_user.phone = request.form.get("phone", "").strip()
            current_user.email = email
            new_password = request.form.get("password", "")
            if new_password:
                if len(new_password) < 8:
                    flash("A nova senha deve ter pelo menos 8 caracteres.", "danger")
                    return render_template("auth/profile.html")
                current_user.set_password(new_password)
            db.session.commit()
            flash("Perfil atualizado.", "success")
            return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html")

@ads_bp.route("/novo", methods=["GET", "POST"])
@login_required
def create():
    if current_user.role != "seller":
        abort(403)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = db.session.get(Category, request.form.get("category_id", type=int))
        try:
            price = Decimal(request.form.get("price", "").replace(",", "."))
        except (InvalidOperation, AttributeError):
            price = Decimal("-1")
        photos = request.files.getlist("photos")
        if not title or not description or not category or price < 0 or not any(f.filename for f in photos):
            flash("Título, descrição, preço, categoria e pelo menos uma foto são obrigatórios.", "danger")
            return render_template("ads/form.html", categories=categories)
        ad = Ad(title=title, description=description, price=price, category=category, seller=current_user)
        db.session.add(ad)
        db.session.flush()
        try:
            for file in photos:
                if file.filename:
                    filename, kind = save_media(file)
                    db.session.add(Media(filename=filename, media_type=kind, ad=ad))
            video = request.files.get("video")
            if video and video.filename:
                filename, kind = save_media(video)
                db.session.add(Media(filename=filename, media_type=kind, ad=ad))
            db.session.commit()
            flash("Anúncio publicado!", "success")
            return redirect(url_for("ads.detail", ad_id=ad.id))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            flash("Não foi possível salvar o anúncio.", "danger")
    return render_template("ads/form.html", categories=categories)

@ads_bp.route("/<int:ad_id>")
def detail(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    if ad.status != "active" and (not current_user.is_authenticated or (current_user.id != ad.seller_id and current_user.role != "admin")):
        abort(404)
    return render_template("ads/detail.html", ad=ad)

@main_bp.route("/suporte")
def whatsapp():
    from urllib.parse import quote
    number = current_app.config["WHATSAPP_NUMBER"]
    return redirect(f"https://wa.me/{number}?text={quote('Olá! Preciso de suporte no Sistema de Anúncios da Cidade.')}")

@ads_bp.route("/minhas")
@login_required
def mine():
    if current_user.role != "seller":
        abort(403)
    ads = Ad.query.filter_by(seller_id=current_user.id).order_by(Ad.created_at.desc()).all()
    return render_template("ads/mine.html", ads=ads)

@ads_bp.route("/<int:ad_id>/editar", methods=["GET", "POST"])
@login_required
def edit(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    if ad.seller_id != current_user.id or current_user.role != "seller":
        abort(403)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        ad.title = request.form.get("title", "").strip()
        ad.description = request.form.get("description", "").strip()
        ad.price = Decimal(request.form.get("price", "0").replace(",", "."))
        ad.category_id = request.form.get("category_id", type=int)
        db.session.commit()
        flash("Anúncio atualizado.", "success")
        return redirect(url_for("ads.mine"))
    return render_template("ads/form.html", ad=ad, categories=categories)

@ads_bp.route("/<int:ad_id>/remover", methods=["POST"])
@login_required
def delete(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    if ad.seller_id != current_user.id or current_user.role != "seller":
        abort(403)
    ad.status = "removed"
    db.session.commit()
    flash("Anúncio removido.", "success")
    return redirect(url_for("ads.mine"))

@ads_bp.route("/<int:ad_id>/vendido", methods=["POST"])
@login_required
def sold(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    if ad.seller_id != current_user.id or current_user.role != "seller" or ad.status != "active":
        abort(403)
    buyer = request.form.get("buyer_name", "").strip() or None
    db.session.add(Sale(ad_title=ad.title, category_name=ad.category.name, price=ad.price,
                        seller_name=current_user.name, buyer_name=buyer, ad_id=ad.id, seller_id=current_user.id))
    ad.status = "sold"
    db.session.commit()
    flash("Venda registrada. O anúncio saiu da área pública.", "success")
    return redirect(url_for("ads.mine"))

@chat_bp.route("/iniciar/<int:ad_id>", methods=["GET", "POST"])
def start(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    if ad.status != "active":
        abort(404)
    if request.method == "POST":
        name = request.form.get("buyer_name", "").strip()
        if not name:
            flash("Informe seu nome para iniciar a conversa.", "danger")
        else:
            conversation = Conversation(ad=ad, buyer_name=name)
            db.session.add(conversation)
            db.session.commit()
            session["buyer_conversations"] = list(set(session.get("buyer_conversations", []) + [conversation.id]))
            return redirect(url_for("chat.room", conversation_id=conversation.id))
    return render_template("chat/start.html", ad=ad)

@chat_bp.route("/conversa/<int:conversation_id>")
def room(conversation_id):
    conversation = db.get_or_404(Conversation, conversation_id)
    is_seller = current_user.is_authenticated and current_user.id == conversation.ad.seller_id
    is_buyer = conversation.id in session.get("buyer_conversations", [])
    if not is_seller and not is_buyer:
        abort(403)
    return render_template("chat/room.html", conversation=conversation, buyer_mode=is_buyer)

@chat_bp.route("/vendedor")
@login_required
def seller_inbox():
    if current_user.role != "seller":
        abort(403)
    conversations = (Conversation.query.join(Ad).filter(Ad.seller_id == current_user.id)
                     .order_by(Conversation.created_at.desc()).all())
    return render_template("chat/inbox.html", conversations=conversations)

@socketio.on("join_conversation")
def join_conversation(data):
    from flask_socketio import join_room
    conversation_id = int(data.get("conversation_id", 0))
    conversation = db.session.get(Conversation, conversation_id)
    is_seller = current_user.is_authenticated and conversation and current_user.id == conversation.ad.seller_id
    is_buyer = conversation_id in session.get("buyer_conversations", [])
    if conversation and (is_seller or is_buyer):
        join_room(f"conversation_{conversation_id}")

@socketio.on("send_message")
def send_message(data):
    from flask_socketio import emit
    conversation_id = int(data.get("conversation_id", 0))
    body = str(data.get("body", "")).strip()[:2000]
    sender_type = data.get("sender_type", "buyer")
    conversation = db.session.get(Conversation, conversation_id)
    if not conversation or not body or sender_type not in {"buyer", "seller"}:
        return
    if sender_type == "seller":
        if not current_user.is_authenticated or current_user.id != conversation.ad.seller_id:
            return
    elif conversation_id not in session.get("buyer_conversations", []):
        return
    message = Message(conversation_id=conversation_id, sender_type=sender_type, body=body)
    db.session.add(message)
    db.session.commit()
    emit("new_message", {"body": body, "sender_type": sender_type,
                         "created_at": message.created_at.strftime("%H:%M")}, room=f"conversation_{conversation_id}")

@admin_bp.before_request
def admin_only():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)

@admin_bp.route("/")
def dashboard():
    from sqlalchemy import func
    total_ads = Ad.query.count()
    active_ads = Ad.query.filter_by(status="active").count()
    sales = Sale.query.order_by(Sale.sold_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", total_ads=total_ads, active_ads=active_ads, sales=sales)

@admin_bp.route("/anuncios")
def moderate():
    ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return render_template("admin/ads.html", ads=ads)

@admin_bp.route("/anuncios/<int:ad_id>/remover", methods=["POST"])
def moderate_remove(ad_id):
    ad = db.get_or_404(Ad, ad_id)
    ad.status = "removed"
    db.session.commit()
    flash("Anúncio removido pelo administrador.", "success")
    return redirect(url_for("admin.moderate"))

@admin_bp.route("/relatorio")
def report():
    from .reports import build_monthly_pdf
    path = build_monthly_pdf()
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)

