from flask import Flask, render_template, request, redirect, session, url_for, flash  # Añadí flash
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required  
from werkzeug.utils import secure_filename
import os
from flask import render_template, request, make_response
from weasyprint import HTML
import datetime

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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Incapacidades
    cursor.execute('''
        SELECT i.*, p.nombre AS colaborador
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        ORDER BY i.id DESC
    ''')
    incapacidades = cursor.fetchall()
    # Incapacidades para jurídico (por ejemplo, solo las aprobadas o en revisión)
    cursor.execute("""
        SELECT i.id, p.nombre AS colaborador, i.motivo
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        WHERE i.estado IN ('aprobada', 'en_revision')
        """)
    incapacidades_para_juridico = cursor.fetchall()
    # Resumen
    resumen = {
        'activas': sum(1 for i in incapacidades if i['estado'] == 'activa'),
        'en_revision': sum(1 for i in incapacidades if i['estado'] == 'en_revision'),
        'por_expirar': sum(1 for i in incapacidades if i['estado'] == 'por_expirar'),
        'aprobadas': sum(1 for i in incapacidades if i['estado'] == 'aprobada')
    }
    # Pagos (si tienes tabla de pagos)
    cursor.execute('''
        SELECT p.*, i.estado AS estado_incapacidad
        FROM pagos p
        JOIN incapacidades i ON p.incapacidad_id = i.id
        WHERE i.estado = 'aprobada'
    ''')
    pagos = cursor.fetchall()
    pagos_conciliados = [p for p in pagos if p['estado_pago'] == 'conciliado']
    pagos_pendientes = [p for p in pagos if p['estado_pago'] != 'conciliado']

    # NUEVO: Incapacidades aprobadas para el select del modal de nuevo pago
    cursor.execute("""
        SELECT i.id, p.nombre AS colaborador, i.motivo
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        WHERE i.estado = 'aprobada'
    """)
    incapacidades_aprobadas = cursor.fetchall()
    
    # Casos jurídicos activos
    cursor.execute("""
        SELECT i.id, p.nombre AS colaborador, i.motivo AS tipo, i.fecha_inicio, i.estado AS estatus
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        WHERE i.estado = 'juridico'
    """)
    casos_juridicos = cursor.fetchall()

    conn.close()
    return render_template(
    'administradores/dashboard_admin.html',
    admin_nombre=admin_nombre,
    resumen=resumen,
    incapacidades=incapacidades,
    pagos_conciliados=pagos_conciliados,
    pagos_pendientes=pagos_pendientes,
    incapacidades_aprobadas=incapacidades_aprobadas,
    incapacidades_para_juridico=incapacidades_para_juridico,
    casos_juridicos=casos_juridicos  # <-- AGREGA ESTA LÍNEA
)
    
@app.route('/actualizar_estado_incapacidad/<int:incapacidad_id>', methods=['POST'])
def actualizar_estado_incapacidad(incapacidad_id):
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))
    nuevo_estado = request.form.get('nuevo_estado')
    comentario = request.form.get('comentario', None)
    if nuevo_estado not in ['activa', 'en_revision', 'por_expirar', 'aprobada', 'rechazada']:
        flash('Estado no válido', 'danger')
        return redirect(url_for('dashboard_admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if nuevo_estado == 'rechazada' and comentario:
        cursor.execute('UPDATE incapacidades SET estado = %s, comentario = %s WHERE id = %s', (nuevo_estado, comentario, incapacidad_id))
    else:
        cursor.execute('UPDATE incapacidades SET estado = %s WHERE id = %s', (nuevo_estado, incapacidad_id))
    conn.commit()
    conn.close()
    flash('Estado actualizado correctamente', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/ver_incapacidad/<int:id>')
def ver_incapacidad(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT i.*, p.nombre AS colaborador
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        WHERE i.id = %s
    ''', (id,))
    incapacidad = cursor.fetchone()
    conn.close()
    return render_template('administradores/ver_incapacidad.html', incapacidad=incapacidad)

@app.route('/editar_incapacidad/<int:id>', methods=['GET', 'POST'])
def editar_incapacidad(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        motivo = request.form['motivo']
        estado = request.form['estado']
        comentario = request.form.get('comentario', '')
        cursor.execute(
            'UPDATE incapacidades SET motivo = %s, estado = %s, comentario = %s WHERE id = %s',
            (motivo, estado, comentario, id)
        )
        conn.commit()
        conn.close()
        flash('Incapacidad actualizada correctamente', 'success')
        return redirect(url_for('dashboard_admin'))
    else:
        cursor.execute('SELECT * FROM incapacidades WHERE id = %s', (id,))
        incapacidad = cursor.fetchone()
        conn.close()
        return render_template('administradores/editar_incapacidad.html', incapacidad=incapacidad)
@app.route('/gestionar_rechazo/<int:id>', methods=['GET', 'POST'])
def gestionar_rechazo(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        comentario = request.form['comentario']
        cursor.execute(
            'UPDATE incapacidades SET estado = %s, comentario = %s WHERE id = %s',
            ('rechazada', comentario, id)
        )
        conn.commit()
        conn.close()
        flash('Incapacidad rechazada correctamente', 'success')
        return redirect(url_for('dashboard_admin'))
    else:
        cursor.execute('SELECT * FROM incapacidades WHERE id = %s', (id,))
        incapacidad = cursor.fetchone()
        conn.close()
        return render_template('administradores/gestionar_rechazo.html', incapacidad=incapacidad)

@app.route('/notificar_juridico', methods=['POST'])
def notificar_juridico():
    incapacidad_id = request.form.get('incapacidad_id')
    comentario = request.form.get('comentario')
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ejemplo: Cambia el estado y guarda el comentario jurídico
    cursor.execute(
        "UPDATE incapacidades SET estado = %s, comentario = %s WHERE id = %s",
        ('juridico', comentario, incapacidad_id)
    )
    conn.commit()
    conn.close()
    flash('Notificación jurídica enviada correctamente', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/conciliar_pago/<int:pago_id>', methods=['POST'])
def conciliar_pago(pago_id):
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pagos SET estado_pago = 'conciliado' WHERE id = %s", (pago_id,))
    conn.commit()
    conn.close()
    flash('Pago conciliado correctamente', 'success')
    return redirect(url_for('dashboard_admin'))
@app.route('/nuevo_pago', methods=['POST'])
def nuevo_pago():
    if 'admin_id' not in session:
        return redirect(url_for('login_admin'))
    incapacidad_id = request.form['incapacidad_id']
    fecha = request.form['fecha']
    monto = request.form['monto']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pagos (incapacidad_id, fecha, monto, estado_pago) VALUES (%s, %s, %s, %s)",
        (incapacidad_id, fecha, monto, 'pendiente')
    )
    conn.commit()
    conn.close()
    flash('Pago registrado correctamente', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/reporte_mensual', methods=['POST'])
def reporte_mensual():
    mes = int(request.form['mes'])
    anio = int(request.form['anio'])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Ejemplo: incapacidades aprobadas en ese mes
    cursor.execute("""
        SELECT i.*, p.nombre AS colaborador
        FROM incapacidades i
        LEFT JOIN pacientes p ON i.empleado_id = p.id
        WHERE MONTH(i.fecha_inicio) = %s AND YEAR(i.fecha_inicio) = %s
    """, (mes, anio))
    incapacidades = cursor.fetchall()

    # Ejemplo: pagos conciliados en ese mes
    cursor.execute("""
        SELECT p.*, i.id AS incapacidad_id, i.motivo, pa.nombre AS colaborador
        FROM pagos p
        JOIN incapacidades i ON p.incapacidad_id = i.id
        LEFT JOIN pacientes pa ON i.empleado_id = pa.id
        WHERE MONTH(p.fecha) = %s AND YEAR(p.fecha) = %s AND p.estado_pago = 'conciliado'
    """, (mes, anio))
    pagos_conciliados = cursor.fetchall()

    conn.close()

    # Renderiza un HTML para el PDF
    rendered = render_template(
        'administradores/reporte_mensual_pdf.html',
        mes=mes,
        anio=anio,
        incapacidades=incapacidades,
        pagos_conciliados=pagos_conciliados
    )
    pdf = HTML(string=rendered).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=reporte_{anio}_{mes}.pdf'
    return response
@app.route('/subir_incapacidad', methods=['POST'])
def subir_incapacidad():
    paciente_id = session.get('usuario_id')
    if not paciente_id:
        return redirect(url_for('login_pacientes'))
    # Aquí deberías procesar el archivo y los datos del formulario
    # Por ejemplo:
    motivo = request.form.get('motivo')
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')
    archivo = request.files.get('archivo')
    filename = None
    if archivo:
        filename = secure_filename(archivo.filename)
        archivo.save(os.path.join('uploads', filename))  # Asegúrate de tener la carpeta 'uploads'
    # Guarda la incapacidad en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO incapacidades (empleado_id, motivo, fecha_inicio, fecha_fin, archivo, estado) VALUES (%s, %s, %s, %s, %s, %s)',
        (paciente_id, motivo, fecha_inicio, fecha_fin, filename, 'en_revision')
    )
    conn.commit()
    conn.close()
    flash('Incapacidad enviada correctamente', 'success')
    return redirect(url_for('dashboard_paciente'))


if __name__ == '__main__':
    app.run(debug=True)
