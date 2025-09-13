import json
import tempfile
from pathlib import Path
from opc_project.opcua_client import OpcClient

def test_load_aliases_from_json_ok():
    # Crear un archivo JSON temporal valido
    data = {
        "MotorStart":"ns=2;i=3",
        "MotorStart":"ns=2;i=4",
    }
    with tempfile.NamedTemporaryFile("w+",delete=False,suffix=".json") as tmp:
        json.dump(data,tmp)
        tmp_path = Path(tmp.name)
    try:
        cli = OpcClient("opc.tcp://localhost:4841")
        cli.load_aliases_from_json(str(tmp_path))
        assert cli.aliases == data
    finally:
        tmp_path.unlink()