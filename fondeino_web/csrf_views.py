from django.conf import settings
from django.http import HttpResponseForbidden


def csrf_failure(request, reason=""):
    cookie_presente = bool(request.COOKIES.get(settings.CSRF_COOKIE_NAME))
    cookie_legacy   = bool(request.COOKIES.get('csrftoken'))
    origin  = request.META.get('HTTP_ORIGIN',  '—')
    referer = request.META.get('HTTP_REFERER', '—')
    secure  = request.is_secure()

    ok = '✅ Sí'
    no = '❌ No'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Refrescando tu sesión – Fondeino</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: linear-gradient(135deg, #0d1218 0%, #14263a 100%);
           color: #dde8f6; display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }}
    .card {{ background: #14263a; border: 1px solid #1e3a5f; border-radius: 16px;
            padding: 2rem 1.5rem 1.5rem; max-width: 420px; width: 100%; text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,.4); }}
    .icon {{ font-size: 3rem; margin-bottom: .6rem; line-height: 1; }}
    h2 {{ margin: 0 0 .7rem; font-size: 1.25rem; font-weight: 700; color: #f0c040; }}
    p  {{ color: #b0cce8; font-size: .95rem; line-height: 1.5; margin: 0 0 1.5rem; }}
    .btn-primary {{
      display: block; background: #f0c040; color: #0d1218; text-decoration: none;
      border-radius: 10px; padding: .85rem; font-size: 1rem; font-weight: 700;
      box-shadow: 0 4px 16px rgba(240,192,64,.3);
      transition: transform .15s, box-shadow .15s; cursor: pointer; border: none; width: 100%;
    }}
    .btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(240,192,64,.45); }}
    .toggle {{
      margin-top: 1.4rem; font-size: .72rem; color: #6ba4ff;
      cursor: pointer; opacity: .45; display: inline-block;
      padding: .35rem .6rem; border-radius: 6px; background: none; border: none;
    }}
    .toggle:hover {{ opacity: .85; }}
    #det {{ display: none; margin-top: .8rem; text-align: left;
            background: #0d1218; border: 1px solid #1e3050; border-radius: 8px;
            padding: .7rem .85rem; font-size: .72rem; }}
    #det table {{ width: 100%; border-collapse: collapse; }}
    #det td {{ padding: .25rem .4rem; border-bottom: 1px solid #1a2840; }}
    #det td:first-child {{ color: #6ba4ff; white-space: nowrap; }}
    #det td:last-child {{ color: #dde8f6; word-break: break-all; font-size: .68rem; }}
  </style>
</head>
<body>
<div class="card">
  <div class="icon">🔄</div>
  <h2>Refrescando tu sesión</h2>
  <p>
    Actualizamos tu acceso por seguridad. Toca el botón y sigues jugando — esto
    solo pasa una vez y no se vuelve a repetir.
  </p>
  <button class="btn-primary" onclick="continuar()">Continuar →</button>
  <button class="toggle" onclick="
    var d=document.getElementById('det');
    d.style.display=d.style.display==='block'?'none':'block';
    this.innerText=d.style.display==='block'?'Ocultar detalles':'Ver detalles técnicos';
  ">Ver detalles técnicos</button>
  <div id="det">
    <table>
      <tr><td>Razón</td><td>{reason or 'desconocido'}</td></tr>
      <tr><td>Cookie CSRF ({settings.CSRF_COOKIE_NAME})</td><td>{ok if cookie_presente else no}</td></tr>
      <tr><td>Cookie legacy (csrftoken)</td><td>{'⚠️ Sí' if cookie_legacy else '— No'}</td></tr>
      <tr><td>HTTPS</td><td>{ok if secure else no}</td></tr>
      <tr><td>Origin</td><td>{origin}</td></tr>
      <tr><td>Referer</td><td>{referer}</td></tr>
    </table>
  </div>
</div>
<script>
function continuar() {{
  var expira = '; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  document.cookie = 'csrftoken=' + expira;
  document.cookie = 'csrftoken=' + expira + '; domain=.fondeino.com';
  document.cookie = 'csrftoken=' + expira + '; domain=fondeino.com';
  window.location.href = document.referrer || '/polla/';
}}
</script>
</body>
</html>"""
    return HttpResponseForbidden(html)
