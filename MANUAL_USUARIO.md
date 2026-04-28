# Manual de Usuario — FONDEINO
## Sistema de Evaluación Crediticia

**Versión:** 1.0  
**Fecha:** Abril 2026  
**Dirigido a:** Asesores de crédito, comité crediticio y administradores del sistema

---

## Tabla de Contenidos

1. [Acceso al sistema](#1-acceso-al-sistema)
2. [Panel de control (Dashboard)](#2-panel-de-control-dashboard)
3. [Nueva evaluación de crédito](#3-nueva-evaluación-de-crédito)
4. [Búsqueda de empleado por nombre](#4-búsqueda-de-empleado-por-nombre)
5. [Entendiendo el resultado de la evaluación](#5-entendiendo-el-resultado-de-la-evaluación)
6. [Plan de pagos](#6-plan-de-pagos)
7. [Exportar evaluación a PDF](#7-exportar-evaluación-a-pdf)
8. [Historial de evaluaciones](#8-historial-de-evaluaciones)
9. [Editar y eliminar evaluaciones](#9-editar-y-eliminar-evaluaciones)
10. [Decisión del comité](#10-decisión-del-comité)
11. [Carga de nómina](#11-carga-de-nómina)
12. [Gestión de usuarios](#12-gestión-de-usuarios)
13. [Configuración del scoring](#13-configuración-del-scoring)
14. [Gestión de modalidades](#14-gestión-de-modalidades)
15. [Cómo se calcula el score](#15-cómo-se-calcula-el-score)
16. [Preguntas frecuentes](#16-preguntas-frecuentes)

---

## 1. Acceso al sistema

### 1.1 Ingresar al sistema

1. Abra su navegador web (Chrome, Edge o Firefox recomendados)
2. Ingrese la dirección del sistema proporcionada por su administrador
3. Aparecerá la pantalla de inicio de sesión
4. Digite su **nombre de usuario** y **contraseña**
5. Haga clic en el botón **Ingresar**

> **Nota:** Si olvidó su contraseña, comuníquese con el administrador del sistema para que la restablezca.

### 1.2 Roles de usuario

El sistema tiene dos tipos de usuarios:

| Rol | Permisos |
|---|---|
| **Administrador** | Acceso total: crear evaluaciones, ver historial, gestionar usuarios, cargar nómina, configurar scoring, registrar decisión del comité, editar/eliminar cualquier evaluación |
| **Comité** | Crear evaluaciones, ver historial de sus propias evaluaciones, editar/eliminar sus propias evaluaciones |

### 1.3 Cerrar sesión

Haga clic en su nombre de usuario en la esquina superior derecha del menú y seleccione **Cerrar sesión**.

---

## 2. Panel de control (Dashboard)

El panel de control es la página de inicio del sistema. Muestra un resumen estadístico del mes en curso y las últimas evaluaciones.

### 2.1 Indicadores del mes (KPIs)

En la parte superior encontrará cinco tarjetas con los indicadores del mes actual:

| Tarjeta | Descripción |
|---|---|
| **Total evaluaciones** (azul) | Número de evaluaciones realizadas en el mes en curso |
| **Aprobadas** (verde) | Cuántas evaluaciones resultaron en APROBAR, con el porcentaje del total |
| **Rechazadas** (rojo) | Cuántas evaluaciones resultaron en RECHAZAR, con el porcentaje del total |
| **En revisión** (celeste) | Cuántas evaluaciones requieren revisión o codeudor, con porcentaje |
| **Score promedio** (amarillo) | Promedio del puntaje crediticio de todas las evaluaciones del mes |

### 2.2 Resumen histórico

Debajo de los KPIs aparecen tres tarjetas con datos acumulados de todos los tiempos:

- **Monto aprobado este mes** (azul): suma en pesos de todos los créditos aprobados en el mes
- **Total histórico de evaluaciones** (oscuro): total de evaluaciones desde el inicio del sistema
- **Monto total aprobado histórico** (verde): suma acumulada de todos los montos aprobados

> Los montos se muestran en formato colombiano: `$1.250.000` (punto como separador de miles).

### 2.3 Distribución por clasificación

A la izquierda del panel inferior aparece la distribución de todas las evaluaciones históricas por clasificación (EXCELENTE, BUENO, REGULAR, ALTO RIESGO), con barras de progreso que muestran el porcentaje de cada una.

### 2.4 Últimas evaluaciones

A la derecha del panel inferior aparece la tabla con las 8 evaluaciones más recientes. Cada fila muestra:
- Nombre del solicitante y fecha
- Monto solicitado
- Score obtenido
- Decisión (APROBAR / REVISAR / RECHAZAR)

Haga clic en cualquier fila para ir al detalle de esa evaluación.

---

## 3. Nueva evaluación de crédito

Para crear una nueva evaluación, haga clic en **Nueva Evaluación** en el menú superior o en el botón azul del dashboard.

El formulario está dividido en cuatro secciones principales:

### 3.1 Datos del solicitante

| Campo | Descripción | Obligatorio |
|---|---|---|
| **Tipo de documento** | C.C., C.E. o Pasaporte | Sí |
| **Buscar empleado** | Campo de búsqueda por nombre o cédula (autocompletado) | No |
| **Cédula** | Número de documento del solicitante | Sí |
| **Nombre completo** | Nombre y apellidos | Sí |
| **Área** | Dependencia o área de trabajo | No |
| **Cargo** | Cargo que ocupa en la empresa | No |
| **Tipo de vinculación** | Indefinido / A término fijo / Prestación de servicios | Sí |
| **Antigüedad (meses)** | Tiempo de vinculación con la empresa en meses | Sí |
| **Salario bruto** | Salario mensual antes de deducciones | Sí |

> **Consejo:** Si la nómina está cargada, use el campo de búsqueda para autocompletar todos los datos del empleado automáticamente (ver sección 4).

### 3.2 Centrales de riesgo

| Campo | Descripción | Obligatorio |
|---|---|---|
| **Puntaje DataCrédito** | Score de central de riesgo (150 a 950) | Sí |
| **¿Crédito activo en FONDEINO?** | Si el solicitante ya tiene un crédito vigente | Sí |
| **% Capital pagado** | Porcentaje del capital ya pagado (0.00 = 0%, 1.00 = 100%). Solo aplica si tiene crédito activo | No |
| **Cuotas otras entidades** | Valor mensual de cuotas con bancos u otras entidades | No |

### 3.3 Descuentos mensuales FONDEINO

| Campo | Descripción |
|---|---|
| **Cuota aporte mensual** | Descuento mensual por concepto de aportes al fondo |
| **Cuota ahorro mensual** | Descuento mensual por concepto de ahorros en el fondo |

Estos valores se suman a las obligaciones para calcular la capacidad de pago.

### 3.4 Garantías acumuladas

| Campo | Descripción |
|---|---|
| **Saldo aportes acumulados** | Total de aportes acumulados del asociado en el fondo |
| **Saldo ahorros acumulados** | Total de ahorros acumulados del asociado en el fondo |

El sistema muestra el **Total Garantías** en tiempo real mientras ingresa los valores.

### 3.5 Condiciones del crédito

| Campo | Descripción | Obligatorio |
|---|---|---|
| **Modalidad** | Tipo de crédito (define la tasa de interés) | Sí |
| **Fecha de desembolso** | Fecha en que se entregaría el dinero | Sí |
| **Número de cuotas** | Plazo del crédito (1 a 48 cuotas) | Sí |
| **Monto solicitado** | Valor del crédito en pesos | Sí |
| **Motivo** | Descripción del destino del crédito | No |

Al seleccionar la **Modalidad**, el sistema muestra automáticamente la tasa mensual y nominal anual correspondiente.

### 3.6 Vista previa en tiempo real

A medida que llena el formulario, el panel **"Vista Previa del Análisis"** se actualiza automáticamente mostrando:

- **Salario Neto**: salario bruto menos 8% (4% salud + 4% pensión)
- **Mínimo Vital (50%)**: mitad del salario neto, que es el límite de endeudamiento permitido
- **Cuota Estimada**: cuota mensual calculada con PMT + seguro de vida
- **Disponible Final**: mínimo vital menos todas las cuotas (debe ser positivo)
- **% Endeudamiento**: porcentaje del salario neto comprometido en cuotas
- **Mínimo Vital**: indica si cumple (verde) o no cumple (rojo) el límite
- **Score Estimado**: puntaje calculado con los datos ingresados
- **Decisión estimada**: APROBAR / REVISAR / RECHAZAR

> Esta vista previa es una **estimación**. El resultado final lo calcula el servidor con mayor precisión.

### 3.7 Guardar la evaluación

Una vez completados todos los campos obligatorios, haga clic en **Evaluar y Guardar**. El sistema calculará el resultado final y lo llevará automáticamente al detalle de la evaluación.

---

## 4. Búsqueda de empleado por nombre

Si la nómina está cargada en el sistema, puede buscar automáticamente los datos de un empleado sin necesidad de digitarlos manualmente.

### 4.1 Búsqueda por nombre o cédula (autocompletado)

1. En el formulario de nueva evaluación, localice el campo **"Buscar empleado por nombre o cédula"**
2. Comience a escribir el nombre del empleado o su número de cédula (mínimo 2 caracteres)
3. Aparecerá una lista desplegable con los empleados que coinciden
4. Haga clic en el empleado correcto
5. El sistema completará automáticamente: cédula, nombre, área, cargo, tipo de vinculación, antigüedad y salario

### 4.2 Búsqueda por cédula (botón lupa)

1. Ingrese el número de cédula en el campo **Cédula**
2. Haga clic en el botón con el ícono de lupa (🔍) que está al lado del campo
3. Si el empleado está en la nómina, los datos se completan automáticamente
4. Si no se encuentra, aparece el mensaje "No encontrado — ingrese datos manualmente"

> **Importante:** Para que la búsqueda funcione, el administrador debe haber cargado previamente la nómina del período vigente (ver sección 11).

---

## 5. Entendiendo el resultado de la evaluación

Después de guardar una evaluación, el sistema muestra la página de detalle con todos los resultados.

### 5.1 Encabezado del resultado

En la parte superior aparece un resumen con:
- Nombre completo, cédula, cargo y área del solicitante
- Nombre del evaluador y fecha/hora de la evaluación
- **Score Total** (grande, en el centro): el puntaje crediticio de 0 a 100
- **Clasificación**: EXCELENTE, BUENO, REGULAR o ALTO RIESGO
- **DECISIÓN**: el resultado final en una etiqueta de color

#### Colores de las decisiones

| Color | Decisión | Significado |
|---|---|---|
| 🟢 Verde | APROBAR | El crédito cumple todos los requisitos |
| 🟡 Amarillo | REVISAR / CODEUDOR | Score entre 40-59, requiere análisis adicional o garantías |
| 🔴 Rojo | RECHAZAR | Score menor a 40 o no cumple el mínimo vital |
| 🔴 Rojo | RECHAZAR - CUOTA EXCEDE LÍMITE | La cuota supera el 50% del salario neto |

### 5.2 Análisis de ingresos y mínimo vital

Esta tabla muestra cómo se calcula el límite de endeudamiento:

1. **Salario Bruto**: el valor ingresado
2. **Salario Neto**: salario bruto × 92% (se descuenta 4% salud + 4% pensión)
3. **Mínimo Vital**: salario neto × 50% (límite máximo de endeudamiento mensual)

### 5.3 Obligaciones mensuales

Muestra todas las cuotas que comprometen el salario:
- Cuotas con otras entidades financieras
- Cuota aporte FONDEINO actual
- Cuota nueva estimada (la del crédito evaluado)
- **Total cuotas**: suma de todas las obligaciones

### 5.4 Validación del mínimo vital

| Campo | Descripción |
|---|---|
| **Disponible Final** | Mínimo vital menos total de cuotas. Debe ser positivo (verde). Si es negativo (rojo), el crédito se rechaza automáticamente |
| **Cumple Mínimo Vital** | SI (verde) o NO (rojo) |
| **% Endeudamiento** | Porcentaje del salario neto comprometido en cuotas |
| **Estado** | Descripción del estado de endeudamiento |

### 5.5 Scoring crediticio detallado

Tabla con el puntaje obtenido en cada uno de los 6 factores:

| Factor | Máximo |
|---|---|
| Puntaje DataCrédito | 25 pts |
| Antigüedad empresa | 15 pts |
| Tipo vinculación | 10 pts |
| Capacidad de pago | 25 pts |
| Garantías acumuladas | 15 pts |
| Historial crédito activo | 10 pts |
| **TOTAL** | **100 pts** |

Una barra de progreso visual muestra el score total sobre 100.

---

## 6. Plan de pagos

Al final de la página de detalle aparece la tabla completa del plan de pagos (amortización), con cada cuota del crédito.

### Columnas del plan de pagos

| Columna | Descripción |
|---|---|
| **#** | Número de cuota |
| **Fecha Pago** | Fecha en que vence cada cuota |
| **Días** | Días del período calculados con método DAYS360 |
| **Saldo Inicial** | Capital pendiente al inicio del período |
| **Interés** | Valor del interés de la cuota |
| **Capital** | Abono al capital en esa cuota |
| **Saldo Final** | Capital pendiente después del pago |
| **Seguro** | Seguro de vida (0.25% del saldo inicial) |
| **Cuota Total** | Valor total a pagar (interés + capital + seguro) |

La última fila muestra los **TOTALES** acumulados de la columna de intereses, capital, seguro y cuota total.

---

## 7. Exportar evaluación a PDF

Puede generar un documento PDF de cualquier evaluación para archivar o imprimir.

### Pasos para exportar

1. Abra el detalle de la evaluación que desea exportar
2. Haga clic en el botón **"Exportar PDF"** (esquina superior derecha)
3. Se abrirá una nueva pestaña del navegador con la versión de impresión
4. El sistema abrirá automáticamente el diálogo de impresión de su navegador
5. En el diálogo de impresión:
   - Seleccione la impresora **"Guardar como PDF"** (o similar según su sistema operativo)
   - Verifique que el tamaño de papel sea **A4**
   - Haga clic en **Guardar** o **Imprimir**

> También puede hacer clic en el botón **"Imprimir / Guardar PDF"** que aparece en la página de impresión antes de que se abra el diálogo automáticamente.

### Contenido del PDF

El documento PDF incluye:
- Encabezado con logo FONDEINO y datos de la evaluación
- Banner con nombre del solicitante, monto, cuotas y decisión destacada
- Tabla de análisis de ingresos y mínimo vital
- Tabla de obligaciones mensuales
- Validación del mínimo vital
- Condiciones del crédito
- Scoring detallado con barra de progreso
- Plan de pagos completo
- Pie de página con fecha de generación

---

## 8. Historial de evaluaciones

La sección de historial muestra todas las evaluaciones registradas en el sistema.

### 8.1 Acceder al historial

Haga clic en **Historial** en el menú superior.

### 8.2 Filtros de búsqueda

En la parte superior del historial encontrará filtros para encontrar evaluaciones específicas:

| Filtro | Cómo usar |
|---|---|
| **Buscar (cédula / nombre)** | Digite parte del nombre o cédula del solicitante |
| **Decisión** | Seleccione Todas, Aprobar, Revisar o Rechazar |
| **Desde** | Fecha de inicio del rango de búsqueda |
| **Hasta** | Fecha de fin del rango de búsqueda |

Haga clic en **Filtrar** para aplicar los filtros. Haga clic en el botón **X** para limpiar todos los filtros y ver todo el historial.

### 8.3 Tabla de resultados

La tabla muestra hasta 200 evaluaciones con las columnas:
- Fecha y hora
- Cédula
- Nombre
- Modalidad
- Monto (formato $1.250.000)
- Score
- Clasificación (con etiqueta de color)
- Decisión (con etiqueta de color)
- Evaluador
- Botones de acción: Ver detalle, Editar, Eliminar

### 8.4 Ver el detalle de una evaluación

Haga clic en el ícono del ojo (👁) en la columna de acciones para ver el detalle completo de cualquier evaluación.

---

## 9. Editar y eliminar evaluaciones

### 9.1 Editar una evaluación

Puede editar una evaluación para corregir datos o recalcular el resultado.

1. Localice la evaluación en el historial o en la página de detalle
2. Haga clic en el botón **Editar** (ícono de lápiz, color amarillo)
3. Modifique los campos que necesite corregir
4. Haga clic en **Recalcular y Guardar**
5. El sistema recalculará el score y la decisión con los nuevos datos

> **Restricción:** Los usuarios de tipo Comité solo pueden editar sus propias evaluaciones. Los administradores pueden editar cualquier evaluación.

### 9.2 Eliminar una evaluación

1. Localice la evaluación en el historial o en la página de detalle
2. Haga clic en el botón **Eliminar** (ícono de papelera, color rojo)
3. El sistema mostrará una pantalla de confirmación con los datos de la evaluación
4. Haga clic en **Sí, eliminar** para confirmar, o en **Cancelar** para volver
5. La evaluación será eliminada permanentemente del sistema

> **Advertencia:** Esta acción no se puede deshacer. Verifique que está eliminando la evaluación correcta antes de confirmar.

---

## 10. Decisión del comité

Los administradores pueden registrar la decisión formal del comité de crédito en cada evaluación.

### 10.1 Registrar la decisión

1. Abra el detalle de la evaluación
2. En la sección **"Decisión del Comité"** (visible solo para administradores), encontrará:
   - Campo **Decisión del Comité**: texto libre para registrar la decisión formal
   - Campo **Observaciones**: texto adicional, notas o condiciones
3. Complete los campos y haga clic en **Registrar Decisión**

La decisión del comité aparecerá registrada en el encabezado de la evaluación y en el PDF exportado.

---

## 11. Carga de nómina

La carga de nómina permite que el sistema reconozca automáticamente a los empleados cuando se evalúa un crédito.

### 11.1 Preparar el archivo de nómina

El archivo debe ser un Excel (`.xlsx`) con las siguientes columnas obligatorias:

| Columna | Descripción |
|---|---|
| `cedula` | Número de cédula del empleado |
| `nombre` | Nombre completo |
| `salario` | Salario bruto mensual |
| `area` | Área o dependencia |
| `cargo` | Cargo del empleado |
| `tipo_vinculacion` | `Indefinido`, `A termino fijo` o `Servicios` |
| `fecha_ingreso` | Fecha de ingreso (formato YYYY-MM-DD o DD/MM/YYYY) |

> Los nombres de columnas no distinguen mayúsculas/minúsculas y se aceptan variaciones comunes (ej. `Cédula`, `CEDULA`, `cedula`).

### 11.2 Cargar el archivo

1. En el menú superior, haga clic en **Administración → Cargar Nómina**
2. Haga clic en **Seleccionar archivo** y elija el archivo Excel de nómina
3. Haga clic en **Cargar Nómina**
4. El sistema procesará el archivo y mostrará un resumen:
   - Número de empleados cargados
   - Número de empleados actualizados
   - Errores encontrados (si los hay)

### 11.3 Historial de cargas

En **Administración → Historial Nóminas** puede ver todas las cargas realizadas con su fecha, usuario y número de registros procesados.

> **Nota:** Cada carga actualiza los registros existentes (por cédula) o crea nuevos. No elimina empleados anteriores.

---

## 12. Gestión de usuarios

Solo los administradores pueden crear y gestionar usuarios del sistema.

### 12.1 Ver usuarios

Vaya a **Administración → Usuarios** para ver la lista de todos los usuarios registrados.

### 12.2 Crear un usuario

1. En la lista de usuarios, haga clic en **Nuevo Usuario**
2. Complete los campos:
   - **Usuario**: nombre de inicio de sesión (sin espacios)
   - **Nombres y apellidos**: nombre completo
   - **Correo electrónico**: email del usuario
   - **Teléfono**: opcional
   - **Rol**: Administrador o Comité
   - **Contraseña** y **Confirmar contraseña**
3. Haga clic en **Guardar**

### 12.3 Editar un usuario

1. En la lista de usuarios, haga clic en el botón **Editar** del usuario
2. Modifique los datos necesarios
3. Haga clic en **Guardar**

### 12.4 Cambiar contraseña

1. En la lista de usuarios, haga clic en el botón **Contraseña** del usuario
2. Ingrese la nueva contraseña dos veces
3. Haga clic en **Guardar**

### 12.5 Activar / desactivar usuarios

En la pantalla de edición del usuario, active o desactive la casilla **Activo** para habilitar o bloquear el acceso del usuario al sistema. Un usuario inactivo no puede iniciar sesión.

---

## 13. Configuración del scoring

Los administradores pueden ajustar todos los parámetros del motor de scoring para que refleje las políticas crediticias de FONDEINO.

### 13.1 Acceder a la configuración

Vaya a **Administración → Config. Scoring**.

### 13.2 Parámetros configurables

#### Factor 1: DataCrédito (25 pts máx.)

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| Umbral DataCrédito EXCELENTE | Score mínimo para 25 pts | 700 |
| Umbral DataCrédito BUENO | Score mínimo para 15 pts | 500 |
| Umbral DataCrédito REGULAR | Score mínimo para 8 pts | 300 |
| Puntaje DataCrédito EXCELENTE | Puntos si score ≥ umbral excelente | 25 |
| Puntaje DataCrédito BUENO | Puntos si score ≥ umbral bueno | 15 |
| Puntaje DataCrédito REGULAR | Puntos si score ≥ umbral regular | 8 |

#### Factor 2: Antigüedad (15 pts máx.)

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| Meses antigüedad nivel 4 | Meses mínimos para máximo puntaje | 24 |
| Meses antigüedad nivel 3 | Meses mínimos para nivel 3 | 12 |
| Meses antigüedad nivel 2 | Meses mínimos para nivel 2 | 6 |
| Meses antigüedad nivel 1 | Meses mínimos para nivel 1 | 3 |
| Puntajes por nivel (1-4) | Puntos para cada nivel | 4, 8, 12, 15 |

#### Factor 3: Tipo de vinculación (10 pts máx.)

| Parámetro | Valor por defecto |
|---|---|
| Puntaje contrato indefinido | 10 |
| Puntaje contrato fijo | 7 |
| Puntaje prestación de servicios | 4 |

#### Factor 4: Capacidad de pago (25 pts máx.)

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| Umbral endeudamiento BAJO | % de endeudamiento para máximo puntaje | 30% |
| Umbral endeudamiento MEDIO | % de endeudamiento para puntaje medio | 50% |
| Puntaje capacidad EXCELENTE | Puntos si endeudamiento ≤ umbral bajo | 25 |
| Puntaje capacidad BUENO | Puntos si endeudamiento ≤ umbral medio | 15 |
| Puntaje capacidad REGULAR | Puntos si endeudamiento > umbral medio | 5 |

#### Factor 5: Garantías (15 pts máx.)

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| Umbral garantías nivel 3 | Cobertura mínima para máximo puntaje | 100% del crédito |
| Umbral garantías nivel 2 | Cobertura para nivel 2 | 50% del crédito |
| Umbral garantías nivel 1 | Cobertura para nivel 1 | 25% del crédito |
| Puntajes por nivel (1-3) | Puntos para cada nivel | 5, 10, 15 |

#### Factor 6: Historial crédito activo (10 pts máx.)

| Parámetro | Valor por defecto |
|---|---|
| Puntaje sin crédito activo | 10 |
| Puntaje crédito activo bien pagado (≥30%) | 7 |
| Puntaje crédito activo con poco pago | 3 |

#### Parámetros generales

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| % Mínimo vital | Porcentaje del salario neto como límite de endeudamiento | 50% |
| Score mínimo APROBAR | Score mínimo para decisión APROBAR | 60 |
| Score mínimo REVISAR | Score mínimo para decisión REVISAR | 40 |
| Seguro de vida | Porcentaje del saldo para seguro mensual | 0.25% |
| % Descuento salud | Porcentaje de descuento de salud | 4% |
| % Descuento pensión | Porcentaje de descuento de pensión | 4% |

### 13.3 Guardar cambios

Modifique los valores que necesite y haga clic en **Guardar Configuración**. Los cambios aplican inmediatamente a todas las nuevas evaluaciones. Las evaluaciones ya guardadas no se recalculan.

---

## 14. Gestión de modalidades

Las modalidades definen los tipos de crédito disponibles y sus tasas de interés.

### 14.1 Ver modalidades

Vaya a **Administración → Modalidades** para ver todas las modalidades configuradas.

### 14.2 Crear una modalidad

1. Haga clic en **Nueva Modalidad**
2. Complete:
   - **Nombre**: nombre descriptivo (ej. "Crédito de Libre Inversión")
   - **Tasa mensual**: tasa de interés mensual en decimal (ej. `0.015` para 1.5% mensual)
   - **PD Base**: probabilidad de incumplimiento base (parámetro de riesgo)
   - **Activa**: marque si la modalidad estará disponible en nuevas evaluaciones
3. Haga clic en **Guardar**

### 14.3 Editar una modalidad

Haga clic en el botón **Editar** de la modalidad que desea modificar, actualice los valores y guarde.

> **Nota:** Desactivar una modalidad no afecta las evaluaciones existentes, pero no estará disponible para nuevas evaluaciones.

---

## 15. Cómo se calcula el score

El sistema replica exactamente la lógica de la Plantilla Excel `Plantilla_Fondeino_V4.xlsm`. A continuación se explica el cálculo de cada factor:

### 15.1 Salario neto y mínimo vital

```
Salario Neto = Salario Bruto × (1 - 4% salud - 4% pensión) = Salario Bruto × 92%
Mínimo Vital = Salario Neto × 50%
```

### 15.2 Cuota del crédito

La cuota base se calcula con la fórmula PMT (igual a Excel):
```
Cuota Base = Monto × Tasa / (1 - (1 + Tasa)^(-N cuotas))
Seguro Vida = Saldo del período × 0.25%
Cuota Total = Cuota Base + Seguro Vida
```

El plan de pagos usa el método **DAYS360** para calcular los días exactos entre fechas, al igual que el Excel original.

### 15.3 Disponible final

```
Disponible Final = Mínimo Vital - (Cuota nueva + Cuotas otras entidades + Cuota aporte + Cuota ahorro)
```

Si `Disponible Final < 0` → Rechazo automático por incumplimiento del mínimo vital.

### 15.4 Score de DataCrédito (25 pts)

```
≥ 700 puntos  → 25 pts (EXCELENTE)
≥ 500 puntos  → 15 pts (BUENO)
≥ 300 puntos  → 8 pts  (REGULAR)
< 300 puntos  → 0 pts  (ALTO RIESGO)
```

### 15.5 Score de antigüedad (15 pts)

```
≥ 24 meses → 15 pts
≥ 12 meses → 12 pts
≥ 6 meses  → 8 pts
≥ 3 meses  → 4 pts
< 3 meses  → 0 pts
```

### 15.6 Score de vinculación (10 pts)

```
Indefinido           → 10 pts
A término fijo       → 7 pts
Prestación servicios → 4 pts
```

### 15.7 Score de capacidad de pago (25 pts)

```
% Endeudamiento = Total Cuotas / Salario Neto

≤ 30%  → 25 pts (EXCELENTE)
≤ 50%  → 15 pts (BUENO)
> 50%  → 5 pts  (REGULAR)
Disponible < 0 → 0 pts
```

### 15.8 Score de garantías (15 pts)

```
Cobertura = (Aportes + Ahorros) / Monto Solicitado

≥ 100% → 15 pts
≥ 50%  → 10 pts
≥ 25%  → 5 pts
< 25%  → 0 pts
```

### 15.9 Score historial crédito activo (10 pts)

```
Sin crédito activo                          → 10 pts
Con crédito activo + capital pagado ≥ 30%  → 7 pts
Con crédito activo + capital pagado < 30%  → 3 pts
```

### 15.10 Score total y clasificación

```
Score Total = suma de los 6 factores (máximo 100 pts)

80 – 100 pts → EXCELENTE → APROBAR
60 – 79 pts  → BUENO     → APROBAR
40 – 59 pts  → REGULAR   → REVISAR / CODEUDOR
0  – 39 pts  → ALTO RIESGO → RECHAZAR
```

---

## 16. Preguntas frecuentes

**¿Puedo cambiar la decisión que da el sistema?**  
El sistema genera una decisión automática basada en el score. El administrador puede registrar una **Decisión del Comité** diferente en el campo correspondiente de la evaluación, que queda documentada junto al resultado automático.

**¿Qué pasa si el empleado no está en la nómina?**  
Puede ingresar los datos manualmente. La búsqueda de empleados es una ayuda para agilizar el proceso, pero no es obligatoria.

**¿Los cambios en la configuración del scoring afectan evaluaciones anteriores?**  
No. Las evaluaciones ya guardadas mantienen sus valores originales. Solo las nuevas evaluaciones usarán la configuración actualizada.

**¿Puedo evaluar a alguien que ya tiene un crédito activo?**  
Sí. En el campo "¿Crédito activo en FONDEINO?" seleccione "Sí" e indique el porcentaje del capital ya pagado. Esto afecta el score del factor de historial crediticio.

**¿Cómo se maneja el seguro de vida en el plan de pagos?**  
El seguro se calcula como el 0.25% del saldo inicial de cada período. Este porcentaje es configurable en la sección de configuración del scoring.

**¿Por qué mi cuota estimada en el formulario es diferente a la del plan de pagos?**  
La vista previa del formulario usa una aproximación en JavaScript. El plan de pagos oficial usa el algoritmo exacto con DAYS360, que considera los días reales de cada período y puede diferir ligeramente.

**¿El sistema funciona en el celular?**  
Sí, el sistema es responsive y funciona en dispositivos móviles, aunque se recomienda usar un computador de escritorio para mayor comodidad al llenar el formulario de evaluación.

**¿Qué formato debe tener el archivo de nómina?**  
El archivo debe ser Excel (`.xlsx`). Ver la sección 11.1 para la lista de columnas requeridas.

**¿Puedo exportar el historial completo a Excel?**  
Esta funcionalidad no está disponible actualmente. Puede exportar las evaluaciones individuales a PDF.

---

*Manual preparado para FONDEINO — Fondo de Empleados*  
*Sistema de Evaluación Crediticia — Versión 1.0 — Abril 2026*
