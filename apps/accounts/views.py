import os
import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control

from .models import Usuario
from .forms import LoginForm, UsuarioCrearForm, UsuarioEditarForm, CambiarPasswordForm


@cache_control(public=True, max_age=300, s_maxage=300)
def landing(request):
    if request.user.is_authenticated:
        return redirect('accounts:panel_selector')
    return render(request, 'accounts/landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:panel_selector')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not user.activo:
            messages.error(request, 'Su cuenta está desactivada.')
        else:
            login(request, user)
            return redirect('accounts:panel_selector')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def panel_selector(request):
    if request.user.es_solo_polla:
        return redirect('polla:index')
    return render(request, 'accounts/panel_selector.html', {
        'muestra_polla': request.user.puede_jugar_polla,
    })


def debug_db(request):
    """Vista temporal para verificar conexión a BD."""
    if request.GET.get('key') != 'fondeino2026':
        from django.http import Http404
        raise Http404
    try:
        count = Usuario.objects.count()
        engine = settings.DATABASES['default']['ENGINE']
        db_name = str(settings.DATABASES['default'].get('NAME', '?'))[:60]
    except Exception as e:
        count = f'ERROR: {e}'
        engine = 'error'
        db_name = 'error'

    # Mostrar variables de entorno clave para diagnóstico
    db_url = os.environ.get('DATABASE_URL', '')
    env_info = {
        'DATABASE_URL': db_url[:40] + '...' if len(db_url) > 40 else (db_url or 'NO DEFINIDA'),
        'SECRET_KEY': 'OK' if os.environ.get('SECRET_KEY') else 'NO DEFINIDA',
        'DEBUG': os.environ.get('DEBUG', 'NO DEFINIDA'),
        'VERCEL': os.environ.get('VERCEL', 'NO (no es Vercel)'),
        'VERCEL_ENV': os.environ.get('VERCEL_ENV', 'NO DEFINIDA'),
    }
    from django.http import HttpResponse
    html = f"""
    <h2>Diagnóstico Vercel</h2>
    <h3>Base de Datos</h3>
    <p><b>Motor:</b> {engine}</p>
    <p><b>Nombre BD:</b> {db_name}</p>
    <p><b>Usuarios:</b> {count}</p>
    <h3>Variables de Entorno</h3>
    {''.join(f'<p><b>{k}:</b> {v}</p>' for k, v in env_info.items())}
    """
    return HttpResponse(html)


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    return redirect('accounts:panel_selector')


@login_required
def usuarios_lista(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'accounts/usuarios_lista.html', {'usuarios': usuarios})


@login_required
def usuario_crear(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    form = UsuarioCrearForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        password_plano = form.cleaned_data.get('password1', '')
        usuario = form.save(commit=False)
        usuario.save()
        # Enviar credenciales por correo si hay email configurado
        if getattr(settings, 'EMAIL_CONFIGURADO', False) and usuario.email:
            try:
                send_mail(
                    subject='Tus credenciales de acceso — FONDEINO',
                    message=(
                        f'Hola {usuario.get_full_name() or usuario.username},\n\n'
                        f'El administrador ha creado tu cuenta en el Sistema de Evaluación Crediticia de FONDEINO.\n\n'
                        f'Tus credenciales de acceso son:\n'
                        f'  Usuario:     {usuario.username}\n'
                        f'  Contraseña:  {password_plano}\n\n'
                        f'Al ingresar por primera vez, el sistema te pedirá que cambies tu contraseña.\n\n'
                        f'Accede en: {request.build_absolute_uri("/")}\n\n'
                        f'— FONDEINO, Sistema de Evaluación Crediticia'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario.email],
                    fail_silently=True,
                )
                messages.success(request, f'Usuario creado. Se enviaron las credenciales a {usuario.email}.')
            except Exception:
                messages.success(request, 'Usuario creado. No se pudo enviar el correo (verifique configuración de email).')
        else:
            msg = 'Usuario creado exitosamente.'
            if not usuario.email:
                msg += ' (sin email registrado, no se envió notificación)'
            elif not getattr(settings, 'EMAIL_CONFIGURADO', False):
                msg += ' (correo no configurado en el sistema)'
            messages.success(request, msg)
        return redirect('accounts:usuarios_lista')
    return render(request, 'accounts/usuario_form.html', {'form': form, 'titulo': 'Crear Usuario'})


@login_required
def usuario_editar(request, pk):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioEditarForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('accounts:usuarios_lista')
    return render(request, 'accounts/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario', 'usuario': usuario})


@login_required
def usuario_cambiar_password(request, pk):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    usuario = get_object_or_404(Usuario, pk=pk)
    form = CambiarPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario.set_password(form.cleaned_data['password1'])
        usuario.save()
        messages.success(request, 'Contraseña actualizada.')
        return redirect('accounts:usuarios_lista')
    return render(request, 'accounts/cambiar_password.html', {'form': form, 'usuario': usuario})


@login_required
def cambiar_mi_password(request):
    """El usuario cambia su propia contraseña (obligatorio en primer ingreso)."""
    obligatorio = getattr(request.user, 'debe_cambiar_password', False)
    form = CambiarPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = request.user
        user.set_password(form.cleaned_data['password1'])
        user.debe_cambiar_password = False
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Contraseña actualizada correctamente.')
        if user.es_solo_polla:
            return redirect('polla:index')
        return redirect('credito:dashboard')
    return render(request, 'accounts/cambiar_mi_password.html', {
        'form': form,
        'obligatorio': obligatorio,
    })


@login_required
@require_POST
def resetear_password_polla(request, pk):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    usuario = get_object_or_404(Usuario, pk=pk, rol=Usuario.ROL_POLLA)
    temp_pwd = secrets.token_urlsafe(6)
    usuario.set_password(temp_pwd)
    usuario.debe_cambiar_password = True
    usuario.save()
    messages.warning(
        request,
        f'Contraseña de «{usuario.get_full_name() or usuario.username}» reseteada. '
        f'Contraseña temporal: {temp_pwd} — Cópiela ahora, no se mostrará de nuevo.'
    )
    return redirect(reverse('accounts:admin_panel') + '?tab=polla')


def manual_usuario(request):
    """Manual de usuario visible para cualquier persona autenticada."""
    return render(request, 'accounts/manual.html')


def protocolo_comite(request):
    """Presentación del protocolo del Comité de Crédito (pública, sin login)."""
    return render(request, 'accounts/protocolo_comite.html')


@login_required
def admin_panel(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    usuarios_credito = Usuario.objects.filter(
        rol__in=[Usuario.ROL_ADMIN, Usuario.ROL_COMITE]
    ).order_by('rol', 'first_name', 'username')
    from django.db.models import Q
    participantes_polla = Usuario.objects.filter(
        Q(rol=Usuario.ROL_POLLA) | Q(participa_polla=True)
    ).order_by('first_name', 'username')
    return render(request, 'accounts/admin_panel.html', {
        'usuarios_credito': usuarios_credito,
        'participantes_polla': participantes_polla,
    })


@login_required
@require_POST
def toggle_permiso(request, pk):
    if not request.user.es_admin:
        return JsonResponse({'ok': False, 'error': 'Sin permiso'}, status=403)
    target = get_object_or_404(Usuario, pk=pk)
    campo = request.POST.get('campo')
    if campo == 'es_admin_polla':
        target.es_admin_polla = not target.es_admin_polla
        target.save(update_fields=['es_admin_polla'])
        return JsonResponse({'ok': True, 'valor': target.es_admin_polla})
    if campo == 'rol_admin':
        if target.rol == Usuario.ROL_ADMIN:
            target.rol = Usuario.ROL_COMITE
        else:
            target.rol = Usuario.ROL_ADMIN
        target.save(update_fields=['rol'])
        return JsonResponse({'ok': True, 'valor': target.rol, 'label': target.get_rol_display()})
    if campo == 'participa_polla':
        target.participa_polla = not target.participa_polla
        target.save(update_fields=['participa_polla'])
        return JsonResponse({'ok': True, 'valor': target.participa_polla})
    if campo == 'activo':
        target.activo = not target.activo
        target.save(update_fields=['activo'])
        return JsonResponse({'ok': True, 'valor': target.activo})
    return JsonResponse({'ok': False, 'error': 'Campo no válido'}, status=400)


@login_required
@require_POST
def usuario_eliminar(request, pk):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    target = get_object_or_404(Usuario, pk=pk)
    if target == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('accounts:admin_panel')
    nombre = target.get_full_name() or target.username
    target.delete()
    messages.success(request, f'Usuario «{nombre}» eliminado correctamente.')
    return redirect('accounts:admin_panel')
