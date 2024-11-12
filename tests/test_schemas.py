import pytest
from pydantic import ValidationError

from app.schemas import MatchCreateIn, PlayerJoinIn


def test_match_create_with_valid_data():
    data = {
        "lobby_name": "ValidLobby",
        "password": "",
        "max_players": 4,
        "player_name": "PlayerOne",
        "token": "sampletoken123"
    }
    match = MatchCreateIn(**data)
    
    assert match.lobby_name == "ValidLobby"
    assert match.is_public is True
    assert match.password == ""
    assert match.max_players == 4
    assert match.player_name == "PlayerOne"

def test_match_create_with_valid_data_and_password():
    data = {
        "lobby_name": "ValidLobby",
        "password": "Password",
        "max_players": 4,
        "player_name": "PlayerOne",
        "token": "sampletoken123"
    }
    match = MatchCreateIn(**data)
    
    assert match.lobby_name == "ValidLobby"
    assert match.is_public is False
    assert match.password == "Password"
    assert match.max_players == 4
    assert match.player_name == "PlayerOne"


def test_match_create_in_password_validation():
    data = {
        "lobby_name": "ValidLobby",
        "password": "invalid@password",
        "max_players": 4,
        "player_name": "PlayerOne",
        "token": "sampletoken123"
    }
    with pytest.raises(ValidationError) as excinfo:
        MatchCreateIn(**data)
    assert " Value error, Input must be alphanumeric" in str(excinfo.value)
    
    # Caso: longitud de la contraseña fuera de límites
    data["password"] = "pw"
    with pytest.raises(ValidationError) as excinfo:
        MatchCreateIn(**data)
    assert "Input length must be great than 3 and less than 50" in str(excinfo.value)

# Prueba de validación de campos `lobby_name` y `player_name`
def test_match_create_in_lobby_name_and_player_name_validation():
    data = {
        "lobby_name": "LobbyName#Lobby",
        "password": "",
        "max_players": 4,
        "player_name": "ValidPlayer",
        "token": "sampletoken123"
    }
    
    data["lobby_name"] = "LobbyName"
    data["player_name"] = "Invalid!Player"
    with pytest.raises(ValidationError) as excinfo:
        MatchCreateIn(**data)
    assert "Input must contain alphanumeric words" in str(excinfo.value)

# Prueba de validación de campo `max_players`
def test_match_create_in_max_players_validation():
    data = {
        "lobby_name": "ValidLobby",
        "password": "",
        "max_players": 1,  # Valor fuera del rango permitido
        "player_name": "PlayerOne",
        "token": "sampletoken123"
    }
    with pytest.raises(ValidationError) as excinfo:
        MatchCreateIn(**data)
    assert "Input must be a number between 2 and 4" in str(excinfo.value)

# Prueba de validación condicional para `is_public`
def test_match_create_in_is_public_conditional():
    # Caso: contraseña vacía (is_public debe ser True)
    data = {
        "lobby_name": "ValidLobby",
        "password": "",
        "max_players": 4,
        "player_name": "PlayerOne",
        "token": "sampletoken123"
    }
    match = MatchCreateIn(**data)
    assert match.is_public is True

    # Caso: contraseña no vacía (is_public debe ser False)
    data["password"] = "securepassword"
    match = MatchCreateIn(**data)
    assert match.is_public is False


    # Prueba con datos válidos
def test_player_join_in_valid_data():
    data = {
        "player_name": "ValidPlayer",
        "password": "validpassword123"
    }
    player = PlayerJoinIn(**data)
    
    assert player.player_name == "ValidPlayer"
    assert player.password == "validpassword123"

# Prueba de validación para `player_name`
def test_player_join_in_player_name_validation():
    # Caso: nombre de jugador con caracteres inválidos
    data = {
        "player_name": "ab",
        "password": "password123"
    }

    # Caso: longitud del nombre de jugador fuera de límites
    data["player_name"] = "ab"  # Demasiado corto
    with pytest.raises(ValidationError) as excinfo:
        PlayerJoinIn(**data)
    assert "Input length must be great than 3 and less than 50" in str(excinfo.value)

    # Caso: nombre de jugador no alfanumérico
    data["player_name"] = "Player!@"
    with pytest.raises(ValidationError) as excinfo:
        PlayerJoinIn(**data)
    assert "Input must contain alphanumeric words" in str(excinfo.value)

# Prueba de validación para `password`
def test_player_join_in_password_validation():
    # Caso: contraseña con caracteres inválidos
    data = {
        "player_name": "ValidPlayer",
        "password": "invalid@password"
    }
    # Caso: longitud de la contraseña fuera de límites
    data["password"] = "pw"  # Demasiado corta
    with pytest.raises(ValidationError) as excinfo:
        PlayerJoinIn(**data)
    assert "Input length must be great than 3 and less than 50" in str(excinfo.value)

    # Caso: contraseña no alfanumérica
    data["password"] = "pass!word"
    with pytest.raises(ValidationError) as excinfo:
        PlayerJoinIn(**data)
    assert "Input must be alphanumeric" in str(excinfo.value)
    
    # Caso: contraseña vacía (debe pasar, ya que es opcional)
    data["password"] = ""
    player = PlayerJoinIn(**data)
    assert player.password == ""