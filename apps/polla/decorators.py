from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect


def afiliado_activo(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        try:
            afiliado = request.user.afiliado
        except ObjectDoesNotExist:
            messages.info(request, 'Activa primero tu cuenta de la Polla Mundialista.')
            return redirect('polla:index')
        if not afiliado.activo:
            messages.warning(request, 'Tu cuenta de afiliado está desactivada.')
            return redirect('polla:index')
        return func(request, *args, **kwargs)
    return inner


def admin_polla_required(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not (request.user.es_admin or request.user.es_admin_polla):
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('polla:index')
        return func(request, *args, **kwargs)
    return inner
