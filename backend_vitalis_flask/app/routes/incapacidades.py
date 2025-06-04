from flask import Blueprint, request, jsonify
from app import mysql

incapacidades_bp = Blueprint('incapacidades', __name__)

@incapacidades_bp.route('/', methods=['GET'])
def obtener_incapacidades():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM incapacidades")
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@incapacidades_bp.route('/', methods=['POST'])
def crear_incapacidad():
    datos = request.json
    empleado_id = datos['empleado_id']
    fecha_inicio = datos['fecha_inicio']
    fecha_fin = datos['fecha_fin']
    motivo = datos.get('motivo', '')
    archivo_url = datos.get('archivo_url', '')

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO incapacidades (empleado_id, fecha_inicio, fecha_fin, motivo, archivo_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (empleado_id, fecha_inicio, fecha_fin, motivo, archivo_url))
    mysql.connection.commit()
    cur.close()
    return jsonify({"mensaje": "Incapacidad creada exitosamente"}), 201

print("✅ Blueprint de incapacidades registrado")
