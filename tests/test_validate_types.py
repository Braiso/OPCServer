import pytest
from opc_project.opcua_server import validate_types  # ajusta el import a tu ruta real
from opcua import ua

def test_boolean_true():
    row = {
        "alias": "FlagOk",
        "nodeid": '""."X"."FlagOk"',
        "datatype": "boolean",   # ya normalizado
        "initial": "true",       # ya normalizado
        "folder": "X",
        "writable": "1",         # ya normalizado
    }
    out = validate_types(row)
    assert out["datatype"] == ua.VariantType.Boolean
    assert out["initial"] is True
    assert out["writable"] is True

def test_boolean_false_variants():
    row = {
        "alias": "FlagOff",
        "nodeid": '""."X"."FlagOff"',
        "datatype": "boolean",
        "initial": "0",          # variantes aceptadas: "0", "false", ""
        "folder": "X",
        "writable": "no",
    }
    out = validate_types(row)
    assert out["datatype"] == ua.VariantType.Boolean
    assert out["initial"] is False
    assert out["writable"] is False

def test_string_basic():
    row = {
        "alias": "Etiqueta",
        "nodeid": '""."X"."Etiqueta"',
        "datatype": "string",
        "initial": "Linea1",
        "folder": "X",
        "writable": "",          # se interpreta como False
    }
    out = validate_types(row)
    assert out["datatype"] == ua.VariantType.String
    assert out["initial"] == "Linea1"
    assert out["writable"] is False

def test_int32_ok_and_default_zero():
    # Caso con valor explícito
    row1 = {
        "alias": "Contador",
        "nodeid": '""."X"."Contador"',
        "datatype": "int32",
        "initial": "42",
        "folder": "X",
        "writable": "yes",
    }
    out1 = validate_types(row1)
    assert out1["datatype"] == ua.VariantType.Int32
    assert out1["initial"] == 42
    assert out1["writable"] is True

    # Caso con inicial vacío -> 0
    row2 = {
        "alias": "Contador2",
        "nodeid": '""."X"."Contador2"',
        "datatype": "int32",
        "initial": "",
        "folder": "X",
        "writable": "0",
    }
    out2 = validate_types(row2)
    assert out2["datatype"] == ua.VariantType.Int32
    assert out2["initial"] == 0
    assert out2["writable"] is False

def test_double_ok_coma_decimal_and_default_zero():
    # coma decimal aceptada
    row1 = {
        "alias": "Temperatura",
        "nodeid": '""."X"."Temperatura"',
        "datatype": "double",
        "initial": "20,5",
        "folder": "X",
        "writable": "si",
    }
    out1 = validate_types(row1)
    assert out1["datatype"] == ua.VariantType.Double
    assert out1["initial"] == pytest.approx(20.5)
    assert out1["writable"] is True

    # vacío -> 0.0
    row2 = {
        "alias": "Setpoint",
        "nodeid": '""."X"."Setpoint"',
        "datatype": "double",
        "initial": "",
        "folder": "X",
        "writable": "false",
    }
    out2 = validate_types(row2)
    assert out2["datatype"] == ua.VariantType.Double
    assert out2["initial"] == pytest.approx(0.0)
    assert out2["writable"] is False
