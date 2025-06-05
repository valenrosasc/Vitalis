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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pacientes WHERE id = %s', (usuario_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def get_incapacidades(paciente_id):
    """Obtiene incapacidades del paciente"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM incapacidades WHERE empleado_id = %s', (paciente_id,))
    data = cursor.fetchall()
    conn.close()
    return data
# -------------------------------------------

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # O tu contraseña si tienes
        database='vitalis_db',
        port=3307     # <--- Agrega esta línea
    )


@app.route('/')
def index():
    return render_template('home.html')  # sin verificar la sesión

'''@app.route('/login', methods=['GET', 'POST'])
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
    return render_template('home.html')'''

# @app.route('/registro', methods=['GET', 'POST'])
# def registro():
#     if request.method == 'POST':
#         nombre = request.form['nombre']
#         email = request.form['email']
#         contraseña = generate_password_hash(request.form['contraseña'])
#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor()
#             cursor.execute(
#                 'INSERT INTO usuarios (nombre, email, contraseña) VALUES (%s, %s, %s)',
#                 (nombre, email, contraseña)
#             )
#             conn.commit()
#             conn.close()
#             return redirect(url_for('login'))
#         except Error as e:
#             return f'Error: {str(e)}'
#     return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_pacientes'))

@app.route('/about')
def about():
    return render_template('about.html') 
@app.route('/guia-pacientes')
def guia_pacientes():
    return render_template('guia_pacientes.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/pacientes', methods=['GET', 'POST'])
def login_pacientes():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM pacientes WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user:
            # Si la contraseña está hasheada, usa check_password_hash
            if user['password'].startswith('pbkdf2:') or user['password'].startswith('scrypt:'):
                if check_password_hash(user['password'], password):
                    session['usuario_id'] = user['id']
                    session['nombre'] = user['nombre']
                    conn.close()
                    return redirect(url_for('dashboard_paciente'))
            # Si la contraseña es texto plano y coincide, la migramos a hash
            elif user['password'] == password:
                new_hash = generate_password_hash(password)
                cursor2 = conn.cursor()
                cursor2.execute('UPDATE pacientes SET password = %s WHERE id = %s', (new_hash, user['id']))
                conn.commit()
                session['usuario_id'] = user['id']
                session['nombre'] = user['nombre']
                conn.close()
                return redirect(url_for('dashboard_paciente'))
        conn.close()
        error = 'Credenciales inválidas'
    return render_template('auth/login_pacientes.html', error=error)
@app.route('/medicos')
def login_medicos():
    return render_template('auth/login_medicos.html')

@app.route('/administradores')
def login_admin():
    return render_template('auth/login_admin.html')

@app.route('/registro_pacientes', methods=['GET', 'POST'])
def registro_pacientes():
    if request.method == 'POST':
        documento = request.form['documento']
        nombre = request.form['nombre']
        eps = request.form['eps']
        otra_eps = request.form.get('otra_eps', '')
        email = request.form['email']
        telefono = request.form['telefono']
        password = generate_password_hash(request.form['password'])

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO pacientes (nombre, email, password, documento, eps, otra_eps, telefono) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (nombre, email, password, documento, eps, otra_eps, telefono)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login_pacientes'))
        except Exception as e:
            return f'Error al registrar: {str(e)}'
    return render_template('auth/registro_pacientes.html')
@app.route('/dashboard_paciente')
def dashboard_paciente():
    paciente_id = session.get('usuario_id')
    if not paciente_id:
        return redirect(url_for('login_pacientes'))
    paciente_data = get_paciente_data(paciente_id)
    incapacidades = get_incapacidades(paciente_id)
    return render_template('pacientes/dashboard_paciente.html', 
                      nombre=paciente_data['nombre'],
                      incapacidades=incapacidades)


if __name__ == '__main__':
    app.run(debug=True)
