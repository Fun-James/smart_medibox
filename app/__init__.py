from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)

    # 延迟导入蓝图
    with app.app_context():
        from .routes import main
        app.register_blueprint(main)

    return app
