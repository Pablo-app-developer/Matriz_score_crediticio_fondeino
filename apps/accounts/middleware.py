from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class ClearLegacyCsrfDomainCookieMiddleware:
    """Expira la cookie csrftoken con Domain=.fondeino.com de versiones previas.

    Esa cookie convivía con la nueva cookie host-only en www.fondeino.com y
    causaba el error "CSRF token from POST incorrect" en el primer intento del
    usuario: Django leía la cookie equivocada según el orden que enviara el
    browser. Mandando un Set-Cookie con Max-Age=0 forzamos al browser a borrar
    la legacy; los que nunca la tuvieron ignoran el header.

    response.cookies (SimpleCookie) sólo admite un morsel por nombre y el
    middleware de CSRF ya puso ahí la cookie host-only nueva; por eso
    inyectamos el delete como header crudo en response.headers — WSGI emite
    ambos como headers Set-Cookie separados.

    Se puede remover este middleware en unas semanas, cuando todos los browsers
    activos hayan recibido al menos un response y limpiado la cookie vieja.
    """

    LEGACY_DELETE = (
        'csrftoken=; '
        'Domain=.fondeino.com; '
        'Path=/; '
        'Max-Age=0; '
        'Expires=Thu, 01 Jan 1970 00:00:00 GMT'
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'csrftoken' in request.COOKIES and 'Set-Cookie' not in response.headers:
            response.headers['Set-Cookie'] = self.LEGACY_DELETE
        return response


class ModuloAccesoMiddleware:
    """Impide que usuarios ROL_POLLA accedan al módulo de crédito/nómina."""

    RUTAS_SOLO_COMITE = ('/credito/', '/nomina/', '/admin-panel/', '/usuarios/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.es_solo_polla
            and any(request.path.startswith(r) for r in self.RUTAS_SOLO_COMITE)
        ):
            return redirect('polla:index')
        return self.get_response(request)


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
