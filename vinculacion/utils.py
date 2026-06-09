import bcrypt
import random
import string
import unicodedata
from django.core.mail import send_mail
from django.conf import settings


def quitar_tildes(texto):
    """Elimina tildes y caracteres especiales."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def generar_username(nombres, apellidos):
    """
    Genera username: 1ª letra nombre + apellido1 + 1ª letra apellido2
    Ejemplo: Pedro Castro López → pcastrol
    """
    from vinculacion.models import Usuario
    
    nombres_split = nombres.strip().split()
    apellidos_split = apellidos.strip().split()
    
    primera_nombre = quitar_tildes(nombres_split[0][0]).lower()
    apellido1 = quitar_tildes(apellidos_split[0]).lower() if len(apellidos_split) > 0 else ''
    primera_apellido2 = quitar_tildes(apellidos_split[1][0]).lower() if len(apellidos_split) > 1 else ''
    
    username_base = primera_nombre + apellido1 + primera_apellido2
    username = username_base
    
    # Verificar duplicados
    contador = 2
    while Usuario.objects.filter(username=username).exists():
        username = f'{username_base}{contador}'
        contador += 1
    
    return username


def generar_password_temporal():
    """Genera contraseña temporal segura de 10 caracteres."""
    mayusculas = random.choice(string.ascii_uppercase)
    numeros = ''.join(random.choices(string.digits, k=3))
    simbolo = random.choice('@#$%')
    minusculas = ''.join(random.choices(string.ascii_lowercase, k=5))
    
    password = list(mayusculas + numeros + simbolo + minusculas)
    random.shuffle(password)
    return ''.join(password)


def hashear_password(password_plano):
    """Hashea la contraseña con bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_plano.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verificar_password(password_plano, password_hash):
    """Verifica contraseña contra el hash bcrypt."""
    return bcrypt.checkpw(
        password_plano.encode('utf-8'),
        password_hash.encode('utf-8')
    )


def enviar_credenciales(correo, nombres, username, password_temporal):
    """Envía correo con credenciales de acceso al nuevo usuario."""
    asunto = 'Acceso al Sistema de Vinculación UTEQ'
    mensaje = f"""
Estimado/a {nombres},

Se ha creado su cuenta de acceso en el Sistema de Gestión de Vinculación con la Colectividad de la UTEQ.

Sus credenciales de acceso son:

  Usuario: {username}
  Contraseña temporal: {password_temporal}

Por seguridad, al iniciar sesión por primera vez se le solicitará cambiar su contraseña.

Ingrese al sistema en: http://vinculacion.uteq.edu.ec

Si no solicitó este acceso, comuníquese con el Departamento de Vinculación.

Saludos,
Departamento de Vinculación con la Colectividad
Universidad Técnica Estatal de Quevedo
    """
    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [correo],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error enviando correo: {e}')
        return False