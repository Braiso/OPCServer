import logging,json,random,argparse,time,sys,os
from typing import Any
from opcua import Client
from types import TracebackType
from typing import Self
from pathlib import Path
from opcua.ua.uaerrors import UaError

logger = logging.getLogger(__name__)
__version__ = "0.1.0"

class OpcClientError(RuntimeError):
    """
    Excepción base para todos los errores relacionados con OpcClient.

    Hereda de RuntimeError, pero define un tipo específico para el dominio OPC.
    Esto permite distinguir fácilmente, en bloques try/except, entre errores
    de la librería estándar y los que provienen del cliente OPC.

    Ejemplo
    -------
    try:
        cli.read_node("ns=2;i=3")
    except OpcClientError as e:
        print("Fallo en cliente OPC:", e)
    """
    pass


class ConnectionError(OpcClientError):
    """
    Error al establecer o mantener una conexión OPC UA.

    Parameters
    ----------
    endpoint : str
        URL del servidor al que se intentaba conectar.
    message : str
        Mensaje descriptivo del fallo.
    original : Exception, optional
        Excepción original capturada (si existe), útil para trazas.

    Uso
    ---
    >>> raise ConnectionError("opc.tcp://localhost:4840", "Timeout de conexión")
    """
    def __init__(self, endpoint: str, message: str, original: Exception | None = None):
        super().__init__(f"{message} (endpoint={endpoint})")
        self.endpoint = endpoint
        self.original = original


class NodeReadError(OpcClientError):
    """
    Error al leer un nodo OPC UA.

    Parameters
    ----------
    nodeid : str
        Identificador del nodo que causó el error.
    message : str
        Mensaje descriptivo del fallo.        
    original : Exception, optional
        Excepción original capturada (si existe).

    Uso
    ---
    >>> raise NodeReadError("ns=2;i=3")
    """
    def __init__(self, nodeid: str, message: str, original: Exception | None = None):
        super().__init__(f"{message}:{nodeid}")
        self.nodeid = nodeid
        self.original = original

class NodeWriteError(OpcClientError):
    """
    Error al escribir en un nodo OPC UA.

    Parameters
    ----------
    nodeid : str
        Identificador del nodo que causó el error.
    message : str
        Mensaje descriptivo del fallo.
    original : Exception, optional
        Excepción original capturada (si existe).
    """
    def __init__(self, nodeid: str, message: str, original: Exception | None = None):
        super().__init__(f"{message}:{nodeid}")
        self.nodeid = nodeid
        self.original = original

'''
¿Por qué ConnectionError y NodeReadError no heredan directamente de 'RuntimeError'?

-Separación semántica: si todo hereda de RuntimeError, en un except RuntimeError atraparías errores de tu cliente OPC y de cualquier otra librería estándar de Python. Con una jerarquía propia (OpcClientError), puedes capturar de forma específica solo los tuyos.

-Jerarquía extensible: al definir OpcClientError como base, puedes añadir fácilmente más subclases (NodeWriteError, SubscriptionError, etc.) sin romper el código que ya captura OpcClientError.

-Información de contexto: al añadir atributos (endpoint, nodeid, original) enriqueces la excepción con datos del dominio, cosa que no tienes con RuntimeError.

Mejor depuración: los logs y trazas muestran claramente que es un error del cliente OPC y no un error genérico de ejecución.
'''


class OpcClient:

    """
    Cliente OPC UA sencillo.

    Esta clase encapsula las operaciones básicas de un cliente OPC UA:
    conexión, desconexión y gestión del estado de la sesión.
    """

    def __init__(self, endpoint_url: str):
        """
        Inicializa una nueva instancia de OpcClient.

        Parameters
        ----------
        endpoint_url : str
            URL del servidor OPC UA al que se intentará conectar,
            en formato opc.tcp (por ejemplo: "opc.tcp://127.0.0.1:4840").

        Attributes
        ----------
        endpoint_url : str
            URL de conexión fija del cliente (no debe cambiar tras la construcción).
        client : Client or None
            Instancia de `opcua.Client` activa si existe conexión,
            o `None` si el cliente está desconectado.
        aliases : dict[str, str]
            Alias de nodos conocidos.
        nodes: dict[str,Any]
            Nodos conocidos resueltos.        
        """

        # Configuracion fija
        self.endpoint_url: str = endpoint_url
        # Estado
        self.client: Client | None = None
        self._aliases: dict[str,str] = {}
        self.nodes: dict[str,Any] = {}

    @property
    def is_connected(self) -> bool:
        '''Indica si hay una conexion OPC UA activa'''
        return self.client is not None

    @property
    def aliases(self) -> dict:
        '''Devuelve los alias cargados de nodos conocidos'''
        return self._aliases

    def __enter__(self) -> Self:
        """
        Método especial del protocolo de context manager.

        Se ejecuta automáticamente al entrar en un bloque `with`.
        Intenta establecer la conexión con el servidor OPC UA.
        Si la conexión falla, lanza una excepción `OpcClientError`.

        Returns
        -------
        self : OpcClient
            Devuelve la propia instancia del cliente, que se asigna
            a la variable usada en la cláusula `as` del bloque `with`.
        """
        self.connect()
        return self

    def __exit__(self, exc_type:type[BaseException] | None, exc:BaseException | None, tb:TracebackType | None) -> None:
        """
        Método especial del protocolo de context manager.

        Se ejecuta automáticamente al salir de un bloque `with`,
        ya sea de forma normal o por una excepción. 
        En este caso, libera el recurso cerrando la conexión.

        Parameters
        ----------
        exc_type : type or None
            El tipo de la excepción ocurrida dentro del bloque `with`,
            o `None` si no hubo excepción.
        exc : Exception or None
            La instancia de la excepción ocurrida, o `None` si no hubo.
        tb : traceback or None
            El objeto traceback asociado a la excepción, o `None` si no hubo.
        """        

        self.disconnect()

    def connect(self, retries: int = 3, backoff_s: float = 1.0) -> bool:
        """
        Establece la conexión con el servidor OPC UA.

        Returns
        -------
        bool
            True si la conexión se estableció o ya estaba activa.

        Raises
        ------
        ConnectionError
            Si no se puede establecer la conexión con el endpoint
            especificado en `self.endpoint_url`.
        """
        if self.is_connected:
            logger.info('Conexion ya establecida a %s',self.endpoint_url)
            return True
        
        last_exc: Exception | None = None
        for attempt in range(1,retries+1):
            try:
                tmp = Client(self.endpoint_url)
                tmp.connect()
                self.client = tmp
                logger.info("Conexion existosa a %s", self.endpoint_url)
                return True
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    logger.warning("Intento %d/%d falló: %s", attempt, retries, exc)
                    time.sleep(backoff_s * attempt)
                else:
                    # Asegura estado consistente
                    logger.exception('Error al conectar a %s: %s', self.endpoint_url,exc)
                    self.client = None
        raise ConnectionError(self.endpoint_url, "Se han agotado los intentos de conexión.", original=last_exc)

    def disconnect(self) -> None:
        """
        Cierra la conexión con el servidor OPC UA.

        Si existe un cliente activo, lo desconecta y lo establece en None.
        """
        if not self.is_connected:
            logger.info("Desconexión solicitada sin conexión activa.")
            return
        try:
            uac = getattr(self.client, "uaclient", None)
            if uac and hasattr(uac, "disconnect_socket"):
                self.client.disconnect()
                logger.info("Cliente desconectado de %s", self.endpoint_url)
            else:
                logger.warning("Cliente sin socket inicializado; nada que desconectar.")
        except Exception as exc:
            logger.exception("Error al desconectar: %s", exc)
        finally:
            self.client = None

    def read_node(self, nodeid: str) -> Any:
        """
        Lee el valor actual de un nodo.

        Parameters
        ----------
        nodeid : str
            Identificador del nodo en formato OPC UA (p. ej. "ns=2;i=3").

        Returns
        -------
        Any
            Valor leı́do del nodo.

        Raises
        ------
        NodeReadError
            Si ocurre un fallo al acceder o leer el nodo.
        """
        if not self.is_connected: raise OpcClientError("Cliente no conectado")
        t0 = time.perf_counter()
        try:
            val = self.client.get_node(nodeid).get_value()
            logger.debug("Leído %s => %r (%.2f ms)", nodeid, val, (time.perf_counter()-t0)*1000)
            return val
        except Exception as exc:
            raise NodeReadError(nodeid,"Error de accesos a nodo",original=exc) from exc    

    def write_node(self, nodeid: str, value: Any) -> None:
        """
        Escribe un valor en un nodo OPC UA.

        Parameters
        ----------
        nodeid : str
            Identificador del nodo en formato OPC UA (p. ej. "ns=2;i=3").
        value : Any
            Valor a escribir. Debe ser compatible con el tipo del nodo.

        Raises
        ------
        NodeWriteError
            Si ocurre un fallo al escribir en el nodo. Puede deberse a:
            - Error de la librería OPC UA (capturado como `UaError`).
            - Error de transporte o sistema (timeout, desconexión, etc.).
            El detalle original estará en `e.original`.
        """
        if not self.is_connected:
            raise OpcClientError("Cliente no conectado")
        try:
            node = self.client.get_node(nodeid)
            node.set_value(value)
            logger.debug("Escrito %s <= %r", nodeid, value)
        except UaError as exc:
            raise NodeWriteError(nodeid, f"Error UA al escribir", original=exc) from exc
        except Exception as exc:
            # Otros fallos (transporte, timeout, etc.)
            raise NodeWriteError(nodeid, "Error de transporte al escribir", original=exc) from exc

    def load_aliases_from_json(self,file_path: str) -> None:
        """
        Carga los browsename y nodeid conocidos desde un JSON exportado
        directamente del servidor.

        Parameters
        ----------
        file_path : str
            Ruta al archivo JSON.

        Raises
        ------
        OpcClientError
            Si el archivo no existe, no puede abrirse, o el contenido es inválido.
        """
        try:
            logger.info("Inicio de carga de alias desde %s", file_path)
            with open(Path(file_path), "r", encoding="utf-8") as archivo:
                self._aliases = json.load(archivo)
            logger.info("Cargados %d alias desde %s", len(self._aliases), file_path)

        except FileNotFoundError as exc:
            self._aliases = {}
            raise OpcClientError(f"No se encuentra el JSON de alias en {file_path}") from exc

        except json.JSONDecodeError as exc:
            self._aliases = {}
            raise OpcClientError(f"El archivo {file_path} no contiene JSON válido") from exc

        except Exception as exc:
            self._aliases = {}
            raise OpcClientError(f"Error inesperado al leer {file_path}") from exc

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

if __name__ == "__main__":

    # ----------------------------
    # Parámetros de conexión
    # ----------------------------
    ip = "localhost"
    port = 4841
    endpoint = f"opc.tcp://{ip}:{port}"

    '''
    Prueba sin with
    cli = OpcClient(endpoint)
    cli.connect()
    '''

    file_dir= Path (__file__).resolve()
    log_path = Path(file_dir.parent) / "client.log"

    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=endpoint)
    parser.add_argument("--log",default=log_path)
    parser.add_argument("--level",default="INFO")
    args = parser.parse_args()

    setup_logging(args.level, args.log)
    logger.info("Arrancando OpcClient v%s", __version__)

    print("Me conecto")
    with OpcClient(args.url) as cli:
            print("\nLeo")

            # Carga de alias conocidos
            cli.load_aliases_from_json (Path(file_dir.parent)/"nodes.json")
            nodes=cli.aliases

            # Leer nodos
            for signal,nodeid in nodes.items():
                print(f"Señal: {signal}\t\tValor: {cli.read_node(nodeid)}")

            print("\nEscribo")

            # Escribir nodo
            signal="Espesor_Medido"
            espesores = [3.5,4.2,5,7]

            cli.write_node(nodes[signal], random.choice(espesores))
            print(f"Señal: {signal}\t\tValor: {cli.read_node(nodes[signal])}")
