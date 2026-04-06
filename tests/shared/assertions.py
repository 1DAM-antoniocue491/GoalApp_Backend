# tests/shared/assertions.py
"""
Custom assertions reutilizables para tests.
"""


def assert_response_status(response, expected_status: int):
    """Verifica el codigo de estado de la respuesta."""
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_response_has_keys(response, keys: list):
    """Verifica que la respuesta JSON contiene las claves esperadas."""
    data = response.json()
    for key in keys:
        assert key in data, f"Key '{key}' not found in response: {data}"


def assert_response_list_length(response, expected_length: int):
    """Verifica que la respuesta es una lista con la longitud esperada."""
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) == expected_length, \
        f"Expected list length {expected_length}, got {len(data)}"


def assert_response_error_message(response, expected_message: str):
    """Verifica que la respuesta contiene un mensaje de error."""
    data = response.json()
    assert "detail" in data, f"No 'detail' key in response: {data}"
    assert expected_message in data["detail"], \
        f"Expected error message containing '{expected_message}', got '{data['detail']}'"