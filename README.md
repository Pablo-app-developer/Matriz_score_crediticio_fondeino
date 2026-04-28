# FONDEINO — Sistema de Evaluación Crediticia

Aplicación web que digitaliza y automatiza la **Matriz de Riesgo Crediticio** del Fondo de Empleados FONDEINO, reemplazando el archivo Excel `Plantilla_Fondeino_V4.xlsm` con una plataforma multiusuario, con historial, exportación PDF y carga de nómina.

---

## Características principales

- **Evaluación de crédito automatizada** — scoring de 6 factores, 100 puntos, decisión automática (APROBAR / REVISAR / RECHAZAR)
- **Plan de pagos** — tabla de amortización con método DAYS360, igual al Excel original
- **Panel de control** — KPIs del mes: total, aprobadas, rechazadas, en revisión, score promedio, montos
- **Historial** — búsqueda por nombre, cédula, decisión y fecha
- **Búsqueda de empleado** — autocompletado AJAX desde la base de nómina cargada
- **Exportación PDF** — página optimizada para A4 con plan de pagos completo
- **Carga de nómina** — upload de Excel (`.xlsx`) procesado en memoria
- **Gestión de usuarios** — roles Admin y Comité, activación/desactivación
- **Configuración del scoring** — todos los umbrales y pesos ajustables por el administrador
- **Modalidades de crédito** — tasas configurables por tipo de crédito

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

---

## Estructura del proyecto

```
fondeino/
├── apps/
│   ├── accounts/          # Usuarios y autenticación
│   ├── credito/           # Evaluaciones, scoring, dashboard, PDF
│   │   ├── scoring.py     # Motor de scoring (replica exacta del Excel)
│   │   ├── models.py      # EvaluacionCredito, Modalidad, Configuracion
│   │   ├── views.py       # Vistas y APIs AJAX
│   │   └── templatetags/  # Filtros: cop (formato COP), sum_field
│   └── nomina/            # Carga y consulta de nómina
├── templates/             # Plantillas HTML por app
├── static/css/main.css    # Estilos globales
├── fondeino_web/
│   └── settings.py        # Configuración Django + Neon + Vercel
├── vercel.json            # Configuración despliegue Vercel
├── build_files.sh         # Script de build para Vercel
└── requirements.txt
```

---

## Factores del scoring (100 puntos)

| Factor | Peso máximo |
|---|---|
| Puntaje DataCrédito (150–950) | 25 pts |
| Antigüedad en la empresa | 15 pts |
| Tipo de vinculación laboral | 10 pts |
| Capacidad de pago (% endeudamiento) | 25 pts |
| Garantías acumuladas (aportes + ahorros) | 15 pts |
| Historial crédito activo FONDEINO | 10 pts |

### Clasificaciones y decisiones

| Score | Clasificación | Decisión |
|---|---|---|
| 80 – 100 | EXCELENTE | APROBAR |
| 60 – 79 | BUENO | APROBAR |
| 40 – 59 | REGULAR | REVISAR / CODEUDOR |
| 0 – 39 | ALTO RIESGO | RECHAZAR |

> Si la cuota supera el mínimo vital (50% del salario neto), se rechaza automáticamente independiente del score.

---

## Instalación local

### Requisitos
- Python 3.11+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino.git
cd Matriz_score_crediticio_fondeino/fondeino

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Crear archivo .env en la raíz con:
SECRET_KEY=tu-clave-secreta
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3   # o URL de PostgreSQL

# 5. Migraciones
python manage.py migrate

# 6. Datos iniciales (modalidades, configuración, usuario admin)
python manage.py seed_data

# 7. Ejecutar servidor
python manage.py runserver
```

Acceder a `http://127.0.0.1:8000` con usuario `admin` / contraseña `Admin1234`.

---

## Despliegue en Vercel

1. Hacer fork del repositorio en GitHub
2. Importar el proyecto en [vercel.com](https://vercel.com)
3. Configurar variables de entorno en el dashboard de Vercel:
   - `SECRET_KEY` — clave secreta Django
   - `DATABASE_URL` — URL de conexión PostgreSQL (Neon.tech)
   - `DEBUG` — `False`
4. El archivo `vercel.json` y `build_files.sh` manejan el resto automáticamente

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `SECRET_KEY` | Clave secreta Django | Sí |
| `DATABASE_URL` | URL PostgreSQL completa | Sí (producción) |
| `DEBUG` | `True` / `False` | No (default False en Vercel) |
| `ALLOWED_HOSTS` | Hosts permitidos separados por coma | No |

---

## Comandos útiles

```bash
# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales
python manage.py seed_data

# Recolectar archivos estáticos
python manage.py collectstatic

# Acceder al shell de Django
python manage.py shell
```

---

## Repositorio

[github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino](https://github.com/Pablo-app-developer/Matriz_score_crediticio_fondeino)
