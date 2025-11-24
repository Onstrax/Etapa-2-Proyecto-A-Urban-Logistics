# modelo_pyomo.py
from pyomo.environ import *


def construir_modelo(datos):
    """
    Construye el modelo CVRP base usando Pyomo.
    Entrada:
        datos: dict con claves:
            - distancias: dict {(i,j): float}
            - demanda: dict {i: float}
            - capacidad: dict {v: float}
            - rango: dict {v: float}
            - num_clients: int (número de clientes)
            - fuel_eff: float (km/gal)
            - fuel_price: float (COP/gal)
    Salida:
        model: ConcreteModel de Pyomo
    """

    # --- Extraer datos ---
    dist = datos["distancias"]
    demanda = datos["demanda"]
    capacidad = datos["capacidad"]
    rango = datos["rango"]
    V = list(capacidad.keys())          # lista de vehículos (IDs numéricos)
    N = datos["num_clients"]            # número de clientes
    fuel_eff = datos["fuel_efficiency"]
    fuel_price = datos["fuel_price"]

    model = ConcreteModel()

    # --- Conjuntos ---
    # Nodo 0 = depósito, nodos 1..N = clientes
    model.V = Set(initialize=V)
    model.N = Set(initialize=range(0, N + 1))      # 0..N
    model.Clients = Set(initialize=range(1, N + 1))  # 1..N

    # --- Parámetros ---
    # dist debe ser un dict con claves (i,j) para i,j en model.N
    model.dist = Param(model.N, model.N,
                       initialize=dist,
                       within=NonNegativeReals,
                       mutable=False)

    model.demanda = Param(model.Clients,
                          initialize=demanda,
                          within=NonNegativeReals,
                          mutable=False)

    model.capacidad = Param(model.V,
                            initialize=capacidad,
                            within=PositiveReals,
                            mutable=False)

    model.rango = Param(model.V,
                        initialize=rango,
                        within=PositiveReals,
                        mutable=False)

    # --- Variables ---
    # x[v,i,j] = 1 si el vehículo v va de i a j
    model.x = Var(model.V, model.N, model.N, within=Binary)

    # carga[v,i] = carga restante en el vehículo v justo después de visitar i (sólo i en Clients)
    model.carga = Var(model.V, model.Clients, within=NonNegativeReals)

    # --- Función objetivo ---
    def obj_rule(m):
        total_dist = sum(m.dist[i, j] * m.x[v, i, j]
                         for v in m.V for i in m.N for j in m.N)

        # Tiempo aproximado (asumimos velocidad 40 km/h -> convertimos a minutos)
        total_time = sum((m.dist[i, j] / 40) * 60 * m.x[v, i, j]
                         for v in m.V for i in m.N for j in m.N)

        # Costo combustible (km / km_por_galon -> galones * precio)
        total_fuel = sum((m.dist[i, j] / fuel_eff) * fuel_price * m.x[v, i, j]
                         for v in m.V for i in m.N for j in m.N)

        return total_dist + total_time + total_fuel

    model.obj = Objective(rule=obj_rule, sense=minimize)

    # ------------------------------------------------------------------
    # ------------------------- RESTRICCIONES ---------------------------
    # ------------------------------------------------------------------

    # 1. Cada cliente debe tener exactamente una llegada (desde algún i y algún vehículo)
    def r1(m, c):
        return sum(m.x[v, i, c] for v in m.V for i in m.N if i != c) == 1
    model.unica_llegada = Constraint(model.Clients, rule=r1)

    # 2. Cada cliente debe tener exactamente una salida (hacia algún j y algún vehículo)
    def r2(m, c):
        return sum(m.x[v, c, j] for v in m.V for j in m.N if j != c) == 1
    model.unica_salida = Constraint(model.Clients, rule=r2)

    # 3. Cada vehículo sale del depósito a lo sumo una vez
    def r3(m, v):
        return sum(m.x[v, 0, j] for j in m.Clients) <= 1
    model.salida_depot = Constraint(model.V, rule=r3)

    # 4. Cada vehículo vuelve al depósito a lo sumo una vez
    def r4(m, v):
        return sum(m.x[v, i, 0] for i in m.Clients) <= 1
    model.llegada_depot = Constraint(model.V, rule=r4)

    # 5. Balance de flujo por vehículo y cliente (entradas = salidas en cada cliente)
    def r5(m, v, c):
        return sum(m.x[v, i, c] for i in m.N if i != c) - sum(m.x[v, c, j] for j in m.N if j != c) == 0
    model.balance_flujo = Constraint(model.V, model.Clients, rule=r5)

    # ---------------- Vínculos entre x y carga ----------------

    # A) Si el vehículo v efectivamente visita c (al menos una entrada), la carga en c >= demanda[c]
    def carga_lower_link(m, v, c):
        return m.carga[v, c] >= m.demanda[c] * sum(m.x[v, i, c] for i in m.N if i != c)
    model.carga_lower_link = Constraint(model.V, model.Clients, rule=carga_lower_link)

    # B) Si el vehículo v no visita c, la carga en c debe ser 0 (esto se logra con la cota superior)
    def carga_upper_link(m, v, c):
        return m.carga[v, c] <= m.capacidad[v] * sum(m.x[v, i, c] for i in m.N if i != c)
    model.carga_upper_link = Constraint(model.V, model.Clients, rule=carga_upper_link)

    # 6. MTZ (adaptación con carga) para eliminar subciclos (i,j != 0)
    def mtz_carga(m, v, i, j):
        if i != j and i != 0 and j != 0:
            # Si x[v,i,j] = 1 entonces la carga en j debe ser al menos carga en i - (Q - demanda[j])
            return m.carga[v, i] - m.carga[v, j] + m.capacidad[v] * m.x[v, i, j] <= m.capacidad[v] - m.demanda[j]
        return Constraint.Skip
    model.mtz_carga = Constraint(model.V, model.Clients, model.Clients, rule=mtz_carga)

    # 7. Carga no excede la capacidad del vehículo
    def r7(m, v, c):
        return m.carga[v, c] <= m.capacidad[v]
    model.max_load = Constraint(model.V, model.Clients, rule=r7)

    # 8. Restricción de rango por vehículo (distancia total de la ruta <= rango)
    def r8(m, v):
        return sum(m.dist[i, j] * m.x[v, i, j] for i in m.N for j in m.N) <= m.rango[v]
    model.limite_rango = Constraint(model.V, rule=r8)

    # ------------------------------------------------------------------
    # Devolver el modelo construido
    return model
