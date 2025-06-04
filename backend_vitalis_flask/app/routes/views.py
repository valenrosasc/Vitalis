from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
import pyotp


views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/about')
def about():
    return render_template('about.html')

@views_bp.route('/guia')
def guia_pacientes():
    return render_template('guia_pacientes.html')

@views_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        documento = request.form['documento']
        nombre = request.form['nombre']
        eps = request.form['eps']
        otra_eps = request.form.get('otra_eps', '')
        email = request.form['email']
        telefono = request.form['telefono']
        password = request.form['password']

        cur = mysql.connection.cursor()
        # Verificar si el correo ya está registrado
        cur.execute("SELECT id FROM pacientes WHERE email = %s", (email,))
        existe = cur.fetchone()
        if existe:
            flash("❌ Este correo ya está registrado. Intenta con otro.")
            return redirect(url_for('views.registro'))
        # Insertar nuevo paciente
        cur.execute(
            """
            INSERT INTO pacientes (documento, nombre, eps, otra_eps, email, telefono, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (documento, nombre, eps, otra_eps, email, telefono, password)
        )
        mysql.connection.commit()
        cur.close()
        flash("✅ ¡Paciente registrado exitosamente!")
        return redirect(url_for('views.login_pacientes'))
    return render_template('auth/registro_pacientes.html')


@views_bp.route('/login/pacientes', methods=['GET', 'POST'])
def login_pacientes():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre FROM pacientes WHERE email = %s AND password = %s", (correo, contraseña))
        paciente = cur.fetchone()
        cur.close()

        if paciente:
            session['paciente_id'] = paciente[0]
            session['paciente_nombre'] = paciente[1]
            flash("✅ ¡Inicio de sesión exitoso!")
            return redirect(url_for('views.dashboard_paciente'))
        else:
            flash("❌ Correo o contraseña incorrectos.")
            return redirect(url_for('views.login_pacientes'))

    return render_template('auth/login_pacientes.html')

@views_bp.route('/login/medicos', methods=['GET', 'POST'])
def login_medicos():
    if request.method == 'POST':
        colegiado = request.form.get('colegiado')
        contraseña = request.form.get('contraseña')

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre FROM medicos WHERE colegiado = %s AND contraseña = %s", (colegiado, contraseña))
        medico = cur.fetchone()
        cur.close()

        if medico:
            session['medico_id'] = medico[0]
            session['medico_nombre'] = medico[1]
            flash("✅ ¡Inicio de sesión exitoso!")
            return redirect(url_for('views.dashboard_medico'))
        else:
            flash("❌ Colegiado o contraseña incorrectos.")
            return redirect(url_for('views.login_medicos'))

    return render_template('auth/login_medicos.html')

@views_bp.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')
        codigo_2fa = request.form.get('codigo2fa')

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, usuario, secreto_2fa FROM admins WHERE usuario = %s AND contraseña = %s", (usuario, contraseña))
        admin = cur.fetchone()
        cur.close()

        if admin:
            totp = pyotp.TOTP(admin[2])
            if totp.verify(codigo_2fa):
                session['admin_id'] = admin[0]
                session['admin_usuario'] = admin[1]
                flash(f'✅ Bienvenido administrador {admin[1]}')
                return redirect(url_for('views.dashboard_admin'))
            else:
                flash('❌ Código 2FA incorrecto', 'danger')
        else:
            flash('❌ Credenciales incorrectas', 'danger')

    return render_template('auth/login_admin.html')

@views_bp.route('/dashboard/paciente')
def dashboard_paciente():
    if 'paciente_id' not in session:
        flash("⚠️ Debes iniciar sesión primero.")
        return redirect(url_for('views.login_pacientes'))
    nombre = session.get('paciente_nombre', 'Paciente')
    return render_template('pacientes/dashboard_paciente.html', nombre=nombre)

@views_bp.route('/dashboard/medico')
def dashboard_medico():
    if 'medico_id' not in session:
        flash("⚠️ Debes iniciar sesión primero.")
        return redirect(url_for('views.login_medicos'))
    return f"<h2>Bienvenido, Dr. {session['medico_nombre']} (ID: {session['medico_id']})</h2>"

@views_bp.route('/dashboard/admin')
def dashboard_admin():
    if 'admin_id' not in session:
        flash("⚠️ Debes iniciar sesión primero.", 'warning')
        return redirect(url_for('views.login_admin'))
    return f"<h2>Bienvenido, Administrador {session['admin_usuario']} (ID: {session['admin_id']})</h2>"

@views_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.')
    return redirect(url_for('views.login_pacientes'))

print("✅ Blueprint de vistas registrado")
