# Auditoría Técnica y Hoja de Ruta: Transición de Fondeino hacia un Producto SaaS B2B

**Elaborado por:** Claude Sonnet 4.6 (Anthropic)  
**Fecha:** Mayo 2026  
**Basado en:** Lectura directa del código fuente del repositorio  
**Versión del stack analizado:** Django 4.2 / Python 3.11 / PostgreSQL Neon / Vercel

---

## Resumen Ejecutivo

Fondeino no es un prototipo. Es un sistema en producción, con usuarios reales, datos financieros reales y lógica de negocio validada operativamente. Eso lo distingue de la mayoría de proyectos en esta etapa. La arquitectura actual — Django modular, PostgreSQL gestionado, despliegue serverless — es una base sólida, no un obstáculo.

La brecha entre el estado actual y un producto SaaS B2B comercializable no es conceptual ni matemática: es estructural y organizacional. El motor de scoring existe, funciona y está correctamente parametrizado. Lo que no existe es la capa que permita que ese motor sirva a múltiples fondos de empleados de forma simultánea, segura y rentable.

Este informe identifica exactamente qué está bien, qué falta y en qué orden construirlo.

---

## 1. Estado Real del Sistema — Lo que Existe Hoy

### 1.1 Stack Tecnológico

| Componente | Tecnología | Evaluación |
|---|---|---|
| Backend | Django 4.2 (Python 3.11) | Sólido. LTS con soporte hasta 2026. |
| Base de datos | PostgreSQL en Neon.tech (serverless) | Correcto para el volumen actual. |
| ORM | Django ORM con migraciones | 25 migraciones organizadas. Trazabilidad de esquema. |
| Despliegue | Vercel (@vercel/python) | Funcional. Con limitaciones para escala. |
| Estáticos | WhiteNoise | Adecuado. Sin CDN propia. |
| Frontend | Bootstrap 5.3 + Django templates + Chart.js | Server-rendered. Sin SPA. |
| Autenticación | Django auth + django-axes | Robusto para el uso actual. |
| Excel | pandas + openpyxl | Correcto para la carga de nómina. |

**Veredicto del stack:** No hay deuda tecnológica grave. Django es el framework correcto para este dominio. La decisión de usar PostgreSQL desde el inicio, en lugar de SQLite, es arquitectónicamente correcta y habilita la ruta hacia multi-tenancy.

---

### 1.2 Módulo de Crédito — Motor de Scoring

El archivo `apps/credito/scoring.py` (413 líneas) contiene el activo intelectual central del producto. Fue leído completo. Estas son sus características reales:

**Lo que hace bien:**

- **Implementa la legislación colombiana correctamente.** El límite del 50% de descuento de nómina está codificado explícitamente en `calcular_validacion()`. Si el endeudamiento supera ese umbral, el sistema bloquea automáticamente la aprobación — esto no es trivial y es un diferenciador legal crítico frente a soluciones genéricas.

- **Plan de amortización DAYS360.** La función `generar_plan_pagos()` implementa el estándar europeo de 360 días, idéntico al cálculo del Excel Plantilla_Fondeino_V4. Incluye seguro mensual (0.0857‰), cierre exacto de saldo en última cuota y lógica de primera cuota según día de desembolso. Este nivel de precisión financiera no es común en proyectos de este tamaño.

- **6 factores configurables.** Los umbrales de DataCrédito, antigüedad, vinculación, capacidad de pago, garantías e historial no están hardcodeados en el archivo de scoring: se leen del modelo `Configuracion` en base de datos. Cualquier administrador puede ajustar los parámetros desde el panel sin tocar código.

- **Métricas de riesgo básicas.** La función `calcular_metricas_riesgo()` calcula PD ajustada, LGD y pérdida esperada. Es un cálculo heurístico (no estadístico), pero la estructura existe y es correcta conceptualmente.

- **Eliminación lógica (soft delete).** Las evaluaciones nunca se borran físicamente. El campo `anulado` preserva el historial con trazabilidad de quién anuló y por qué. Esto es un requisito implícito del SARC.

**Lo que puede mejorar:**

- **El modelo de scoring es heurístico (reglas fijas), no estadístico.** Los pesos de cada factor (DataCrédito = 25 pts, antigüedad = 15 pts, etc.) fueron definidos manualmente, no derivados de datos históricos de mora. Esto es absolutamente correcto para un fondo con pocos años de datos, pero en el mediano plazo deberá validarse estadísticamente contra la cartera real.

- **DataCrédito es entrada manual.** El analista escribe el puntaje a mano. En un SaaS B2B, esta integración debe ser automática vía API con Datacrédito Experian o TransUnion.

- **No hay análisis de portafolio.** La plataforma evalúa créditos individuales pero no tiene vista macro: tasa de mora por área, exposición por modalidad, tendencia de la cartera. Esto es lo que necesita un gerente financiero, no solo el analista.

---

### 1.3 Módulo de Autenticación y Seguridad

Configuración relevante encontrada en `settings.py` y `apps/accounts/`:

**Lo que está bien:**
- `SECURE_HSTS_SECONDS = 31536000` activo en Vercel (fuerza HTTPS por 1 año)
- `SESSION_COOKIE_HTTPONLY = True` y `CSRF_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_AGE = 1800` (30 minutos de inactividad)
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`
- django-axes activo: bloqueo tras 5 intentos fallidos, 1 hora de penalización
- Flag `debe_cambiar_password`: obliga al usuario a cambiar su contraseña en el primer acceso

**Lo que falta:**
- No existe autenticación por API (JWT / OAuth2). Todas las rutas son HTML server-rendered. Cuando se exponga una API para integración con otros sistemas core, este será el primer requisito.
- No hay 2FA (autenticación de dos factores). En un sistema financiero con datos de salario y crédito, esto es un riesgo reputacional aunque no sea un requisito legal inmediato.

---

### 1.4 Módulo de Nómina

El módulo lee archivos Excel con pandas y almacena los registros en `Empleado`. Los datos de nómina alimentan el autocompletar del formulario de crédito (cédula → datos del solicitante).

**Limitación crítica:** El módulo de nómina opera como fuente de datos para el scoring, pero no hay validación cruzada automatizada. Si la nómina no está actualizada, un analista puede ingresar un salario incorrecto sin que el sistema lo detecte. Esto introduce riesgo operativo.

---

### 1.5 Módulo Polla

Sistema completo de predicciones deportivas para el Mundial FIFA, con ~1.278 líneas en `views.py`. Integra api-football.com, calcula puntos, genera rankings, maneja doble polla para nuevos asociados y autoriza descuentos por nómina.

Este módulo es funcionalmente irrelevante para el producto SaaS B2B de crédito, pero demuestra capacidad de construcción de productos completos y es un activo de fidelización de usuarios internos.

---

### 1.6 Despliegue e Infraestructura

**Plataforma actual:** Vercel (serverless Python) + Neon.tech (PostgreSQL serverless)

**Lo que funciona:** El modelo serverless es correcto para este volumen. Vercel CDN sirve los estáticos globalmente. Neon.tech maneja el pooling de conexiones automáticamente (crítico para serverless).

**Limitaciones reales para escala SaaS:**

| Limitación | Impacto |
|---|---|
| Vercel Hobby/Pro tiene límite de 10 segundos por función | El scoring actual es rápido, pero un lote de 50 evaluaciones simultáneas podría exceder el límite |
| No hay cola de tareas asíncronas (Celery/Redis) | La generación de PDFs masivos, el sync de la API football y operaciones pesadas bloquean el hilo principal |
| No hay caché en memoria (Redis) | Cada solicitud recalcula datos que podrían almacenarse |
| No hay observabilidad (no Sentry, no logging estructurado) | Un error en producción solo se descubre cuando un usuario reporta |
| Las migraciones corren en `wsgi.py` al arrancar | En producción concurrente esto puede causar race conditions |

---

## 2. Brechas Críticas para el Salto a SaaS B2B

### 2.1 La Brecha más Importante: No Existe Multi-Tenancy

Este es el único punto que hace que el sistema actual sea imposible de comercializar como SaaS sin modificación estructural.

Todo el modelo de datos fue diseñado para un solo fondo (Fondeino). No existe un modelo `Fondo` o `Tenant`. No hay `tenant_id` en ninguna tabla. Si mañana se agrega el Fondo de Empleados Enlazo como cliente, sus evaluaciones, sus empleados, su configuración de scoring y sus usuarios estarían mezclados con los de Fondeino en las mismas tablas, separados únicamente por convención de uso — no por arquitectura.

**La solución recomendada:** Aislamiento por esquema lógico (Bridge Pattern).

PostgreSQL soporta múltiples schemas dentro de una misma base de datos. Cada fondo de empleados obtiene su propio schema (ej: `fondeino`, `enlazo`, `cibest`) con tablas idénticas pero completamente aisladas. Una consulta SQL del schema `enlazo` nunca puede leer datos del schema `fondeino` por diseño, no por filtro.

Django soporta esto mediante la librería `django-tenants`. La migración es compleja pero no requiere reescribir el modelo de negocio: las apps `credito`, `nomina` y `polla` se convierten en apps de tenant, mientras `accounts` y la configuración global permanecen en el schema público.

Esto implica:
- Un modelo `Fondo` (tenant) con subdominio propio (`enlazo.fondeino.com`)
- Resolución dinámica de tenant por subdominio en cada request
- Migraciones separadas para el schema público y los schemas de tenant

---

### 2.2 No Hay API REST

Todas las vistas de Django retornan HTML. No existe ningún endpoint que devuelva JSON para ser consumido por un sistema externo.

Para el SaaS B2B, esto es el segundo requisito después del multi-tenancy. Los fondos de empleados ya tienen sistemas core (ERPs, software de nómina). Si el scoring de Fondeino no puede integrarse vía API, el proceso de adopción requiere que el analista abra un navegador y digite datos manualmente — lo que anula gran parte del valor de la automatización.

El endpoint mínimo viable es:
```
POST /api/v1/credito/evaluar/
Authorization: Bearer <token>
Body: { cedula, salario_bruto, monto, n_cuotas, modalidad, ... }
Response: { score, decision, plan_pagos, metricas }
```

---

### 2.3 Cero Tests en el Módulo Crítico

Los 3 archivos de tests existentes cubren únicamente el módulo de polla. El módulo `credito/scoring.py` — el activo intelectual del producto, el que toma decisiones financieras reales — no tiene ni un solo test automatizado.

Esto significa que cualquier cambio en los parámetros de scoring, cualquier refactorización del algoritmo PMT o cualquier actualización de la lógica de capacidad de pago puede introducir un error silencioso que solo se descubre cuando un analista nota que los números no cuadran.

Para un producto que decide si alguien recibe o no un crédito, esto es inaceptable en producción comercial.

---

### 2.4 Observabilidad Inexistente

No hay Sentry, no hay logging estructurado, no hay métricas de performance. Los logs de Vercel son texto plano capturado de stderr.

Si un cálculo de amortización produce un resultado incorrecto en producción, no hay forma de detectarlo proactivamente. Se descubre cuando un asociado reclama.

---

### 2.5 Integración Manual con DataCrédito

El campo `puntaje_datacredito` es un `IntegerField` que el analista llena a mano. Cada consulta a DataCrédito tiene un costo operativo (tiempo del analista + riesgo de error de transcripción).

En un modelo SaaS donde el scoring debe ser instantáneo y reproducible, esta integración debe ser automática.

---

### 2.6 No Hay Módulo de Facturación ni Control de Acceso por Suscripción

Esto es obvio para un SaaS pero vale mencionarlo: no existe ninguna estructura para gestionar planes, límites de evaluaciones, fechas de vencimiento de contrato o facturación recurrente.

---

## 3. Auditoría de Seguridad

### 3.1 Hallazgos Positivos
- TLS forzado vía HSTS (31536000 segundos, incluye subdominios y preload)
- Cookies con HTTPOnly y Secure activados
- CSRF token activo en todos los formularios (Django por defecto)
- django-axes con bloqueo por fuerza bruta
- La credencial de Neon fue movida a variable de entorno (commit `6f1bbea` del historial)
- Contraseñas nunca se almacenan en texto plano (Django usa PBKDF2 por defecto)

### 3.2 Hallazgos de Riesgo

**Riesgo ALTO:**
- **Historial de git puede contener credenciales.** El commit `6f1bbea` con mensaje "mover credenciales Neon a variable de entorno" indica que en algún punto la credencial estuvo en el código. Si el repositorio fue alguna vez público, o si esa credencial no fue rotada inmediatamente después del commit, existe exposición. **Acción requerida: verificar con `git log -p` si la credencial aparece en algún commit anterior y, si es así, rotar la credencial de Neon y limpiar el historial con `git filter-repo`.**

**Riesgo MEDIO:**
- **No hay Content Security Policy completa.** El header CSP actual en `vercel.json` solo define `frame-src`. Un CSP completo debe cubrir `script-src`, `style-src`, `img-src`, `connect-src` para prevenir XSS y data exfiltration.
- **El endpoint `debug_db` expone información de diagnóstico.** La vista `debug_db()` en `accounts/views.py` retorna información de conexión a la base de datos. Debe estar protegida con `@login_required` y restringida exclusivamente a superusuarios, o eliminada en producción.
- **No hay 2FA.** Un analista con credenciales comprometidas tiene acceso completo a todos los expedientes crediticios.

**Riesgo BAJO:**
- **Sesión de 30 minutos es conservadora** — correcto para un sistema financiero. No se recomienda aumentar.
- **Sin rate limiting en endpoints API internos** (buscar_empleado, get_modalidad_tasa). Si estos se exponen públicamente en el futuro, necesitarán throttling.

---

## 4. Cumplimiento Normativo — SARC y Ley 1581

### 4.1 SARC (Sistema de Administración de Riesgo Crediticio)

El SARC no exige una tecnología específica. Exige que la entidad pueda demostrar que tiene un proceso documentado, reproducible y auditable para la evaluación y seguimiento del riesgo crediticio.

**Lo que Fondeino ya cumple:**
- Cada evaluación queda registrada con todos sus parámetros de entrada y resultados calculados
- La decisión del comité se registra con fecha, usuario y observaciones
- La anulación es lógica (preserva el historial con quién anuló y por qué)
- Los parámetros de la matriz son configurables y auditables

**Lo que falta para un SARC completo:**
- **Reportes automáticos de cartera:** clasificación por categoría de riesgo (A, B, C, D, E), provisiones requeridas, cartera en mora. Actualmente hay que construirlos manualmente desde los datos.
- **Alertas de seguimiento:** no hay notificación automática cuando una evaluación aprobada se acerca al vencimiento o cuando el asociado acumula nuevas obligaciones que cambiarían su score.
- **Seguimiento post-desembolso:** el sistema evalúa antes del crédito pero no tiene módulo de seguimiento durante la vida del crédito.

### 4.2 Ley 1581 de 2012 (Habeas Data)

**Lo que falta:**
- No hay registro explícito de consentimiento de tratamiento de datos personales en el flujo de evaluación. El formulario captura cédula, salario, historial crediticio — todos datos sensibles bajo la ley — sin un mecanismo de consentimiento documentado.
- No hay política de retención y eliminación de datos. Los expedientes se conservan indefinidamente.
- Para el SaaS B2B, cada fondo de empleados cliente será responsable del tratamiento de datos de sus asociados. El contrato de servicio con cada fondo debe incluir un acuerdo de procesamiento de datos que defina responsabilidades bajo la ley.

---

## 5. El Modelo de Negocio SaaS B2B — Análisis de Viabilidad

### 5.1 Por qué este producto tiene ventaja real

La mayoría de los fondos de empleados en Colombia (y hay más de 700 registrados ante la Supersolidaria) no tienen software especializado. Usan Excel, soluciones genéricas de crédito no adaptadas al sector solidario, o sistemas legacy costosos.

La ventaja de Fondeino es que fue construido **desde adentro de un fondo real**. Los parámetros del scoring (la restricción del 50% de nómina, el peso de los aportes como garantía, la lógica del mínimo vital) reflejan la realidad operativa del sector solidario colombiano, no una adaptación genérica.

Eso no se compra. Se construye con años de operación.

### 5.2 El argumento de venta correcto

No es "un software de scoring". Es "el primer sistema de administración de riesgo crediticio diseñado específicamente para el sector solidario colombiano que automatiza el cumplimiento del SARC".

Eso es una posición de mercado, no una característica técnica.

### 5.3 Estructura de precios sugerida

| Tier | Target | Precio mensual estimado | Incluye |
|---|---|---|---|
| **Básico** | Fondos < 500 asociados | $150.000 - $300.000 COP | Scoring ilimitado, PDF, 3 usuarios |
| **Profesional** | Fondos 500-2.000 asociados | $500.000 - $900.000 COP | Todo Básico + API, reportes SARC, integración nómina |
| **Corporativo** | Fondos > 2.000 asociados | $1.500.000+ COP | Todo Profesional + white-label, soporte dedicado, DataCrédito API |

Un fondo mediano que actualmente dedica 2 horas de analista por evaluación (cálculo manual en Excel + revisión + acta) justifica el costo del tier básico con 3-4 evaluaciones al mes.

---

## 6. Hoja de Ruta — 12 Meses

Las fases están ordenadas por impacto en viabilidad comercial, no por complejidad técnica.

---

### Fase 1 — Blindar lo que existe (Meses 1-2)

Objetivo: llevar el producto actual a estándares de producción comercial sin cambiar su funcionalidad.

**Semana 1-2 — Seguridad crítica:**
- [ ] Auditar historial de git con `git log -p | grep -i neon` para confirmar si la credencial fue expuesta. Si sí: rotar credencial y limpiar historial.
- [ ] Restringir o eliminar el endpoint `debug_db` en producción.
- [ ] Agregar CSP completa en `vercel.json`.

**Semana 3-6 — Tests del motor de scoring:**
- [ ] Escribir suite de tests para `apps/credito/scoring.py`. Mínimo 30 casos de prueba que cubran:
  - Casos límite de capacidad de pago (exactamente en el 50%)
  - Scores en cada banda (0, 40, 60, 80, 100)
  - Plan de amortización: verificar que la suma de capital = monto solicitado
  - Validación de restricciones (bloqueado, no bloqueado)
  - Cálculo de mínimo vital con distintos salarios
- [ ] Integrar pytest en el proyecto y correr en cada commit.

**Semana 5-8 — Observabilidad:**
- [ ] Integrar Sentry (plan gratuito suficiente para empezar). Una línea en `settings.py` + un DSN.
- [ ] Configurar logging estructurado en Django para errores de cálculo y fallos de base de datos.
- [ ] Extraer las migraciones de `wsgi.py` y ejecutarlas solo en el build, no en cada request.

**Entregable de Fase 1:** El sistema actual, sin features nuevas, pero con tests del motor de scoring, monitoreo en producción y las brechas de seguridad cerradas. Este es el requisito mínimo para presentarlo a un cliente externo sin riesgo reputacional.

---

### Fase 2 — Multi-tenancy (Meses 3-5)

Objetivo: que el sistema pueda servir a múltiples fondos de empleados con aislamiento completo de datos.

**Diseño de arquitectura:**
- Instalar `django-tenants` (librería madura, 2.500+ estrellas en GitHub).
- Crear modelo `Fondo` (tenant) con: nombre, subdominio, NIT, plan, estado.
- Migrar `credito`, `nomina` como apps de tenant (una por schema).
- `accounts` permanece en schema público (usuarios compartidos con identificación de tenant).
- Subdominio por fondo: `fondeino.fondeino.com`, `enlazo.fondeino.com`, etc.

**Migración de datos:**
- Los datos actuales de Fondeino se migran al schema `fondeino`.
- El schema `public` queda para configuración global.

**Panel de superadmin:**
- Vista para crear/suspender fondos.
- Vista para ver estado de cada tenant (evaluaciones del mes, usuarios activos).

**Entregable de Fase 2:** Es posible crear un segundo fondo de empleados, asignarle un subdominio, y sus datos nunca se mezclan con los de Fondeino. Este es el requisito para tener el primer cliente piloto externo.

---

### Fase 3 — API y Dashboard Analítico (Meses 6-8)

Objetivo: habilitar integraciones externas y dar al gerente financiero las herramientas que necesita.

**API REST:**
- Instalar Django REST Framework.
- Exponer endpoints:
  - `POST /api/v1/credito/evaluar/` — evaluación en tiempo real
  - `GET /api/v1/credito/evaluaciones/` — historial con filtros
  - `GET /api/v1/configuracion/` — parámetros actuales del scoring
- Autenticación: JWT por tenant (cada fondo tiene su API key).
- Documentación automática con drf-spectacular (OpenAPI).

**Dashboard de portafolio (nuevo módulo):**
- Vista gerencial con: cartera total, distribución por clasificación de riesgo (A/B/C/D/E), tasa de aprobación del mes, comparativo meses anteriores, evaluaciones con decisión pendiente.
- Reporte de provisiones para cumplimiento SARC: tabla con evaluaciones por categoría de mora y provisión requerida.
- Export a Excel del reporte regulatorio.

**Entregable de Fase 3:** El producto puede integrarse con el sistema de nómina del fondo vía API, y el gerente tiene visibilidad de la cartera sin necesidad de exportar a Excel manualmente.

---

### Fase 4 — Comercialización y Primer Cliente Externo (Meses 9-12)

Objetivo: firma del primer contrato B2B externo con un fondo diferente a Fondeino.

**Infraestructura de pagos:**
- Integrar Wompi (pasarela colombiana con soporte para pagos recurrentes).
- Lógica de suscripción: fecha inicio, fecha corte, suspensión automática por mora.
- Panel de facturación por tenant.

**Módulo de consentimiento (Ley 1581):**
- En el flujo de creación de usuario de cualquier tenant: pantalla de aceptación de política de tratamiento de datos con timestamp y huella de auditoría.

**Primer piloto:**
- Identificar 2-3 fondos de empleados en Bucaramanga o región, con menos de 1.000 asociados.
- Oferta de piloto gratuito 3 meses a cambio de retroalimentación estructurada.
- El objetivo no es facturar en el piloto: es validar que la arquitectura multitenant funciona en condiciones reales con un cliente externo.

**Materiales de venta:**
- Página de producto en `www.fondeino.com` orientada a fondos de empleados (no al asociado final).
- Caso de estudio con datos de Fondeino: cuántas evaluaciones se han hecho, tiempo promedio por evaluación vs. Excel, errores reducidos.

**Entregable de Fase 4:** Al menos un contrato firmado con un fondo externo y facturación recurrente iniciada.

---

## 7. Lo que No Requiere Cambio Inmediato

Hay recomendaciones de la auditoría de Gemini que son técnicamente correctas pero prematuramente costosas para esta etapa:

| Recomendación de Gemini | Por qué esperar |
|---|---|
| Kubernetes / microservicios | Vercel serverless es suficiente para los primeros 20 clientes. La complejidad operativa de K8s destruiría el tiempo de desarrollo de un equipo de una persona. |
| Apache Kafka / RabbitMQ | Celery + Redis es suficiente para las colas de tareas necesarias en los próximos 2 años. |
| Migración a scikit-learn / XGBoost | El scoring heurístico actual es válido y regulatoriamente más transparente que un modelo de caja negra. La migración a ML requiere al menos 500-1.000 evaluaciones históricas con resultado de mora conocido para tener datos de entrenamiento. Primero hay que acumular esos datos. |
| Análisis de Composición de Software (SCA) automatizado | Correcto hacerlo, pero no en las primeras 8 semanas. GitHub Dependabot (gratuito) resuelve el 90% de esto con una configuración de 5 minutos. |

---

## 8. Tabla de Prioridades

| Prioridad | Tarea | Impacto | Esfuerzo |
|---|---|---|---|
| **CRÍTICO** | Tests para `scoring.py` | Evita errores silenciosos en producción | 2-3 días |
| **CRÍTICO** | Auditar credenciales en historial git | Cierra riesgo de seguridad existente | 1 hora |
| **CRÍTICO** | Arquitectura multitenant con django-tenants | Habilita comercialización | 3-4 semanas |
| **ALTO** | Sentry + logging | Visibilidad en producción | 1 día |
| **ALTO** | Restricción/eliminación de `debug_db` | Cierra brecha de información | 1 hora |
| **ALTO** | API REST con DRF + JWT | Habilita integraciones | 2-3 semanas |
| **ALTO** | Dashboard de portafolio | Valor para el gerente financiero | 2 semanas |
| **MEDIO** | Reporte automático SARC | Argumento de venta diferenciador | 1-2 semanas |
| **MEDIO** | Consentimiento Ley 1581 | Cumplimiento legal | 3-4 días |
| **MEDIO** | Integración DataCrédito API | Elimina error humano | Variable (depende de contrato con Experian) |
| **BAJO** | 2FA | Seguridad adicional | 1-2 días |
| **BAJO** | CSP completa | Seguridad adicional | 2-4 horas |
| **FUTURO** | ML / scikit-learn | Requiere datos históricos de mora | 6-12 meses |
| **FUTURO** | Kubernetes | Requiere >50 clientes activos | 18+ meses |

---

## 9. Conclusión

Fondeino tiene algo que la mayoría de startups FinTech no tienen en esta etapa: un producto real, en producción, validado por un cliente real durante meses. El motor de scoring es correcto, la lógica de negocio está bien implementada y la base tecnológica es sólida.

La transición a SaaS B2B no requiere reescribir nada. Requiere cuatro movimientos secuenciales:

1. Blindar el motor de scoring con tests antes de abrirlo a clientes externos.
2. Agregar multi-tenancy para que múltiples fondos compartan la infraestructura sin mezclar datos.
3. Exponer el scoring vía API para que se integre con los sistemas existentes de los clientes.
4. Agregar el reporte de portafolio que convierte el sistema de "herramienta de evaluación" a "sistema de administración de riesgo crediticio".

El mercado existe. La tecnología existe. Lo que convierte este proyecto en un negocio es la ejecución disciplinada de esos cuatro pasos.

---

*Este informe fue elaborado a partir de la lectura directa del código fuente del repositorio. Todos los hallazgos corresponden a comportamiento observable en los archivos, no a inferencias sobre patrones típicos de proyectos similares.*
