import pandas as pd
from utilidades import calcular_distancia_haversine


def cargar_datos(ruta_clients, ruta_vehicles, ruta_depots, ruta_params):
    """
    Carga todos los CSV necesarios para el Caso Base.
    Devuelve un diccionario estructurado.
    """

    clients = pd.read_csv(ruta_clients)
    vehicles = pd.read_csv(ruta_vehicles)
    depots = pd.read_csv(ruta_depots)
    params = pd.read_csv(ruta_params)

    # Extraer parámetros base
    fuel_price = float(params.loc[params['Parameter'] == 'fuel_price', 'Value'].values[0])
    fuel_eff = float(params.loc[params['Parameter'] == 'fuel_efficiency_typical', 'Value'].values[0])

    return {
        "clients": clients,
        "vehicles": vehicles,
        "depots": depots,
        "fuel_price": fuel_price,
        "fuel_efficiency": fuel_eff
    }


def generar_matriz_distancias(datos):
    """
    Construye la matriz de distancias (km) entre todos los puntos:
    - depósito (índice 0)
    - clientes (1..n)
    """

    depot = datos["depots"].iloc[0]
    clients = datos["clients"]

    nodos = [(depot.Latitude, depot.Longitude)] + [
        (row.Latitude, row.Longitude) for _, row in clients.iterrows()
    ]

    N = len(nodos)

    dist = {}
    for i in range(N):
        for j in range(N):
            if i == j:
                dist[(i, j)] = 0.0
            else:
                lat1, lon1 = nodos[i]
                lat2, lon2 = nodos[j]
                dist_calc = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
                dist[(i, j)] = float(dist_calc)

    # Normalizar todos los valores a float
    for k, v in dist.items():
        dist[k] = float(v)

    return dist



def preparar_datos_pyomo(ruta_clients, ruta_vehicles, ruta_depots, ruta_params):
    """
    Carga todo, genera distancias y empaca datos para Pyomo.
    """

    datos = cargar_datos(ruta_clients, ruta_vehicles, ruta_depots, ruta_params)

    # Matriz distancias
    dist = generar_matriz_distancias(datos)

    clients = datos["clients"]
    vehicles = datos["vehicles"]

    num_clients = len(clients)

    # Demandas en dict {1: d1, 2: d2, ...}
    demanda = {i + 1: clients.iloc[i].Demand for i in range(num_clients)}

    # Capacidades y rangos
    capacidad = {int(v.VehicleID): float(v.Capacity) for _, v in vehicles.iterrows()}
    rango = {int(v.VehicleID): float(v.Range) for _, v in vehicles.iterrows()}

    return {
        "distancias": dist,
        "demanda": demanda,
        "capacidad": capacidad,
        "rango": rango,
        "num_clients": num_clients,
        "fuel_price": datos["fuel_price"],
        "fuel_efficiency": datos["fuel_efficiency"],
        "clients_df": clients,
        "vehicles_df": vehicles,
        "depots_df": datos["depots"]
    }