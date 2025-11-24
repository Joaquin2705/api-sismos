import os
import boto3
import requests
from bs4 import BeautifulSoup

dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    url = os.environ["IGP_URL"]
    table_name = os.environ["SISMOS_TABLE"]
    table = dynamodb.Table(table_name)

    # 1. Descargar la página de sismos reportados
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    # 2. Parsear HTML
    soup = BeautifulSoup(resp.text, "html.parser")

    # Aquí asumo que hay una tabla con las filas de sismos:
    # ajusta el selector según lo que veas en el HTML (Inspeccionar)
    rows = soup.select("app-table table tbody tr")

    ultimos_10 = rows[:10]

    items_guardados = []

    for row in ultimos_10:
        celdas = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(celdas) < 4:
            # si la fila no tiene suficientes columnas, la ignoramos
            continue

        # Según el encabezado de la página:
        # 0 = Reporte sísmico (id)
        # 1 = Referencia
        # 2 = Fecha y hora (local)
        # 3 = Magnitud
        item = {
            "id": celdas[0],               # PK
            "reporte_sismico": celdas[0],
            "referencia": celdas[1],
            "fecha_hora_local": celdas[2],
            "magnitud": celdas[3],
        }

        table.put_item(Item=item)
        items_guardados.append(item)

    return {
        "statusCode": 200,
        "body": {
            "mensaje": "Sismos actualizados correctamente",
            "cantidad": len(items_guardados),
            "items": items_guardados,
        },
    }
