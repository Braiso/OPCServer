import logging,sys
from typing import Any
from opcua import ua

class OpcServerError(RuntimeError):
    """
    Excepción base para todos los errores relacionados con OpcServer.

    Hereda de RuntimeError, pero define un tipo específico para el dominio OPC.
    Esto permite distinguir fácilmente, en bloques try/except, entre errores
    de la librería estándar y los que provienen del cliente OPC.
    """
    def __init__(self, endpoint: str, message: str, original: Exception | None = None):
        super().__init__(f"{message} (endpoint={endpoint})")
        self.endpoint = endpoint
        self.original = original

def validate_types(node_line: dict[str,Any])->dict:  
    """
    Valida que 'datatype' sea soportado y que 'initial' concuerde con el tipo.
    - Convierte datatype (str) -> ua.VariantType
    - Castea 'initial' a su homólogo Python
    - Devuelve el mismo dict mutado
    """

    TYPE_MAP = {"boolean":ua.VariantType.Boolean,
                "sbyte":ua.VariantType.SByte,
                "byte":ua.VariantType.Byte,
                "int16":ua.VariantType.Int16,
                "uint16":ua.VariantType.UInt16,
                "int32":ua.VariantType.Int32,
                "uint32":ua.VariantType.UInt32,
                "int64":ua.VariantType.Int64,
                "uint64":ua.VariantType.UInt64,
                "float":ua.VariantType.Float,
                "double":ua.VariantType.Double,
                "string":ua.VariantType.String
    }              

    _TRUE = {"1", "true", "t", "yes", "y", "si", "sí"}
    _FALSE = {"0", "false", "f", "no", "n", ""}

    # Ver que el tipo de datos este contemplado
    dtype_key = str(node_line["datatype"]).strip().lower()
    if dtype_key not in TYPE_MAP:
        raise ValueError(f"Datatype no soportado: {node_line['datatype']!r}")

    # Casteo según vtype
    vtype = TYPE_MAP[dtype_key]
    raw = str(node_line.get("initial", "")).strip()

    # bool
    if vtype == ua.VariantType.Boolean:
        low = raw.lower()
        if low in _TRUE:
            initial = True
        elif low in _FALSE:
            initial = False
        else:
            raise ValueError(f"Valor inicial no es booleano: {raw!r}")

    # string
    elif vtype == ua.VariantType.String:
        initial = raw 

    # int
    elif vtype in {
            ua.VariantType.SByte, ua.VariantType.Byte,
            ua.VariantType.Int16, ua.VariantType.UInt16,
            ua.VariantType.Int32, ua.VariantType.UInt32,
            ua.VariantType.Int64, ua.VariantType.UInt64,
        }:
        # Permite vacío -> 0
        if raw == "":
            initial = 0
        else:
            try:
                initial = int(raw)
            except Exception:
                raise ValueError(f"Valor inicial no es int: {raw!r}")

    # float
    elif vtype == ua.VariantType.Float or ua.VariantType.Double:
        # Permite vacío -> 0.0 y coma decimal
        norm = raw.replace(",", ".")
        try:
            initial = float(norm) if norm != "" else 0.0
        except Exception:
            raise ValueError(f"Valor inicial no es float: {raw!r}")

    else:
        # No deberías llegar aquí con el TYPE_MAP actual
        raise ValueError(f"Datatype no manejado: {vtype}")

    # Mutar el dict de entrada con valores ya validados/casteados
    node_line["datatype"]= vtype
    node_line["initial"]= initial

    # Castear writable
    writable=str(node_line["writable"]).strip().lower()
    if writable in _TRUE:
        node_line["writable"] = True
    elif writable in _FALSE:
        node_line["writable"] = False
    else:
        raise ValueError(f"Valor de 'Writable' no es booleano: {writable!r}")

    return node_line

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

def setup_logging(level: str | None, file_path: str | None = None) -> None:
    """
    Configura el sistema de logging de la aplicación.

    Crea un logger básico con salida a consola (`stdout`) y,
    opcionalmente, a un archivo si se especifica `file_path`.
    Permite establecer el nivel de logging a través de texto
    (ej. "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").

    Parameters
    ----------
    level : str, default="INFO"
        Nivel de logging mínimo a mostrar. Se debe pasar como texto
        (por ejemplo, "DEBUG", "INFO", etc.). Si no coincide con un
        nivel válido, se usará `logging.INFO` por defecto.
    file_path : str or None, default=None
        Ruta a un archivo donde guardar los logs. Si es `None`,
        no se crea archivo de log y solo se envía a consola.

    Examples
    --------
    >>> setup_logging("DEBUG")
    >>> setup_logging("WARNING", "app.log")
    """

    if level:
        handlers = [logging.StreamHandler(sys.stdout)]
        if file_path:
            handlers.append(logging.FileHandler(file_path, encoding="utf-8"))
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            handlers=handlers,
    )