from django.shortcuts import render


def solicitud_credito(request):
    return render(request, 'asociados/solicitud_credito.html')
