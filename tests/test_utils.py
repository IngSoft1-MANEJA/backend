import pytest
from app.utils.utils import validate_color
from app.exceptions import ColorNotValid
from app.models.enums import Colors

def test_validate_color_valid():
    # Prueba con un color válido
    try:
        validate_color("red")
    except ColorNotValid:
        pytest.fail("validate_color raised ColorNotValid unexpectedly!")

def test_validate_color_invalid():
    # Prueba con un color inválido
    with pytest.raises(ColorNotValid):
        validate_color("black")