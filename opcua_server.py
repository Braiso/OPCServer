'''
Mejoras:
- Generacion automatica de nodos
'''

# pip install opcua
from opcua import Server, ua
import time, json, os
from opcua_lib import build_node_dict

# Crear servidor
server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4841")
idx = server.register_namespace("CAFERSA")

# Nodo raiz
nodes = server.get_objects_node()

# **** ### SALIDAS PLC - ENTRADAS HALCON ### *****
Realizar_Vision = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Realizar_Vision\"", idx), "Realizar_Vision", 20.5)
Espesor_Nominal = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Espesor_Nominal\"", idx), "Espesor_Nominal", 0.0)
Cargar_Fichero_1 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Cargar_Fichero_1\"", idx), "Cargar_Fichero_1", False)
Cargar_Fichero_2 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Cargar_Fichero_2\"", idx), "Cargar_Fichero_2", False)
Control_Esquinas_1 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Control_Esquinas_1\"", idx), "Control_Esquinas_1", False)
Control_Esquinas_2 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Control_Esquinas_2\"", idx), "Control_Esquinas_2", False)
Control_Perforaciones_1 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Control_Perforaciones_1\"", idx), "Control_Perforaciones_1", False)
Control_Perforaciones_2 = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Control_Perforaciones_2\"", idx), "Control_Perforaciones_2", False)
Produccion = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"Produccion\"", idx), "Produccion", False)
ID_Pizarra_In = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"ID_Pizarra\"", idx), "ID_Pizarra_In", 0)
LiveBit_In = nodes.add_variable(ua.NodeId("\"\".\"SALIDAS\".\"LiveBit\"", idx), "LiveBit_In", False)

# **** ### ENTRADAS PLC - SALIDAS HALCON ### *****
COD_Error = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"COD_Error\"", idx), "COD_Error", 0)
Vision_Realizada = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Vision_Realizada\"", idx), "Vision_Realizada", False)
Largo_Medido = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Largo_Medido\"", idx), "Largo_Medido", 0.0)
Ancho_Medido = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Ancho_Medido\"", idx), "Ancho_Medido", 0.0)
Espesor_Medido = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Espesor_Medido\"", idx), "Espesor_Medido", 0.0)
Tercio_Visible = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Tercio_Visible\"", idx), "Tercio_Visible", 0)
Calidad_Tercio_1 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Calidad_Tercio_1\"", idx), "Calidad_Tercio_1", 0)
Calidad_Tercio_3 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Calidad_Tercio_3\"", idx), "Calidad_Tercio_3", 0)
Fichero_Cargado_1 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Fichero_Cargado_1\"", idx), "Fichero_Cargado_1", False)
Fichero_Cargado_2 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"Fichero_Cargado_2\"", idx), "Fichero_Cargado_2", False)
ID_Pizarra_Out = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"ID_Pizarra\"", idx), "ID_Pizarra_Out", 0)
ID_Produccion_1 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"ID_Produccion_1\"", idx), "ID_Produccion_1", 0)
ID_Produccion_2 = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"ID_Produccion_2\"", idx), "ID_Produccion_2", 0)
LiveBit_Out = nodes.add_variable(ua.NodeId("\"\".\"ENTRADAS\".\"LiveBit\"", idx), "LiveBit_Out", False)

# Hacer variables escribibles desde clientes
COD_Error.set_writable()
Vision_Realizada.set_writable()
Largo_Medido.set_writable()
Ancho_Medido.set_writable()
Espesor_Medido.set_writable()
Tercio_Visible.set_writable()
Calidad_Tercio_1.set_writable()
Calidad_Tercio_3.set_writable()
Fichero_Cargado_1.set_writable()
Fichero_Cargado_2.set_writable()
ID_Pizarra_Out.set_writable()
ID_Produccion_1.set_writable()
ID_Produccion_2.set_writable()
LiveBit_Out.set_writable()

# Crear diccionario de nodos para uso por parte del cliente
node_dict = {}
root = server.get_root_node()
children = root.get_child(["0:Objects"])
build_node_dict(children, node_dict,idx)

# Exportar a un archivo JSON
with open(os.path.dirname(__file__)+"/nodes.json", "w", encoding="utf-8") as f:
    json.dump(node_dict, f, ensure_ascii=False, indent=4)

# Arrancar servidor
server.start()
print("Servidor OPC UA iniciado en opc.tcp://127.0.0.1:4841")

try:
    while True:        
        time.sleep(1)
except KeyboardInterrupt:
    print('Servidor desconectado')
    server.stop()