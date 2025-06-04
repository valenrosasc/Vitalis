from flask import Flask
from flask_cors import CORS
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

mysql = MySQL()

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../../templates')  # ← carga las vistas HTML desde la carpeta correcta
    CORS(app)

    # Configuración de MySQL
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    app.secret_key = 'clave-secreta-vitalis'  # puedes usar una mejor luego

    mysql.init_app(app)

    # Registrar blueprints correctamente
    from app.routes.incapacidades import incapacidades_bp
    from app.routes.views import views_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(incapacidades_bp, url_prefix="/api/incapacidades")
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    return app
