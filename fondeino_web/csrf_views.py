from django.http import HttpResponseForbidden


def csrf_failure(request, reason=""):
    cookie_presente = bool(request.COOKIES.get('csrftoken'))
    origin = request.META.get('HTTP_ORIGIN', '—')
    referer = request.META.get('HTTP_REFERER', '—')
    secure = request.is_secure()

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Error CSRF – Fondeino</title>
  <style>
    body {{ font-family: sans-serif; background: #0d1218; color: #dde8f6;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }}
    .card {{ background: #14263a; border: 1px solid #1e3a5f; border-radius: 12px;
             padding: 1.5rem; max-width: 480px; width: 100%; }}
    h2 {{ color: #e05050; margin: 0 0 1rem; font-size: 1.1rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .82rem; }}
    td {{ padding: .35rem .5rem; border-bottom: 1px solid #1e3050; }}
    td:first-child {{ color: #6ba4ff; white-space: nowrap; }}
    .btn {{ display: block; text-align: center; margin-top: 1.2rem;
            background: #1e3a5f; color: #dde8f6; text-decoration: none;
            border-radius: 8px; padding: .65rem; font-size: .9rem; }}
    .reason {{ background: #1a0808; border: 1px solid #5a1010; border-radius: 6px;
               padding: .5rem .75rem; font-size: .8rem; color: #e05050; margin-bottom: 1rem; }}
  </style>
</head>
<body>
<div class="card">
  <h2>⚠️ Error de seguridad (CSRF)</h2>
  <div class="reason">Motivo: <strong>{reason or 'desconocido'}</strong></div>
  <table>
    <tr><td>Cookie CSRF presente</td><td>{'✅ Sí' if cookie_presente else '❌ No'}</td></tr>
    <tr><td>Conexión segura (HTTPS)</td><td>{'✅ Sí' if secure else '❌ No'}</td></tr>
    <tr><td>Origin</td><td>{origin}</td></tr>
    <tr><td>Referer</td><td>{referer}</td></tr>
  </table>
  <a class="btn" href="javascript:history.back()">← Volver e intentar de nuevo</a>
</div>
</body>
</html>"""
    return HttpResponseForbidden(html)
