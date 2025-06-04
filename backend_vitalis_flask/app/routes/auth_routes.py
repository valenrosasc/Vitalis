from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import mysql  # Asegúrate de que app/__init__.py exporte mysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login/pacientes', methods=['GET', 'POST'])
def login_pacientes():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pacientes WHERE correo = %s", (correo,))
        paciente = cur.fetchone()
        cur.close()

        if paciente:
            if paciente[3] == contraseña:  # columna 3 = contraseña
                flash('Inicio de sesión exitoso ✅', 'success')
                return redirect(url_for('views.home'))
            else:
                flash('Contraseña incorrecta ❌', 'danger')
        else:
            flash('Correo no registrado ❌', 'danger')

    return render_template('auth/login_pacientes.html')
