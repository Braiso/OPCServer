import pytest
from opc_project.opcua_server import OpcServer, OpcServerError

@pytest.fixture
def server():
    srv = OpcServer(
        endpoint_url="opc.tcp://localhost:4840/freeopcua/server/",
        namespace="urn:test",
        files_dir=".",
        nodes_input_file="nodes.csv",
        nodes_output_file="nodes.json"
    )
    yield srv
    # cleanup defensivo
    if srv.is_connected:
        srv.stop()

def test_start_and_stop(server):
    assert not server.is_connected
    assert server.start()
    assert server.is_connected
    assert server._server is not None
    assert server._idx is not None

    # idempotencia
    assert server.start()
    assert server.is_connected

    # parada limpia
    assert server.stop()
    assert not server.is_connected
    assert server._server is None
    assert server._idx is None

def test_start_with_invalid_endpoint():
    srv = OpcServer(
        endpoint_url="opc.tcp://:invalid",
        namespace="urn:test",
        files_dir=".",
        nodes_input_file="nodes.csv",
        nodes_output_file="nodes.json"
    )
    with pytest.raises(OpcServerError):
        srv.start(retries=1)
    assert srv._server is None
    assert srv._idx is None
