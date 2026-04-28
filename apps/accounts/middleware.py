from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class CambioPasswordObligatorioMiddleware:
    """Redirige al usuario a cambiar su contraseña si fue marcado por el admin."""

    RUTAS_PERMITIDAS = [
        'accounts:cambiar_mi_password',
        'accounts:logout',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and getattr(request.user, 'debe_cambiar_password', False)
        ):
            try:
                url_cambio = reverse('accounts:cambiar_mi_password')
                url_logout = reverse('accounts:logout')
            except NoReverseMatch:
                return self.get_response(request)

            if request.path not in (url_cambio, url_logout):
                return redirect(url_cambio)

        return self.get_response(request)
