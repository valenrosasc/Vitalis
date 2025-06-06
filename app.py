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
        user='vitalis_user',
        password='vitalis123',  # O tu contraseña si tienes
        database='vitalis',
        port=3306     # <--- Agrega esta línea
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

@app.route('/administradores', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        token = request.form['token']
        ADMIN_SECRET = 'JBSWY3DPEHPK3PXP'

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admins WHERE usuario = %s', (usuario,))
        admin = cursor.fetchone()

        if admin:
            # Si la contraseña está hasheada
            if admin['contraseña'].startswith('pbkdf2:') or admin['contraseña'].startswith('scrypt:'):
                if check_password_hash(admin['contraseña'], password):
                    if token == ADMIN_SECRET:
                        session['admin_id'] = admin['id']
                        session['admin_nombre'] = admin['usuario']
                        conn.close()
                        return redirect(url_for('dashboard_admin'))
                    else:
                        conn.close()
                        return render_template('auth/login_admin.html', error='Token inválido')
            # Si la contraseña es texto plano y coincide, la migramos a hash
            elif admin['contraseña'] == password:
                new_hash = generate_password_hash(password)
                cursor2 = conn.cursor()
                cursor2.execute('UPDATE admins SET contraseña = %s WHERE id = %s', (new_hash, admin['id']))
                conn.commit()
                session['admin_id'] = admin['id']
                session['admin_nombre'] = admin['usuario']
                conn.close()
                return redirect(url_for('dashboard_admin'))
        conn.close()
        return render_template('auth/login_admin.html', error='Credenciales inválidas')
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
@app.route('/dashboard_admin')
def dashboard_admin():
    admin_id = session.get('admin_id')
    admin_nombre = session.get('admin_nombre')
    if not admin_id:
        return redirect(url_for('login_admin'))
    # Resumen de ejemplo para evitar error en el template
    resumen = {
        'activas': 0,
        'en_revision': 0,
        'por_expirar': 0,
        'aprobadas': 0
    }
    incapacidades = []  # Puedes poblar esto con datos reales después
    return render_template('administradores/dashboard_admin.html', admin_nombre=admin_nombre, resumen=resumen, incapacidades=incapacidades)


if __name__ == '__main__':
    app.run(debug=True)
