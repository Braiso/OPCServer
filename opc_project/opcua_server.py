from opcua import Server
from pathlib import Path
from typing import Any
from .opcua_lib import setup_logging,build_node_dict
import time,json,logging,argparse

logger = logging.getLogger(__name__)
__version__ = "0.1.0"

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
        '''

        self._endpoint_url: str = endpoint_url
        self._namespace : str = namespace
        self._files_dir : str = files_dir
        self._nodes_input : str = nodes_input_file
        self._nodes_output : str = nodes_output_file
        self._server: Server | None = None
        self._nodes : dict[str,Any] | None = None
        self._idx: int | None = None

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
        # Comprobar si el servidor esta arrancado
        if self.is_connected:
            logger.info(f"Servidor ya arrancado en {self._endpoint_url}")
            return True

        # Arrancar servidor
        last_exc : Exception | None = None
        for attempt in range(1,retries+1):
            try:
                self._check_invariants()
                tmp = Server()
                tmp.set_endpoint(self._endpoint_url)                 
                idx = tmp.register_namespace(self._namespace)   

                tmp.start()
                self._server = tmp
                self._idx = idx

                logger.info(f"Arranque servidor en {self._endpoint_url} exitoso")
                self._check_invariants()
                return True
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    logger.warning("Intento %d/%d falló: %s", attempt, retries, exc)
                    time.sleep(backoff_s * attempt)
                else:
                    logger.error("Error al arrancar a %s tras %d intentos", self._endpoint_url, retries)
                    # Asegura estado consistente
                    if tmp is not None:
                        try:
                            tmp.stop()
                        except Exception:
                            pass
                    self._server = None                    
                    self._idx = None
        self._check_invariants()
        raise OpcServerError(self._endpoint_url,"Se han agotado los intentos de arranque.",original=last_exc)

    def stop(self) -> bool:
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
            # asegurar estado consistente
            self._server = None
            self._idx = None
        self._check_invariants()
        return True

    def load_nodes_from_csv(self):
        '''
        Carga y crea los nodos a partir de un archivo CSV.
        '''
        pass

    def export_nodes_to_json(self):
        '''
        Guarda en un JSON la información de los nodos para los clientes.
        '''
        pass
    
    def _check_invariants(self) -> None:
        # Ciclo de vida coherente
        if self._server is None:
            assert self._idx is None, "idx debe ser None si el servidor no está arrancado"
        else:
            assert self._idx is not None, "idx no puede ser None si el servidor está arrancado"

        # Endpoint y namespace
        assert isinstance(self._endpoint_url, str) and self._endpoint_url.startswith("opc.tcp://"), \
            "endpoint_url inválido"
        assert isinstance(self._namespace, str) and self._namespace, "namespace vacío"

    @property
    def is_connected(self) -> bool:
        '''Indica si hay un servidor OPC UA activo'''
        return self._server is not None


if __name__=="__main__":
  pass