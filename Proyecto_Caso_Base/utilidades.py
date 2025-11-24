import math
import pandas as pd
import os
import matplotlib.pyplot as plt


# -----------------------------------------------------------
# 1. Distancia Haversine
# -----------------------------------------------------------

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula distancia en km entre dos coordenadas geográficas.
    """

    R = 6371  # radio promedio de la Tierra en km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# -----------------------------------------------------------
# 2. Función para graficar rutas
# -----------------------------------------------------------

def graficar_rutas(rutas_por_vehiculo, clientes_df, deposito_df):
    """
    Dibuja las rutas en un gráfico simple.
    rutas_por_vehiculo es un dict:
    { vehiculo_id : [0, 5, 7, 0], ... }
    """

    plt.figure(figsize=(8, 8))

    # Graficar clientes
    plt.scatter(clientes_df.Longitude, clientes_df.Latitude,
                label="Clientes", c="blue")

    # Graficar depósito
    plt.scatter(deposito_df.Longitude, deposito_df.Latitude,
                label="Depósito", c="red", s=120, marker="X")

    # Graficar rutas
    for v, ruta in rutas_por_vehiculo.items():
        xs = []
        ys = []

        for n in ruta:
            if n == 0:
                lat = deposito_df.Latitude.iloc[0]
                lon = deposito_df.Longitude.iloc[0]
            else:
                lat = clientes_df.iloc[n - 1].Latitude
                lon = clientes_df.iloc[n - 1].Longitude

            ys.append(lat)
            xs.append(lon)

        plt.plot(xs, ys, marker="o", label=f"Vehículo {v}")

    plt.legend()
    plt.title("Rutas obtenidas")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.grid(True)
    plt.show()


# -----------------------------------------------------------
# 3. Generar archivo de verificación
# -----------------------------------------------------------

def generar_archivo_verificacion(rutas_por_vehiculo, output_path):
    """
    Crea el archivo verificacion_caso1.csv con el formato solicitado.
    rutas_por_vehiculo es una lista de diccionarios.
    """

    df = pd.DataFrame(rutas_por_vehiculo)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False, float_format="%.4f")

    return df
