# FONDEINO — Plataforma Web

Plataforma web del **Fondo de Empleados FONDEINO** que integra evaluación crediticia, gestión de nómina, landing pública y sistema de polla deportiva para afiliados.

---

## Módulos

### Crédito
- Scoring automatizado de 6 factores (100 pts) — decisión APROBAR / REVISAR / RECHAZAR
- Plan de pagos con amortización método DAYS360
- Panel de control con KPIs del mes
- Historial con búsqueda por nombre, cédula, decisión y fecha
- Exportación PDF optimizada para A4
- Modalidades de crédito con tasas configurables
- Configuración de umbrales y pesos desde el panel admin

### Nómina
- Carga de nómina desde Excel (`.xlsx`)
- Autocompletado AJAX de empleados en el formulario de crédito

### Cuentas y autenticación
- Roles: Admin y Comité
- Bloqueo por fuerza bruta (django-axes, 5 intentos)
- Cambio de contraseña obligatorio al primer ingreso
- Recuperación de contraseña por correo
- Cierre de sesión automático por inactividad (30 min)

### Landing pública
- Página principal de fondeino.com con información del fondo

### Polla deportiva
- Sistema de predicciones de partidos para afiliados
- Ranking público
- Autorización de descuento por nómina

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django 4.2 (Python 3.11) |
| Base de datos | PostgreSQL (Neon.tech serverless) |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Archivos estáticos | WhiteNoise |
| Deploy | Vercel (serverless Python) |
| Excel / Nómina | pandas + openpyxl |
| Seguridad | django-axes |

---

## Estructura del proyecto

```
├── apps/
│   ├── accounts/          # Usuarios, autenticación, landing, middleware
│   ├── credito/           # Evaluaciones, scoring, dashboard, PDF
│   │   ├── scoring.py     # Motor de scoring
│   │   ├── models.py      # EvaluacionCredito, Modalidad, Configuracion
│   │   └── templatetags/  # Filtros: cop (formato COP), sum_field
│   ├── nomina/            # Carga y consulta de nómina
│   └── polla/             # Sistema de polla deportiva
├── templates/             # Plantillas HTML por app
├── static/css/main.css    # Estilos globales
├── fondeino_web/
│   └── settings.py        # Configuración Django + Neon + Vercel
├── vercel.json            # Configuración despliegue Vercel
├── build_files.sh         # Script de build para Vercel
└── requirements.txt
```

---

## Factores del scoring crediticio (100 puntos)

| Factor | Peso máximo |
|---|---|
| Puntaje DataCrédito (150–950) | 25 pts |
| Antigüedad en la empresa | 15 pts |
| Tipo de vinculación laboral | 10 pts |
| Capacidad de pago (% endeudamiento) | 25 pts |
| Garantías acumuladas (aportes + ahorros) | 15 pts |
| Historial crédito activo FONDEINO | 10 pts |

| Score | Clasificación | Decisión |
|---|---|---|
| 80 – 100 | EXCELENTE | APROBAR |
| 60 – 79 | BUENO | APROBAR |
| 40 – 59 | REGULAR | REVISAR / CODEUDOR |
| 0 – 39 | ALTO RIESGO | RECHAZAR |

> Si la cuota supera el 50% del salario neto se rechaza automáticamente, sin importar el score.

---

## Instalación local

### Requisitos
- Python 3.11+

```bash
# 1. Clonar el repositorio
git clone https://github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino.git
cd Matriz_score_crediticio_fondeino

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Copiar .env.example como .env y completar los valores
cp .env.example .env

# 5. Migraciones
python manage.py migrate

# 6. Datos iniciales (modalidades, configuración, usuario admin)
python manage.py seed_data

# 7. Ejecutar servidor
python manage.py runserver
```

Acceder a `http://127.0.0.1:8000`.

---

## Despliegue en Vercel

1. Importar el repositorio en [vercel.com](https://vercel.com)
2. Configurar las variables de entorno en el dashboard de Vercel (ver tabla abajo)
3. El archivo `vercel.json` y `build_files.sh` manejan el build automáticamente

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `SECRET_KEY` | Clave secreta Django | Sí |
| `DATABASE_URL` | URL de conexión PostgreSQL (Neon.tech) | Sí |
| `DEBUG` | `True` / `False` | No (default `False` en Vercel) |
| `ALLOWED_HOSTS` | Hosts permitidos separados por coma | No |
| `EMAIL_HOST_USER` | Correo Gmail para envío de notificaciones | No |
| `EMAIL_HOST_PASSWORD` | Contraseña de aplicación Gmail | No |
| `API_FOOTBALL_KEY` | API key de api-football.com (polla) | No |

Las credenciales **nunca deben hardcodearse** en `settings.py`. Usar siempre `.env` en local y variables de entorno en Vercel.

---

## Comandos útiles

```bash
# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales
python manage.py seed_data

# Recolectar archivos estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell
```

---

## Repositorio

[github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino](https://github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino)
