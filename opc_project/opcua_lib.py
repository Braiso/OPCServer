import logging,sys
from opcua import ua

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