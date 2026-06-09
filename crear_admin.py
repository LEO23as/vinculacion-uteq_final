import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import bcrypt
from django.utils import timezone
from vinculacion.models import Usuario, Rol

# ── CONFIGURA AQUÍ ──────────────────────────
NOMBRES       = "Administrador"
USERNAME      = "admin1"
PASSWORD      = "Admin2025@"   # Esta es tu clave, guárdala
ROL_NOMBRE    = "ADMIN"
# ─────────────────────────────────────────────

def hashear(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    rol = Rol.objects.get(nombre=ROL_NOMBRE)
except Rol.DoesNotExist:
    print(f"ERROR: No existe el rol '{ROL_NOMBRE}' en la BD.")
    print("Roles disponibles:", list(Rol.objects.values_list('nombre', flat=True)))
    sys.exit(1)

if Usuario.objects.filter(username=USERNAME).exists():
    print(f"El usuario '{USERNAME}' ya existe.")
    sys.exit(0)

usuario = Usuario(
    username=USERNAME,
    password=hashear(PASSWORD),
    id_rol=rol,
    nombres=NOMBRES,
    activo=True,
    debe_cambiar_clave=False,
    creado_en=timezone.now(),
)
usuario.save()

print("=" * 40)
print("Usuario administrador creado:")
print(f"  Usuario  : {USERNAME}")
print(f"  Contraseña: {PASSWORD}")
print(f"  Rol      : {ROL_NOMBRE}")
print("=" * 40)
print("GUARDA ESTA CONTRASEÑA EN UN LUGAR SEGURO.")