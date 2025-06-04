import MySQLdb
import pyotp
# ...existing code...

# Conexión a la base de datos (MODIFICA aquí si tienes otros datos)
conn = MySQLdb.connect(
    host='localhost',
    user='vitalis_user',               # ✅ Tu usuario real de MySQL
    passwd='vitalis123',         # ✅ Tu contraseña real de MySQL
    db='vitalis'
)

cursor = conn.cursor()

# Genera el secreto y lo imprime
secreto = pyotp.random_base32()
print("Secreto generado:", secreto)

# Supón que el admin con id = 1 es el que vamos a actualizar
cursor.execute("UPDATE admins SET secreto_2fa = %s WHERE id = 1", (secreto,))
conn.commit()

cursor.close()
conn.close()
