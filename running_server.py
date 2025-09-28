from pathlib import Path
from opc_project.opcua_lib import setup_logging
from opc_project.opcua_server import  OpcServer,__version__,logger
import time,argparse
    
# Parametros por defecto de constructor
endpoint_url="opc.tcp://127.0.0.1:4841"
namespace = "CAFERSA"
files_dir = (Path(__file__).resolve().parent).as_posix()+"/opc_project/files/"
nodes_input_file = "nodes.csv"
nodes_output_file = "nodes.json" 

# Parametros por defecto logging
log_path = Path (__file__).resolve().parent / "opc_project/logs/server.log"
level = "INFO"

# Argumentos CLI - Constructor
parser = argparse.ArgumentParser()
parser.add_argument("--url",default=endpoint_url)
parser.add_argument("--namespace",default=namespace)
parser.add_argument("--files",default=files_dir)
parser.add_argument("--nodes_in",default=nodes_input_file)
parser.add_argument("--nodes_out",default=nodes_output_file)

# Argumentos CLI - Logging
parser.add_argument("--log",default=log_path)
parser.add_argument("--level",default=level)
args = parser.parse_args()

# Configuracion de logging
setup_logging(args.level, args.log)
logger.info("Arrancando OpcServer v%s en %s", __version__, args.url)

server = OpcServer(
    endpoint_url=args.url,
    namespace=args.namespace,
    files_dir=args.files,
    nodes_input_file=args.nodes_in,
    nodes_output_file=args.nodes_out
    )

server.create()
server.load_nodes_from_csv()
server.resolve_nodes()
server.export_nodes_to_json()

try:
    print('Servidor escuchando')
    while True:        
        time.sleep(1)
except KeyboardInterrupt:
    print('Servidor desconectado')
server.stop(clean=True)