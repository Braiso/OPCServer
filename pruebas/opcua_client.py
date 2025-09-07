import threading,queue,time,json,os
import tkinter as tk
from tkinter import ttk, messagebox
from opcua import Client, ua
from opcua_lib import SubHandler

'''
Manejador que espera la librería python-opcua para entregar las notificaciones de una suscripción.
Cuando haces sub = client.create_subscription(500, handler), el cliente llamará a los métodos de handler
 desde un hilo interno cada vez que haya un cambio de datos o un evento.

Es una clase cualquiera; no hereda de nada especial.
Solo necesita definir ciertos métodos con nombres esperados por la librería

Se invoca en cada notificación de cambio de datos de un ítem monitorizado.
Firma exacta: datachange_notification(self, node, val, data).

Parametros:
    - node: es el Node asociado al ítem monitorizado (útil para consultar nombres o atributos).

    - val: valor nuevo, ya “desempaquetado” a un tipo Python (la librería extrae el Variant y te pasa el valor puro).
    Puedes usarlo directamente.

    - data: objeto DataChangeNotif con metadatos de la notificación; dentro lleva el monitored_item
    (con Value, SourceTimestamp, ServerTimestamp, etc.) y subscription_data
    (por ejemplo, client_handle, atributo monitorizado, filtros…).
    Si necesitas marcas de tiempo o el código de estado, sácalos de data.monitored_item. 
'''

#------------------------
# Configuracion
#------------------------
endpoint = Client("opc.tcp://127.0.0.1:4841")
NS_IDX = 2 # Indice de namespace

# Cargar nodos desde archivo
with open(os.path.dirname(__file__)+"/nodes.json", "r", encoding="utf-8") as f:
    VARIABLES = json.load(f)

try:
    endpoint.connect()
    print("Conectado al servidor OPC UA")

    # Obtener el nodo raíz
    root = endpoint.get_root_node()
    print("Nodo raíz:", root)

    # Obtener el nodo de objetos
    objects = endpoint.get_objects_node()
    print("Nodo de objetos:", objects)

    # Acceder a las variables
    
    # **** ### SALIDAS PLC - ENTRADAS HALCON ### *****
    Realizar_Vision = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Realizar_Vision\"")
    Espesor_Nominal = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Espesor_Nominal\"")
    Cargar_Fichero_1 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Cargar_Fichero_1\"")
    Cargar_Fichero_2 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Cargar_Fichero_2\"")
    Control_Esquinas_1 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Control_Esquinas_1\"")
    Control_Esquinas_2 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Control_Esquinas_2\"")
    Control_Perforaciones_1 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Control_Perforaciones_1\"")
    Control_Perforaciones_2 = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Control_Perforaciones_2\"")
    Produccion = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"Produccion\"")
    ID_Pizarra_In = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"ID_Pizarra\"")
    LiveBit_In = endpoint.get_node("ns=2;s=\"\".\"SALIDAS\".\"LiveBit\"")

    # **** ### ENTRADAS PLC - SALIDAS HALCON ### *****
    COD_Error = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"COD_Error\"")
    Vision_Realizada = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Vision_Realizada\"")
    Largo_Medido = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Largo_Medido\"")
    Ancho_Medido = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Ancho_Medido\"")
    Espesor_Medido = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Espesor_Medido\"")
    Tercio_Visible = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Tercio_Visible\"")
    Calidad_Tercio_1 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Calidad_Tercio_1\"")
    Calidad_Tercio_3 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Calidad_Tercio_3\"")
    Fichero_Cargado_1 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Fichero_Cargado_1\"")
    Fichero_Cargado_2 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"Fichero_Cargado_2\"")
    ID_Pizarra_Out = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"ID_Pizarra\"")
    ID_Produccion_1 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"ID_Produccion_1\"")
    ID_Produccion_2 = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"ID_Produccion_2\"")
    LiveBit_Out = endpoint.get_node("ns=2;s=\"\".\"ENTRADAS\".\"LiveBit\"")
    
    # Monitorizar las variables
    def datachange_handler(node, val, data):
        print(f"Nuevo valor para {node.get_browse_name()}: {val}")

    # Suscripción (periodo/publishing interval en ms)
    '''
    Se instancia un manejador de la clase SubHandler,
    que contedrá los métodos necesarios para manejar la notificaciones 
    de cambios y eventos.
    '''
    handler = SubHandler()

    # Se crea la suscripción utilizando el método create_subscription del cliente OPC UA.
    sub = endpoint.create_subscription(500, handler)

    # Se suscribe a los cambios en el nodo específico.
    handle_cod_error = sub.subscribe_data_change(COD_Error)

    # Ejemplo de escritura en una variable
    while True:
        # Leer el valor actual
        current_value = COD_Error.get_value()
        
        # print(f"Valor actual de COD_Error: {current_value}")

        time.sleep(10)  # Esperar 10 segundos antes de la siguiente iteración

except Exception as e:
    print("Error:", e)

finally:
    endpoint.disconnect()
    print("Desconectado del servidor OPC UA")
