# README – Proyecto A, Caso 3

Optimización de rutas de distribución urbana con múltiples centros de distribución

## Introducción

El Caso 3 del Proyecto A plantea un problema de ruteo de vehículos en operaciones de distribución urbana en Bogotá. El objetivo consiste en determinar rutas eficientes que partan desde varios centros de distribución, atiendan a un conjunto de clientes con demanda conocida y regresen a un centro, todo mientras se minimiza el costo total de operación. Este costo incluye costos fijos por activación de vehículos y costos variables asociados a la distancia recorrida, al combustible y al tiempo del conductor.

El problema presenta características reales de la última milla urbana. La flota es heterogénea y tiene límites de capacidad y rango. Los clientes imponen restricciones sobre el tipo de vehículo que pueden recibir por razones de espacio. Cada cliente debe ser atendido exactamente una vez. Las distancias entre nodos se calculan mediante la fórmula de Haversine para utilizar distancias geográficas reales. Todo el modelo se implementa en Pyomo y se resuelve con el solver HiGHS bajo un límite de tiempo razonable, dado el tamaño del caso.

## Datos utilizados

El proyecto emplea cuatro archivos suministrados en formato CSV.
El archivo clients.csv contiene 90 clientes, cada uno con coordenadas, demanda y una restricción sobre el tamaño máximo del vehículo admitido.
El archivo depots.csv contiene 12 centros de distribución junto con su ubicación geográfica.
El archivo vehicles.csv contiene 45 vehículos de tres tipos (small van, medium van y light truck). Cada vehículo tiene capacidad de carga y un rango máximo de operación.
El archivo parameters_urban.csv contiene parámetros económicos esenciales como costos fijos, costo por kilómetro, costo del tiempo del conductor y parámetros de combustible asociados a cada tipo de vehículo.

Estos datos se procesan y se integran en el modelo para establecer distancias, restricciones, compatibilidades y costos.

## Distancias entre nodos

Las distancias entre todos los pares de nodos se calculan mediante la fórmula de Haversine, considerando un radio terrestre de 6371 kilómetros. Esta aproximación permite que el modelo utilice distancias geográficas realistas, lo cual es necesario para respetar los rangos máximos de los vehículos y para calcular correctamente el costo variable dependiente del recorrido.

## Formulación del modelo matemático

El modelo se implementa en Pyomo mediante una estructura estándar para problemas de ruteo de vehículos.

Los conjuntos incluyen los clientes, los depósitos, los nodos totales del sistema y los vehículos.
Los parámetros incluyen demand, cap, range, las distancias entre nodos, los costos por tipo de vehículo y la matriz de compatibilidad entre vehículos y clientes.
Las variables son binarias e indican si un vehículo viaja entre dos nodos y si un vehículo es activado para operar.

La función objetivo minimiza el costo total del sistema. Este costo incluye el costo fijo de activación por cada vehículo utilizado y el costo variable asociado a cada arco recorrido por cualquier vehículo.

Las restricciones incluyen las siguientes condiciones.
Cada cliente debe ser atendido exactamente una vez.
Se conserva el flujo en cada cliente, es decir, si un vehículo entra a un cliente debe también salir del mismo.
Cada vehículo debe iniciar y finalizar su ruta en un centro de distribución.
Ningún vehículo puede exceder su capacidad de carga.
La distancia total recorrida por un vehículo no puede superar su rango operativo.
Se garantiza que un vehículo solo puede atender a un cliente si el tipo de vehículo cumple con la restricción de tamaño impuesta por ese cliente.
Se establece una relación de enlace entre las variables de activación del vehículo y las variables de recorrido, con el fin de evitar rutas sin costo fijo asociado.

## Configuración del solver y manejo de la brecha de optimalidad

El modelo se resolvió con el solver HiGHS a través de la interfaz de Pyomo. Dado que el problema de ruteo de vehículos es combinatorio y contiene un número elevado de variables binarias, se definió explícitamente un presupuesto de tiempo de cómputo. En particular, se configuró HiGHS con un límite de tiempo de ciento ochenta segundos y una meta de brecha relativa de optimalidad del uno por ciento. La idea fue equilibrar la calidad de la solución con el tiempo disponible para ejecutar el modelo en un entorno académico y de recursos limitados.

Durante la ejecución, HiGHS realizó la búsqueda en el árbol de branch and bound e informó al final que alcanzó el límite de tiempo establecido. La condición de terminación fue maxTimeLimit y el estado de la solución reportado fue feasible. Esto significa que, aunque el solver no logró cerrar la brecha hasta el umbral del uno por ciento, sí encontró una solución factible que satisface todas las restricciones del modelo. En otras palabras, el solver mantuvo una cota inferior y una cota superior sobre el valor óptimo de la función objetivo, pero no alcanzó a acercar suficientemente ambas cotas dentro del presupuesto de tiempo definido.

En este contexto se tomó la decisión de trabajar con la mejor solución factible encontrada por el solver al momento de alcanzar el límite de tiempo. Esta decisión está justificada por varias razones. Primero, todas las restricciones del problema se verifican de manera explícita en el modelo y en los resultados, lo que garantiza la validez operativa de la solución. Segundo, el objetivo principal del proyecto es demostrar la correcta formulación e implementación del problema de ruteo de vehículos, junto con la construcción de rutas coherentes y un archivo de verificación consistente con la solución, más que obtener el óptimo global exacto a cualquier costo computacional. Tercero, en aplicaciones reales de logística es habitual fijar límites de tiempo y aceptar soluciones con brecha de optimalidad no nula siempre que sean factibles y suficientemente buenas para la toma de decisiones.
Adicionalmente, se verificó que la solución entregada por HiGHS no presenta violaciones de capacidad, rango o compatibilidad de vehículos, y que todos los clientes son atendidos exactamente una vez. Esto se comprobó mediante la tabla de resumen por vehículo y mediante la construcción del archivo verificacion_caso3.csv a partir de los arcos activos. La combinación de estas verificaciones permite concluir que, aunque la solución no esté certificada como óptima globalmente, sí es una solución robusta, operacionalmente válida y adecuada para los objetivos del Caso 3.

## Resultados obtenidos

El modelo utiliza dieciocho vehículos de los cuarenta y cinco disponibles.
La tabla veh_summary_df confirma que, para cada vehículo utilizado, la demanda atendida cumple con los límites de capacidad y que la distancia total recorrida se mantiene dentro del rango máximo permitido.
Todos los vehículos cumplen las restricciones de compatibilidad entre tipo y cliente.

Las rutas reconstruidas a partir de las variables del modelo muestran que cada vehículo parte de un centro de distribución, atiende una secuencia de clientes y finaliza en un centro.
Por ejemplo, la ruta del vehículo V001 sigue la secuencia CD05 → C045 → C047 → C030 → C020 → C042 → C016 → CD05.
El vehículo V004 recorre la ruta CD12 → C068 → C083 → C029 → C073 → CD07.
Las rutas reflejan una asignación coherente con la distribución geográfica y con las restricciones de capacidad y rango.

## Archivo verificacion_caso3.csv

El archivo verificacion_caso3.csv se generó a partir de todos los arcos activos del modelo (arcs_df).
Este procedimiento garantiza que se revisen exactamente las decisiones del solver y no una reconstrucción parcial de rutas.

El archivo contiene las siguientes columnas.
Vehicle
VehicleType
Capacity
Range
From
To
FromIsDepot
ToIsDepot
Distance_km
DemandAtTo

El archivo final contiene ciento ocho arcos, con noventa clientes distintos atendidos y una suma total de demanda igual a la demanda total original de mil ciento trece unidades. Con ello se verifica que todos los clientes fueron atendidos y que el archivo es apto para ser evaluado por el monitor o el profesor del curso.

## Conclusiones

El modelo desarrollado integra correctamente los costos fijos y variables, las restricciones operativas y las particularidades de una flota heterogénea con restricciones urbanas reales.
La solución obtenida cumple con todos los requisitos del Caso 3 del Proyecto A y ofrece rutas factibles, consistentes y justificadas dentro del límite de tiempo establecido.
El archivo de verificación contiene todas las decisiones del modelo y fue validado de manera explícita para asegurar que representa exactamente la solución del problema.
El enfoque utilizado puede servir como base para problemas futuros de mayor escala y para incorporar heurísticas de inicialización o mejoras metaheurísticas en escenarios donde se requiera reducir el tiempo de cómputo o aproximar mejor el óptimo global.
