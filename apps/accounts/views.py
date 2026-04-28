from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Usuario
from .forms import LoginForm, UsuarioCrearForm, UsuarioEditarForm, CambiarPasswordForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('credito:evaluacion')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not user.activo:
            messages.error(request, 'Su cuenta está desactivada.')
        else:
            login(request, user)
            return redirect('credito:evaluacion')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    return redirect('credito:evaluacion')


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
        form.save()
        messages.success(request, 'Usuario creado exitosamente.')
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
