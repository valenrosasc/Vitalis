# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    # Puedes agregar campos adicionales aquí si los necesitas
    pass
