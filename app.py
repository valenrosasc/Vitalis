from flask import Flask, render_template, request, redirect, session, url_for, flash  # Añadí flash
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required  

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# --- Añadí estas funciones para pacientes ---
def get_paciente_data(usuario_id):
    """Obtiene datos específicos del paciente desde la BD"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pacientes WHERE usuario_id = %s', (usuario_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def get_incapacidades(paciente_id):
    """Obtiene incapacidades del paciente"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM incapacidades WHERE paciente_id = %s', (paciente_id,))
    data = cursor.fetchall()
    conn.close()
    return data
# -------------------------------------------

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='vitalis_db'
    )


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Por defecto, sin contraseña en XAMPP
        database='vitalis_db'
    )

@app.route('/')
def index():
    return render_template('home.html')  # sin verificar la sesión

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['contraseña'], contraseña):
            session['usuario_id'] = user['id']
            session['nombre'] = user['nombre']
            return redirect(url_for('index'))
        return 'Credenciales inválidas'
    return render_template('home.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = generate_password_hash(request.form['contraseña'])
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO usuarios (nombre, email, contraseña) VALUES (%s, %s, %s)',
                (nombre, email, contraseña)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Error as e:
            return f'Error: {str(e)}'
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html') 
@app.route('/guia-pacientes')
def guia_pacientes():
    return render_template('guia_pacientes.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/pacientes')  
def login_pacientes():
    return render_template('auth/login_pacientes.html')

@app.route('/medicos')
def login_medicos():
    return render_template('auth/login_medicos.html')

@app.route('/administradores')
def login_admin():
    return render_template('auth/login_admin.html')
@app.route('/registro_pacientes', methods=['GET', 'POST'])
def registro_pacientes():
    if request.method == 'POST':
        # Lógica para procesar el registro (base de datos, etc.)
        return redirect(url_for('login_pacientes'))  # Redirige tras registro
    return render_template('auth/registro_pacientes.html')  # Renderiza el formulario
@app.route('/dashboard_paciente')
@login_required
def dashboard_paciente():
    # Obtener datos del paciente desde la BD
    paciente_data = get_paciente_data(current_user.id)
    incapacidades = get_incapacidades(paciente_data['id'])
    return render_template('dashboard_paciente.html', 
                         nombre=paciente_data['nombre'],
                         incapacidades=incapacidades)


if __name__ == '__main__':
    app.run(debug=True)
