import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, login_manager, socketio, csrf

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-chave-altere-antes-de-publicar"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///anuncios.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=30 * 1024 * 1024,
        ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", "admin@seudominio.com").lower(),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "admin123"),
        WHATSAPP_NUMBER=os.getenv("WHATSAPP_NUMBER", "5535999999999"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre na sua conta para continuar."
    socketio.init_app(app, cors_allowed_origins=[])
    csrf.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .routes import main_bp, auth_bp, ads_bp, admin_bp, chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/conta")
    app.register_blueprint(ads_bp, url_prefix="/anuncios")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    with app.app_context():
        db.create_all()
        from .models import Category
        defaults = ["Veículos", "Eletrônicos", "Móveis", "Eletrodomésticos",
                    "Material de construção", "Utensílios", "Decoração", "Outros"]
        for name in defaults:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name))
        db.session.commit()
        _ensure_admin(app)

    from .scheduler import start_scheduler
    start_scheduler(app)
    return app

def _ensure_admin(app):
    from .models import User
    from werkzeug.security import generate_password_hash
    email = app.config["ADMIN_EMAIL"]
    admin = User.query.filter_by(email=email).first()
    if not admin:
        db.session.add(User(
            name="Administrador", phone="", email=email,
            password_hash=generate_password_hash(app.config["ADMIN_PASSWORD"]),
            role="admin", active=True
        ))
        db.session.commit()
