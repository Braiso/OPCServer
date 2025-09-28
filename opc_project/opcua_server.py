from opcua import Server, ua, Node
from typing import Any
from .opcua_lib import validate_types,build_node_dict,OpcServerError
import time,json,logging
import csv
from pathlib import Path
from opcua.ua.uaerrors import UaError

'''
Funcionalidades por implementar:
- Context Manager
- Rango de valores en validate_types
'''

logger = logging.getLogger(__name__)
__version__ = "0.1.0"

class OpcServer:

    '''
    Servidor OPC UA sencillo.

    Esta clase encapsula las operaciones básicas de un servidor OPC UA:
    conexón, desconexión y gestión de los nodos.

    '''

    def __init__(self,endpoint_url : str,namespace : str,
                 files_dir : str, nodes_input_file: str, nodes_output_file: str) -> None:
        '''
        Inicializa un una instancia de OpcServer.

        Parameters
        ----------
        endpoint_url : str
            URL del servidor OPC UA.
        namespace: str
            Espacio de nombres.
        files_dir: str
            Directorio de los archivos de configuracion.
        nodes_input: str
            Archivo CSV donde se guarda informacion para la creacion de los nodos.
        nodes_output: str
            Archivo JSON con la información para la instanciación de los nodos por parte de los clientes.

        Attributes
        ----------
        endpoint_url : str
        namespace: str
        files_dir: str
        nodes_input: str
        nodes_output: str
        server = Server or None
            Instancia del servidor.
        nodes =  dict[str,Any] or None
            Nodos creados. Fuente: Archivo CSV    
        self._idx : int
            Indice del espacio de nombre definido en el constructor
        '''

        self._endpoint_url: str = endpoint_url
        self._namespace : str = namespace
        self._files_dir : str = files_dir
        self._nodes_input : str = nodes_input_file
        self._nodes_output : str = nodes_output_file
        self._server: Server | None = None
        self._nodes : dict[str,Any] | None = None
        self._resolved_nodes : list | None = None
        self._idx : int | None = None
        self._started: bool | None = None
        self._check_general_invariants
        
    def create(self) -> None:
        '''
        Crea el servidor y registra el namespace
        '''
        self._check_general_invariants

        # Idempotencia
        if self.is_created:
            logger.info(f"Servidor ya creado en {self._endpoint_url}")

            # Comprobar si tambien tien el espacio de nombre registrado
            if not self.idx_is_registered:
                self._register_index()
            return
    
        try:
            server = Server()
            server.set_endpoint(self._endpoint_url)

            self._server = server
            self._register_index()  
        except Exception as exc:
            # Limpieza del estado interno solo si algo se rompió antes de quedar listo
            self._server = None
            self._idx = None
            logger.exception("Fallo creando el servidor en %s", self._endpoint_url)
            raise OpcServerError(self._endpoint_url, "Fallo en la creación del servidor") from exc

        logger.info(f"Servidor creado en {self._endpoint_url}")
        self._check_general_invariants

    def start(self, retries: int = 3, backoff_s:float = 1.0) -> bool:
        '''
        Arranca el servidor.

        Parameters
        ----------
        retries
            Numero de reintentos en caso de error de inicio
        backoff_s
            Tiempo de espera entre reintentos
        
        Returns
        -------
        bool
            True si la conexión se estableció o ya estaba activa.

        Raises
        ------
        OpcServerError
            Si no se puede arrancar el servidor con el endpoint
            especificado en `self.endpoint_url`.        
        '''

        # Validación rápida de args
        if retries < 1:
            raise ValueError("retries debe ser >= 1") 
        if backoff_s <= 0:
            raise ValueError("backoff_s debe ser > 0")

        self._check_general_invariants() 

        # Asegurar servidor creado (y namespace registrado) sin arrancar
        if not self.is_created:
            self.create()
        elif not self.idx_is_registered:
            self._register_index()

        # Idempotencia
        if self.is_started:
            logger.info(f"Servidor ya arrancado en {self._endpoint_url}")
            return True

        # Arrancar servidor
        last_exc : Exception | None = None
        for attempt in range(1,retries+1):
            try:
                self._check_general_invariants()              

                assert self._server is not None
                self._server.start()
                self._started=True

                logger.info(f"Arranque servidor en {self._endpoint_url} exitoso")
                self._check_general_invariants()
                return True
            
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    logger.warning("Intento %d/%d falló: %s", attempt, retries, exc)
                    time.sleep(backoff_s * attempt)
                else:
                    logger.error("Error al arrancar a %s tras %d intentos", self._endpoint_url, retries)
                    
                    # Asegura estado consistente
                    if self._server is not None:
                        try:
                            self.stop(True)
                        except Exception:
                            pass
                    self._started = False

        self._check_general_invariants()
        raise OpcServerError(self._endpoint_url,"Se han agotado los intentos de arranque.",original=last_exc) from last_exc

    def stop(self, clean:bool=False) -> bool:
        '''
        Detiene el servidor si está en ejecución.

        Returns
        -------
        bool
            True si se detuvo el servidor, False si no estaba en ejecución.
        '''
        if self._server is None:
            return False  # nada que detener

        try:
            self._server.stop()
            logger.info("Servidor detenido en %s", self._endpoint_url)
        except Exception as exc:
            logger.warning("Error al detener servidor: %s", exc, exc_info=True)
        finally:
            self._started = False

            if clean:
                self._server: Server | None = None
                self._idx : int | None = None
                self._nodes : dict[str,Any] | None = None

        self._check_general_invariants()
        return True

    def load_nodes_from_csv(self,
                            *,
                            delimiter: str = ',',
                            encoding: str = 'utf-8',
                            required_fields: tuple[str,...] = ("alias","nodeid","datatype","initial","folder","writable")
                            ) -> dict:
        """
        Carga y crea los nodos a partir de un archivo CSV.

        Parameters
        ----------
        delimiter : str
            Separador de campos (por defecto ',').
        encoding : str
            Codificación del archivo (por defecto 'utf-8').
        required_fields : tuple[str, ...]
            Columnas mínimas obligatorias en el CSV.

        Returns
        -------
        dict
            Resumen con métricas de carga:
            {
            "total_rows": int,
            "loaded": int,
            "skipped": int,
            "duplicates": int,
            "errors": int,
            }

        Raises
        ------
        OpcServerError
            Si hay errores de E/S (archivo inexistente, permisos, etc.)
            o si la cabecera no contiene los campos obligatorios.
        """

        # Ruta de importacion
        path_csv= Path(self._files_dir + self._nodes_input)

        # Carga de archivo
        try: 
            f = path_csv.open("r", newline="", encoding=encoding)
            logger.info(f"Archivo CSV cargado correctamente: {path_csv}")
        except FileNotFoundError as exc:
            raise OpcServerError(self._endpoint_url,f"El archivo no existe: {path_csv}",original=exc) from exc
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,f"Error inesperado en la carga fichero CSV: {path_csv}",original=exc) from exc

        with f:
            reader = csv.DictReader(f,delimiter=delimiter)
            header = reader.fieldnames

            # Validación de cabecera
            if not header:
                raise OpcServerError(self._endpoint_url, f"CSV sin cabecera: {path_csv}")

            faltan = [c for c in required_fields if c not in header]
            if faltan:
                raise OpcServerError(
                    self._endpoint_url,
                    f"Faltan columnas obligatorias {faltan} en {path_csv}. Cabecera: {header}",
                )

            # Estructuras de estado
            stats = {"total_rows": 0, "loaded": 0, "skipped": 0, "duplicates": 0, "errors": 0}
            nodes: dict[str, dict] = {} if self._nodes is None else dict(self._nodes)  # copia defensiva

            # Procesando fila a fila
            for row in reader:
                stats["total_rows"] +=1
                line = reader.line_num  # línea real del archivo (útil para logs)

                # Normalización básica: strip en strings
                norm_row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

                # Comprobar requeridos no vacíos
                if any(not norm_row.get(c) for c in required_fields):
                    logger.warning("Fila %d: campos requeridos vacíos (%s). Se omite.", line, required_fields)
                    stats["skipped"] += 1
                    continue

                alias = norm_row["alias"]

                # Duplicados por nombre (ajusta la clave si usas otra)
                if alias in nodes:
                    logger.warning("Fila %d: nombre duplicado '%s'. Se omite.", line, alias)
                    stats["duplicates"] += 1
                    continue

                # Construcción del dict del nodo
                try:
                    node_def = validate_types(norm_row)
                    
                except ValueError as exc:
                    # Errores de contenido/parseo
                    logger.warning("Fila %d: datos inválidos (%s). Se omite.", line, exc) 
                    stats["errors"] += 1
                    continue
                except Exception as exc:
                    logger.warning("Fila %d: error inesperado al procesar fila: %s", line, exc, exc_info=True)
                    stats["errors"] += 1
                    continue

                # Guardar en estructura local
                nodes[alias] = node_def
                stats["loaded"] += 1


            logger.info(
                "CSV cargado: %s | total=%d, loaded=%d, skipped=%d, duplicates=%d, errors=%d",
                path_csv, stats["total_rows"], stats["loaded"], stats["skipped"], stats["duplicates"], stats["errors"]
            )

        # Commit de los nodos cargados en el estado del servidor
        prev_nodes = self._nodes
        self._nodes = nodes

        # Comprobar invariantes
        try:
            self._check_nodes_invariants()  
        except AssertionError as exc:
            # Revierte estado si no cumple
            self._nodes = prev_nodes
            raise OpcServerError(self._endpoint_url, "Invariantes de nodos incumplidas", original=exc) from exc
        
        return stats
    
    def resolve_nodes(self):
        '''
        Añade nodos a partir de los alias cargados
        '''

        self._check_general_invariants()
        
        if not self.is_created:
            self.create()

        if not self.alias_is_loaded:
            self.load_nodes_from_csv()

        # Edicion en frio
        if self.is_started:
            self.stop()
        
        # Obtener estructura de nodos e indice                
        assert self._server is not None
        root = self._server.get_objects_node()
        assert self._idx is not None
        idx = self._idx

        # En cada resolucion se borra lo anterior
        try:
            root = root.get_child([f"{idx}:root"])
            self._server.delete_nodes([root], recursive=True)
            logger.info("Eliminada carpeta raiz existente")
        except Exception:
            pass  # no existía

        # Y se crea una carpeta raiz limpia
        nodes = root.add_folder(idx, 'root')
        self._resolved_nodes = []

        # Estructuras de estado
        stats = {"total_rows": 0, "resolved": 0, "duplicates": 0, "errors": 0}
        
        # Recorrer alias
        assert self._nodes is not None
        for node in self._nodes.values():
            stats["total_rows"] +=1

            # Los nodos estan organizados desde en carpetas en el CSV
            try:
                folder = nodes.get_child([f"{idx}:{node["folder"]}"])
            except Exception:
                # no existe → crear
                folder = nodes.add_folder(idx, node["folder"])
                logger.info("Carpeta %s creada.",node["folder"])
            try:
                var = folder.add_variable(
                    ua.NodeId(node["nodeid"], idx),
                    node["alias"], node["initial"],
                    varianttype=node["datatype"])
        
                if node["writable"]:
                    var.set_writable()

                logger.info("Nodo %s añadido en la carpeta %s.",node["alias"],node["folder"])
                self._resolved_nodes.append(var)
                stats["resolved"] +=1
            except UaError as exc: 

                code = getattr(exc, "code", None) or getattr(exc, "status", None)

                if code == ua.StatusCodes.BadNodeIdExists:
                    logger.warning("Nodo existente: %s ", node["alias"])
                    stats["duplicates"] += 1
                    continue

                logger.exception("Nodo %s: error UA al añadir variable (status=%s)", node["alias"], code)
                stats["errors"] += 1
                continue
        
            except Exception:
                logger.exception("Nodo %s: error inesperado al añadir variable", node["alias"])
                stats["errors"] += 1
                continue

        # Arrancar el servidor automaticamente
        if not self.is_started:
            self.start()

        logger.info(
            "Resolucion finalizada | total=%d, resolved=%d, duplicates=%d, errors=%d",
            stats["total_rows"], stats["resolved"], stats["duplicates"], stats["errors"]
            )

        # Comprobar invariantes
        try:
            self._check_general_invariants()
            self._check_nodes_resolved(stats=stats,root=nodes)
        except AssertionError as exc:
            # Borrar estado
            self._resolved_nodes = []
            self._server.delete_nodes([root], recursive=True)
            raise OpcServerError(self._endpoint_url, "Invariantes de resolucion incumplidas", original=exc) from exc

        return stats

    def write_node(self,nodeid:str,value:Any) -> None: 
        '''
        Escribe un nodo
        
        Parameters
        ----------
        nodeid: str
            nodeid del nodo 

        Raises
        ------
        OpcServerError:
            Error en la obtencion del nodo

        OpcServerError:
            Error en la escritura del nodo
        '''

        assert self._resolved_nodes is not None
        assert self._server is not None
        assert self._idx is not None

        try:
            node = self._server.get_node(ua.NodeId(nodeid, self._idx, ua.NodeIdType.String))
            assert node in self._resolved_nodes
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,"Error en la obtencion del nodo en la escritura", original=exc) from exc

        try:
            node.set_value(value)
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,"Error en la escritura del nodo", original=exc) from exc
        
        logging.info(f'Escritura realizada en variable \'{nodeid}\' con valor \'{node.get_value()}\'')
        return

    def read_node(self,nodeid:str) -> None: 
        '''
        Lee un nodo
        
        Parameters
        ----------
        nodeid: str
            nodeid del nodo 

        Raises
        ------
        OpcServerError:
            Error en la obtencion del nodo

        OpcServerError:
            Error en la lectura del nodo
        '''

        assert self._resolved_nodes is not None
        assert self._server is not None
        assert self._idx is not None
        
        try:
            node = self._server.get_node(ua.NodeId(nodeid, self._idx, ua.NodeIdType.String))
            assert node in self._resolved_nodes
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,"Error en la obtencion del nodo en la lectura", original=exc) from exc

        try:
            value=node.get_value()
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,"Error en la lectura del nodo", original=exc) from exc
        
        logging.info(f'Lectura realizada en variable \'{nodeid}\' con valor \'{value}\'')
        return

    def export_nodes_to_json(self)->None:
        '''
        Exporta en un JSON la información de los nodos para los clientes.
        '''

        if not self.nodes_resolved:
            logging.exception("No existen nodos resueltos para exportar")
            return

        nodes_dict={}

        # Actualizar el archivo de nodos por si varia el index
        assert self._server is not None
        root = self._server.get_root_node() # Cargar nodos añadidos
        children = root.get_child(["0:Objects"])
        build_node_dict(children, nodes_dict,self._idx)

        # Escribir el archivo
        try:
            with open(self._files_dir + self._nodes_output,"w",encoding="utf-8") as f:
                json.dump(nodes_dict, f, ensure_ascii=False, indent=4)
        except Exception as exc:
            raise OpcServerError(self._endpoint_url,"Error en la exportacion de nodos a JSON", original=exc) from exc 
        return

    def _register_index(self)->None:
        '''
        Registra el namespace y guarda el indice
        '''

        if self._server is None:
            raise OpcServerError(self._endpoint_url, "Servidor no inicializado. Debe arrancar el servidor antes de registrar el namespace.")
        try:
            idx = self._server.register_namespace(self._namespace)
        except Exception as exc:
            raise OpcServerError(self._endpoint_url, f"Error al registrar namespace: {self._namespace}", original=exc) from exc
        self._idx = idx
        self._check_general_invariants()
        logger.info(f"Espacio de nombres {self._namespace} registrado en {self._endpoint_url} con indice: {self._idx}")

    def _check_general_invariants(self) -> None:
        # Ciclo de vida coherente
        if self._server is None:
            assert self._idx is None, "idx debe ser None si el servidor no está creado"
        else:
            assert self._idx is not None, "idx no puede ser None si el servidor está creado"

        # Flag de arranque
        if self._started:
            assert self._server is not None,"server debe ser true si el el servidor esta arrancado"
            assert self._idx is not None,"idx debe ser true si el el servidor esta arrancado"

        # Endpoint y namespace
        assert isinstance(self._endpoint_url, str) and self._endpoint_url.startswith("opc.tcp://"), \
            "endpoint_url inválido"
        assert isinstance(self._namespace, str) and self._namespace, "namespace vacío"

    def _check_nodes_invariants(self) -> None:
        from opcua import ua

        nodes = self._nodes
        assert isinstance(nodes, dict), "self._nodes debe ser dict"

        # Unicidad de alias (por si llega algo raro)
        assert len(nodes) == len(set(nodes.keys())), "Alias duplicados en self._nodes"

        for alias, nd in nodes.items():
            assert isinstance(alias, str) and alias, f"alias inválido: {alias!r}"
            assert isinstance(nd, dict), f"node_def debe ser dict en {alias}"

            # Campos mínimos
            for k in ("nodeid", "datatype", "initial"):
                assert k in nd, f"Falta '{k}' en nodo {alias}"

            # Tipo correcto
            dt = nd["datatype"]
            assert dt in ua.VariantType, f"datatype inválido en {alias}: {dt!r}"

            # initial no None
            assert nd["initial"] is not None, f"initial None en {alias}"

            # writable booleano (si existe)
            if "writable" in nd:
                assert isinstance(nd["writable"], bool), f"writable no bool en {alias}"

    def _check_nodes_resolved(self,stats:dict, root: Node) -> None:
        assert stats["total_rows"] == stats["resolved"] + stats["duplicates"] + stats["errors"]
        assert self._resolved_nodes is not None
        assert len(self._resolved_nodes) == stats["resolved"]
        # pertenencia y namespace
        for n in self._resolved_nodes:
            assert n.nodeid.NamespaceIndex == self._idx
            assert root in n.get_path()  # o comprueba padre recursivo

    @property
    def is_created(self) -> bool:
        '''Indica si el servidor esta creado'''
        return self._server is not None

    @property
    def is_started(self) -> bool:
        '''Indica si hay un servidor OPC UA arrancado'''
        return self._started is not None and self._started 

    @property
    def alias_is_loaded(self) -> bool:
        '''Indica si se han cargado los alias'''
        return self._nodes is not None
    
    @property
    def idx_is_registered(self) -> bool:
        '''Indica si se ha registado el espacio de nombres'''
        return self._idx is not None

    @property
    def nodes_resolved(self) -> bool:
        '''Indica si el servidor tiene nodos resueltos'''
        return bool(self._resolved_nodes)
    
if __name__=="__main__":
  pass