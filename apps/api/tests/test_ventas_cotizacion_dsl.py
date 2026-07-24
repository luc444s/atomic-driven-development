# ruff: noqa: S101
from plugins.ventas.cotizacion.backend.services.cotizacion import _extract_tokens


def test_extract_tokens_without_quotes():
    result = _extract_tokens("cotizar cliente Bohdan 200 Bombona1 mañana 8:00")
    assert result["cliente_raw"] == "Bohdan"
    assert result["items_raw"] == [{"cantidad": 200, "producto": "Bombona1"}]
    assert result["fecha_raw"] == "mañana"
    assert result["hora_raw"] == "8:00"


def test_extract_tokens_with_quotes():
    result = _extract_tokens('preview cotizar cliente "Bohdan" 200 "Bombona1" mañana 8:00')
    assert result["dry_run"] is True
    assert result["cliente_raw"] == "Bohdan"
    assert result["items_raw"] == [{"cantidad": 200, "producto": "Bombona1"}]
    assert result["fecha_raw"] == "mañana"
    assert result["hora_raw"] == "8:00"


def test_extract_tokens_with_quoted_names_with_spaces():
    result = _extract_tokens('cotizar cliente "Gas del Norte" 500 "Bombona 10kg" hoy')
    assert result["cliente_raw"] == "Gas del Norte"
    assert result["items_raw"] == [{"cantidad": 500, "producto": "Bombona 10kg"}]
    assert result["fecha_raw"] == "hoy"


def test_extract_tokens_with_quoted_vehicle():
    result = _extract_tokens('cotizar cliente Bohdan 200 Bombona1 hoy vehiculo "IHUI-329I4G"')
    assert result["vehiculo_raw"] == "IHUI-329I4G"


def test_extract_tokens_case_insensitive():
    result = _extract_tokens('COTIZAR CLIENTE "BOHDAN" 200 "BOMBONA1" MAÑANA 8:00')
    assert result["cliente_raw"] == "BOHDAN"
    assert result["items_raw"] == [{"cantidad": 200, "producto": "BOMBONA1"}]
    assert result["fecha_raw"] == "MAÑANA"
    assert result["hora_raw"] == "8:00"
