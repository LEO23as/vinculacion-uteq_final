from django.shortcuts import redirect
from django.conf import settings


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rutas_publicas = getattr(settings, 'RUTAS_PUBLICAS', ['/login/', '/'])
        
        # Permitir recursos estáticos y admin sin verificar sesión
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/admin/')):
            return self.get_response(request)

        # Verificar si la ruta requiere autenticación
        if request.path not in rutas_publicas:
            if not request.session.get('usuario_id'):
                return redirect('login')

        return self.get_response(request)
    