# Proyecto A – Caso 2 (LogistiCo – Urban Logistics Bogotá)

## 1. Introducción

Este documento describe la implementación y los resultados del **Caso 2 (proyecto especializado)** del Proyecto A de logística urbana.

El objetivo es **planear rutas diarias de distribución** para una empresa de paquetería con:

* **Múltiples centros de distribución (CD)** con inventario limitado
* **Flota heterogénea** (vans y camiones ligeros) con capacidad y autonomía distintas
* **Función objetivo unificada de costos** (fijo, distancia, tiempo y combustible)

La solución se implementó en un **notebook de Google Colab** usando:

* `Python`
* `Pyomo` (modelado)
* `HiGHS` (solver MIP)
* `pandas` / `numpy` (manejo de datos)

---

## 2. Datos utilizados

Se usan cuatro fuentes de datos en formato CSV:

* **`clients.csv`**

  * `ClientID`, `StandardizedID` (C001, C002, …)
  * `LocationID` y coordenadas (`Latitude`, `Longitude`)
  * `Demand` (kg)

* **`depots.csv`**

  * `DepotID`, `StandardizedID` (CD01, CD02, …)
  * `LocationID` y coordenadas
  * `Capacity` (inventario máximo disponible en kg)

* **`vehicles.csv`**

  * `VehicleID` (1, 2, …)
  * `VehicleType` (V001, V002, …) – usado como identificador visible
  * `StandardizedID` (small van, medium van, light truck) – usado como tipo lógico
  * `Capacity` (kg)
  * `Range` (km de autonomía)

* **`parameters_urban.csv`**

  * Parámetros globales de costo:

    * `C_fixed` (costo fijo por vehículo usado)
    * `C_dist` (costo por km)
    * `C_time` (costo por hora)
    * `fuel_price` (precio por galón)
  * Velocidad urbana promedio, si se incluye (por defecto 25 km/h)

Además, se genera el archivo de salida:

* **`verificacion_caso2.csv`**

  * En el formato requerido por el enunciado (`VehicleId`, `DepotId`, `RouteSequence`, etc.), para validación automática.

---

## 3. Decisiones de modelado

### 3.1 Representación de la red y distancias

* Nodos:

  * Conjunto de clientes `C` (LocationID de clientes).
  * Conjunto de depósitos `D` (LocationID de CDs).
  * `N = C ∪ D`.

* Distancias:

  * Se calcula la distancia entre nodos con una **métrica Manhattan en km** sobre latitud/longitud:

```math
\Delta \text{lat}_\text{km} \approx 111 \cdot |\Delta \text{lat}|
```

```math
\Delta \text{lon}_\text{km} \approx 111 \cdot \cos(\text{lat}_\text{media}) \cdot |\Delta \text{lon}|
```

```math
d[i,j] = \Delta \text{lat}_\text{km} + \Delta \text{lon}_\text{km}
```

* Solo se consideran arcos `A = {(i,j) ∈ N×N : i ≠ j}`.

### 3.2 Costos de combustible

Se define una eficiencia típica (km/gal) según el tipo de vehículo:

* small van ≈ 40 km/gal
* medium van ≈ 30 km/gal
* light truck ≈ 25 km/gal

El costo de combustible por vehículo es:

```math
C^\text{fuel}_v = \frac{\text{dist}_v}{\text{eff}_v} \cdot \text{fuel\_price}
```

---

## 4. Formulación del modelo de optimización

### 4.1 Conjuntos

* `C`: clientes
* `D`: centros de distribución
* `N = C ∪ D`: nodos
* `V`: vehículos
* `A ⊂ N×N`: arcos dirigidos `(i,j)` con `i ≠ j`

### 4.2 Parámetros

* `d[i,j]`: distancia (km) entre nodos `i` y `j`.
* `demand[c]`: demanda del cliente `c` (kg).
* `depot_capacity[s]`: inventario disponible en CD `s` (kg).
* `capacity_v[v]`: capacidad de carga del vehículo `v` (kg).
* `range_v[v]`: autonomía máxima del vehículo `v` (km).
* `speed_v[v]`: velocidad media (km/h).
* `eff_v[v]`: eficiencia de combustible (km/gal).
* `C_fixed`, `C_dist`, `C_time`, `fuel_price`: parámetros de costo globales.

### 4.3 Variables de decisión

* `x[i,j,v] ∈ {0,1}`
  = 1 si el vehículo `v` recorre el arco `i → j`.

* `q[c,v] ≥ 0`
  = cantidad (kg) que el vehículo `v` entrega al cliente `c`.

* `z[v,s] ∈ {0,1}`
  = 1 si el vehículo `v` sale (y regresa) del depósito `s`.

* `y_use[v] ∈ {0,1}`
  = 1 si el vehículo `v` se utiliza.

* `dist_v[v] ≥ 0`
  = distancia total recorrida por `v`.

* `time_v[v] ≥ 0`
  = tiempo total de ruta de `v` (horas).

* `u[c,v]`
  = variables MTZ para eliminar subtours en clientes.

* `load_vs[v,s] ≥ 0`
  = carga total (kg) que el vehículo `v` saca del CD `s`.

### 4.4 Función objetivo

Se minimiza el costo logístico total:

```math
Z =
C_\text{fixed} \sum_v y\_\text{use}[v]
+ C_\text{dist} \sum_v \text{dist}_v[v]
+ C_\text{time} \sum_v \text{time}_v[v]
+ \sum_v \frac{\text{dist}_v[v]}{\text{eff}_v[v]} \cdot \text{fuel\_price}
```

### 4.5 Restricciones principales

1. **Definición de distancia y tiempo por vehículo**

```math
\text{dist}_v[v] = \sum_{(i,j)\in A} d[i,j] \, x[i,j,v]
```

```math
\text{dist}_v[v] \leq \text{range}_v[v] \quad \forall v
```

```math
\text{time}_v[v] = \frac{\text{dist}_v[v]}{\text{speed}_v[v]} \quad \forall v
```

2. **Visita única por cliente**

Cada cliente es atendido exactamente una vez:

```math
\sum_v \sum_{i:(i,c)\in A} x[i,c,v] = 1
\quad \forall c \in C
```

3. **Conservación de flujo en clientes**

Para cada vehículo y cliente:

```math
\sum_{i:(i,c)\in A} x[i,c,v] =
\sum_{j:(c,j)\in A} x[c,j,v]
\quad \forall c \in C,\; \forall v \in V
```

4. **Asignación vehículo–depósito y salida/retorno**

Cada vehículo se asigna a un único CD si se usa:

```math
\sum_{s \in D} z[v,s] = y\_\text{use}[v]
\quad \forall v \in V
```

Inicio y fin en el mismo CD:

```math
\sum_{j:(s,j)\in A} x[s,j,v] = z[v,s]
\quad \forall v \in V,\; \forall s \in D
```

```math
\sum_{i:(i,s)\in A} x[i,s,v] = z[v,s]
\quad \forall v \in V,\; \forall s \in D
```

5. **Capacidad del vehículo**

```math
\sum_{c \in C} q[c,v] \leq \text{capacity}_v[v]
\quad \forall v \in V
```

Vínculo visita–entrega:

```math
q[c,v] \leq \text{demand}[c] \cdot
\sum_{i:(i,c)\in A} x[i,c,v]
\quad \forall c \in C,\; \forall v \in V
```

6. **Satisfacción de demanda**

```math
\sum_{v \in V} q[c,v] = \text{demand}[c]
\quad \forall c \in C
```

7. **Inventario de centros de distribución**

Vínculo carga–CD:

```math
\text{load\_vs}[v,s] \leq \text{capacity}_v[v] \cdot z[v,s]
\quad \forall v \in V,\; \forall s \in D
```

```math
\text{load\_vs}[v,s] \geq
\sum_{c \in C} q[c,v] - \text{capacity}_v[v] \cdot (1 - z[v,s])
\quad \forall v \in V,\; \forall s \in D
```

Capacidad del CD:

```math
\sum_{v \in V} \text{load\_vs}[v,s]
\leq \text{depot\_capacity}[s]
\quad \forall s \in D
```

8. **Eliminación de subtours (MTZ)**

Se usan restricciones tipo Miller–Tucker–Zemlin en `u[c,v]` únicamente sobre clientes, para evitar ciclos internos que no pasen por el depósito:

```math
u[i,v] - u[j,v] + n_\text{clientes} \cdot x[i,j,v]
\leq n_\text{clientes} - 1
```

para clientes `i ≠ j` y cada vehículo `v`.

---

## 5. Implementación

Se desarrolló un **notebook de Colab** con la siguiente estructura:

1. Carga de librerías e instalación de `pyomo` y `highspy`.
2. Lectura de CSV y construcción de diccionarios de parámetros.
3. Cálculo de la matriz de distancias Manhattan.
4. Construcción del modelo en `Pyomo` (conjuntos, parámetros, variables, objetivo y restricciones).
5. Resolución con **HiGHS** via `SolverFactory("highs")`.
6. Extracción de solución:

   * Rutas por vehículo.
   * Demanda servida por cliente.
   * Utilización de vehículos y depósitos.
   * Archivo `verificacion_caso2.csv`.
7. Visualización:

   * Tablas (`pandas.DataFrame`).
   * Gráficas de barras y heatmaps (`matplotlib`).
   * Mapa de rutas con Folium (opcional).

El solver HiGHS alcanzó una solución **óptima** con gap relativo de alrededor de `0.01%`.

---

## 6. Resultados

### 6.1 Asignación de demanda

* Hay **9 clientes (C001–C009)**.
* En el DataFrame de demanda por cliente se observa:

  * `Demand` = `Delivered` para todos los clientes.
  * `Fulfillment_% = 100%` en todos los casos.

Es decir, **se satisface el 100% de la demanda de todos los clientes**.

Además, cada cliente queda asociado a:

* Un único `VehicleId` (V001–V006).
* El `DepotId` del cual sale ese vehículo.

### 6.2 Utilización de centros de distribución

Del resumen de depósitos:

* Se usan efectivamente 4 centros:

| DepotId | Capacity | Used | Utilization_% |
| ------- | -------- | ---- | ------------- |
| CD05    | 28       | 26   | ~92.9%        |
| CD09    | 43       | 43   | 100%          |
| CD11    | 16       | 15   | 93.75%        |
| CD12    | 18       | 18   | 100%          |

* El resto de CDs (CD01–CD04, CD06–CD10) no despachan carga en esta solución (utilización 0%).

Esto muestra una **fuerte concentración de carga** en CDs 09 y 12, y un uso casi pleno de los CDs 05 y 11.

### 6.3 Utilización de vehículos

En el resumen de vehículos:

* Se dispone de 6 vehículos (V001–V006), pero solo **4 son utilizados** (V001, V002, V003 y V005).
* Cargas aproximadas:

| VehicleId | Load (kg) | Capacity (kg) | Utilization_% |
| --------- | --------- | ------------- | ------------- |
| V001      | 42        | ≈132          | ~31.8%        |
| V002      | 26        | ≈108          | ~24.0%        |
| V003      | 18        | ≈91.5         | ~19.7%        |
| V005      | 15        | ≈22.7         | ~66.2%        |
| V004      | 0         | ≈32.9         | 0%            |
| V006      | 0         | ≈22.7         | 0%            |

Se observa que:

* El vehículo V005 (tipo light truck) opera cerca de 2/3 de su capacidad.
* Los vehículos V001–V003 tienen aún capacidad ociosa; el modelo prioriza la **minimización de costos**, no la máxima utilización.

### 6.4 Rutas por vehículo

A partir del DataFrame de rutas (`routes_df`), la solución óptima genera **4 rutas**:

* **V001 – CD09**

  * Ruta: `CD09–C003–C005–C008–C007–CD09`
  * Atiende 4 clientes.
  * Carga inicial: 42 kg.
  * Distancia ≈ 30.3 km, tiempo ≈ 1.21 h.

* **V002 – CD05**

  * Ruta: `CD05–C006–C002–CD05`
  * Atiende 2 clientes.
  * Carga inicial: 26 kg.
  * Distancia ≈ 17.8 km.

* **V003 – CD12**

  * Ruta: `CD12–C004–C001–CD12`
  * Atiende 2 clientes.
  * Carga inicial: 18 kg.
  * Distancia ≈ 29.3 km.

* **V005 – CD11**

  * Ruta: `CD11–C009–CD11`
  * Atiende 1 cliente.
  * Carga inicial: 15 kg.
  * Distancia ≈ 9.0 km.

Las matrices vehículo–cliente y depósito–cliente permiten visualizar:

* Qué clientes atiende cada vehículo (bloques de carga en la matriz).
* Qué CD abastece a cada cliente (relación DepotId–ClientId).

### 6.5 Costos por vehículo

Se calculó el desglose de costos por vehículo:

* Componente fijo: `C_fixed · y_use[v]`.
* Componente por distancia: `C_dist · dist_v[v]`.
* Componente por tiempo: `C_time · time_v[v]`.
* Componente de combustible: `dist_v[v]/eff_v[v] · fuel_price`.

La solución resultante minimiza el costo total combinando:

* Número de vehículos usados (4 de 6).
* Distancias moderadas.
* Buena utilización de los CDs con inventario.

### 6.6 Archivo de verificación

Se generó el archivo **`verificacion_caso2.csv`** con el formato exigido:

* `VehicleId` (V001, V002, …)
* `DepotId` (CDxx)
* `InitialLoad`
* `RouteSequence` (ej. `CD09-C003-C005-C008-C007-CD09`)
* `ClientsServed`
* `DemandsSatisfied` (lista de cargas en orden de visita)
* `TotalDistance`, `TotalTime`, `FuelCost`

Este archivo es coherente con los DataFrames de rutas, demandas y cargas, y puede ser usado para validación automática.

---

## 7. Conclusiones

* Se construyó e implementó un **modelo MDVRP con capacidad e inventario** usando Pyomo y resuelto con HiGHS.

* El modelo:

  * Utiliza distancias Manhattan basadas en coordenadas reales.
  * Respeta capacidad de vehículos, autonomía y capacidad de inventario de cada CD.
  * Satisface el 100% de la demanda de todos los clientes.
  * Usa solo 4 vehículos de 6 y 4 CDs de 12, reduciendo costos sin sacrificar servicio.

* La solución muestra:

  * Concentración de la carga en unos pocos CDs bien posicionados.
  * Rutas relativamente cortas que agrupan clientes cercanos a cada CD.
  * Espacio para extensiones: ventanas de tiempo, tipos de vehículo adicionales, restricciones de zonas, etc.

En resumen, el modelo implementado cumple con los requisitos del **Caso 2 del Proyecto A**, genera rutas factibles y económicamente eficientes, y produce salidas (tablas, gráficas y archivo de verificación) que permiten analizar y comunicar claramente la solución obtenida.
