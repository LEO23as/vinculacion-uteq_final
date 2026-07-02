from django.http import JsonResponse
from django.conf import settings


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Todas las rutas API y admin pasan sin restricción de sesión
        if (request.path.startswith('/static/') or
            request.path.startswith('/media/') or
            request.path.startswith('/admin/') or
            request.path.startswith('/api/')):
            return self.get_response(request)

        return self.get_response(request)
    