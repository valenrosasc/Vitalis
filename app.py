from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'  # Cambia esto por una clave más fuerte

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
    return render_template('login.html')

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

if __name__ == '__main__':
    app.run(debug=True)
