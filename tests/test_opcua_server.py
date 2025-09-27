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
    if srv.is_created:
        srv.stop()

def test_start_and_clean_stop(server: OpcServer):
    assert server._server is None
    assert server._idx is None
    assert not server.is_started

    # Arranque servidor (inclue creacion)
    assert server.start()

    assert server.is_started
    assert server._server is not None
    assert server._idx is not None
    assert server.is_started

    # idempotencia
    assert server.start()
    assert server.is_started

    # parada con perseverancia
    assert server.stop()

    assert server.is_created
    assert not server.is_started
    assert server._server is not None
    assert server._idx is not None

    # Rearranque
    assert server.start()
    assert server.is_started

    # parada limpia
    assert server.stop(clean=True)

    assert not server.is_created
    assert not server.is_started
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
