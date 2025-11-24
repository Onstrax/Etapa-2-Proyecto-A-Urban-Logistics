# Caso Base
Optimización de rutas de distribución urbana con un único centro de distribución

#IMPORTANTE
El archivo Proyecto_Caso_Base.ipynb está ejecutado sobre datos recortados 
debido a que el tiempo de ejecucion con los datos originales escaló a horas
y por cuestiones de tiempo no pudimos imprimir la verificacion con la totalidad de los datos
Sin embargo, para vizualizarlos simplemente se deben reiniciar los outputs (Clear all outputs) y el kernel (Restart)
y ejecutar uno por uno en orden descendente todos los bloques de codigo en el notebook.
Tras ejecutar el ultimo se podrá si la solucion es viable o no y quedará la informacion guardada en resultados/resultados.csv

## Introducción
El Caso Base plantea un problema de ruteo de vehículos para la distribución urbana partiendo de un único centro de distribución (CDA). El objetivo es determinar rutas eficientes que atiendan a un conjunto de clientes con demanda conocida y regresen al centro, minimizando costos operativos. 

El costo total incluye costos fijos de activación de vehículos y costos variables asociados a la distancia recorrida. La flota es heterogénea, con límites de capacidad y rango por vehículo. Cada cliente debe ser atendido exactamente una vez y se respetan restricciones de capacidad y rango de los vehículos.

Las distancias entre nodos se calculan mediante la fórmula de Haversine para reflejar la distancia geográfica real. El modelo se implementa en Pyomo y se resolvió con el solver HiGHS bajo un límite de tiempo razonable.

---

## Datos utilizados
Los datos provienen de archivos CSV:

- `data/clients.csv`: Contiene 10 clientes (en el caso de prueba reducido), cada uno con coordenadas y demanda.
- `data/depots.csv`: Contiene un único centro de distribución (CDA) con su ubicación geográfica.
- `data/vehicles.csv`: Contiene 5 vehículos heterogéneos, cada uno con capacidad y rango máximo de operación.

Estos datos se integran al modelo para establecer distancias, restricciones de capacidad y rango, y compatibilidades de vehículos.

---

## Distancias entre nodos
Se utilizan distancias geográficas calculadas con la fórmula de Haversine, considerando un radio terrestre de 6371 km. Esto permite:

- Respetar los rangos máximos de los vehículos.
- Calcular correctamente los costos variables asociados a la distancia recorrida.

---

## Formulación del modelo matemático
El modelo se implementa en Pyomo usando una estructura estándar de problemas de ruteo de vehículos (VRP):

- **Conjuntos:** Clientes, depósito, nodos totales y vehículos.  
- **Parámetros:** Demanda de clientes, capacidad y rango de vehículos, distancias entre nodos.  
- **Variables:** Binarias que indican si un vehículo viaja entre dos nodos y si se activa.  
- **Función objetivo:** Minimiza el costo total (costo fijo + costo por distancia recorrida).  

### Restricciones:
1. Cada cliente es atendido exactamente una vez.  
2. Se conserva flujo en cada cliente (entrada = salida).  
3. Cada vehículo inicia y finaliza su ruta en el depósito.  
4. Ningún vehículo excede su capacidad de carga.  
5. Ningún vehículo supera su rango máximo.  

---

## Configuración del solver
- Solver: HiGHS vía Pyomo.  
- Límite de tiempo: 180 segundos.  
- Brecha de optimalidad relativa: 1%.  

Dado el carácter combinatorio del problema, se utilizó la mejor solución factible encontrada al límite de tiempo. Todas las restricciones se verificaron explícitamente.

---

## Resultados obtenidos
- Se utilizaron 3 de los 5 vehículos disponibles.  
- Todas las rutas respetan capacidad y rango de los vehículos.  
- Cada cliente es atendido exactamente una vez.  
- Rutas reconstruidas desde la variable `rutas_por_vehiculo`:

  Ejemplos:  
  - `V001`: CDA → C006 → C004 → C001 → C009 → C005 → C008 → CDA  
  - `V005`: CDA → C003 → C002 → C007 → CDA  

- Archivo de resultados generado: `resultados/resultados.csv`, con columnas:  
  `VehicleId`, `DepotId`, `RouteSequence`, `InitialLoad`, `ClientsServed`, `DemandsSatisfied`.  
- Validación realizada con `base_case_verification.py` confirmó que todas las rutas son factibles.

---

## Archivo de verificación
El archivo `resultados/resultados.csv` contiene todas las decisiones del modelo y permite verificar:

- Capacidad y rango de cada vehículo.  
- Que cada cliente fue visitado exactamente una vez.  
- Correspondencia entre demanda de clientes y demanda satisfecha en la ruta.  

---

## Conclusiones
El modelo implementado integra correctamente costos fijos y variables, restricciones de capacidad y rango, y asegura rutas factibles para todos los clientes. La solución obtenida representa una solución operacionalmente válida, consistente y robusta para el Caso Base, y el archivo de verificación permite validar explícitamente la solución para fines de entrega o revisión académica.


