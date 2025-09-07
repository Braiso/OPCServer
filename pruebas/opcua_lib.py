from opcua import Client, ua
from typing import Final
import json,os

# -----------------------
# Cliente OPC UA
# -----------------------
class OpcClient:
    def __init__(self, endpoint_url, variables_dict):
        # Configuracion: deberian ser inmutables tras init
        self.endpoint_url: Final[str] = endpoint_url # URL OPC UA
        self.var_ids: Final[str] = variables_dict # {nombre_lógico -> nodeid_str}

        # Estado de ejecución: cambia a lo largo del ciclo de vida
        self._client = None # Sesión OPC UA activa
        self._sub = None # Objeto de suscripción activa 
        self._sub_handles = [] # Identificadores de "monitored items" devueltos por "subscribe_data_change"
        self.nodes = {}  # Cache de nodos resueltos {nombre_lógico -> Node}
        self.name_by_nodeid = {} # Cache inversa {nodeid_str -> nombre_lógico}

# Propiedad: "connected: bool"
# Propiedad: "subscribed: bool"
# Instanciar nodes con connect() y limpiar con disconnect()

# Invariantes:
# Tras connect(): _client is not None, nodes y name_by_nodeid no estan vacíos si var_ids no está vacío
# Tras disconnect(): _suscription is None, _clint is None, nodes == {} y name_by_nodeid == {}
# Si subscribe() es True, etonces connected debe ser True (relación jerárquica)
'''
    def connect(self,idx):
        self.client = Client(self.endpoint_url)
        self.client.connect()

        # Resolver nodos y leer valores iniciales
        for name, idstr in self.vars.items():
            n = self.client.get_node(ua.NodeId(idstr, idx))
            self.nodes[name] = n
            try:
                nodeid_str = n.nodeid.to_string()
                self.name_by_nodeid[nodeid_str] = name
            except Exception:
                pass

    def disconnect(self):
        try:
            if self.sub:
                # Anular suscripciones
                for h in self.sub_handles:
                    try:
                        self.sub.unsubscribe(h)
                    except Exception:
                        pass
                try:
                    self.sub.delete()
                except Exception:
                    pass
        finally:
            self.sub = None
            self.sub_handles = []
            if self.client:
                self.client.disconnect()
                self.client = None

    def subscribe(self, q):
        # Crear handler y suscripción
        handler = SubHandler(q, self.name_by_nodeid)
        self.sub = self.client.create_subscription(500, handler)
        self.sub_handles = []
        for name, node in self.nodes.items():
            try:
                h = self.sub.subscribe_data_change(node)
                self.sub_handles.append(h)
            except Exception as e:
                # Si falla una, continúa con las demás
                q.put(("log", None, f"Error al suscribir {name}: {e}", None))

    def read_all(self):
        # Lectura “bulk” inicial (útil si el servidor no emite cambio si no varía)
        out = {}
        for name, node in self.nodes.items():
            try:
                out[name] = node.get_value()
            except Exception as e:
                out[name] = f"<error: {e}>"
        return out

    def write(self, name, value):
        # Utilidad rápida para escribir (por ejemplo un bool)
        node = self.nodes.get(name)
        if not node:
            raise RuntimeError(f"Nodo desconocido: {name}")
        node.set_value(value)
'''

def build_node_dict(root_node, dic, idx_filter=None):
    # Recorre recursivamente todos los nodos hijos a partir de root_node
    # root_node: nodo inicial (por ejemplo, server.get_objects_node())
    # dic: diccionario donde se guardan los pares {BrowseName: NodeId}
    # idx_filter: si se indica, solo añade nodos de ese namespace index

    # Obtener hijos directos del nodo actual
    children = root_node.get_children()

    for child in children:
        try:
            # Obtener el nombre legible del nodo
            browse_name = child.get_browse_name().Name
            # Convertir NodeId a string (ejemplo: "ns=2;i=3")
            nodeid_str = child.nodeid.to_string()

            # Comprobar si es Variable y si coincide con el filtro de namespace
            if child.get_node_class() == ua.NodeClass.Variable:
                if idx_filter is None or child.nodeid.NamespaceIndex == idx_filter:
                    dic[browse_name] = nodeid_str
        except Exception:
            # Algunos nodos pueden no devolver browse_name o clase -> ignorar
            pass

        # Llamada recursiva para explorar los subnodos
        build_node_dict(child, dic, idx_filter)

# -----------------------
# Handler de suscripción
# -----------------------
class SubHandler:
    """Handler para recibir notificaciones de cambios"""
    def datachange_notification(self, node, val, data):
        # No meter trabajo pesado aquí (bloquea el hilo de callbacks)
        try:
            bn = node.get_browse_name()
        except Exception:
            bn = None
        print(f"[DataChange] {bn or node}: {val}")

    def event_notification(self, event):
        print(f"[Event] {event}")

if __name__ == "__main__":
    
    #------------------------
    # Configuracion
    #------------------------
    ENDPOINT = "opc.tcp://127.0.0.1:4841"
    NS_IDX = 2 # Indice de namespace
    # Cargar nodos desde archivo
    with open(os.path.dirname(__file__)+"/nodes.json", "r", encoding="utf-8") as f:
        VARIABLES = json.load(f)

    cliente = OpcClient(ENDPOINT,VARIABLES)
    pass