def polla_context(request):
    """Añade afiliado_nav a todos los templates si el usuario está autenticado."""
    if request.user.is_authenticated:
        try:
            return {'afiliado_nav': request.user.afiliado}
        except Exception:
            pass
    return {'afiliado_nav': None}
