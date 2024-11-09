import pytest
from sqlalchemy.orm.exc import NoResultFound

from app.models.models import Matches
from app.models.enums import MatchState


def test_get_matches(match_service, db_session):
    matches = match_service.get_all_matches()
    list_matches = [
        {'name': 'Match 1', 'max_players': 4, 'public': True},
        {'name': 'Match 2', 'max_players': 4, 'public': False},
        {'name': 'Match 3', 'max_players': 4, 'public': True}
    ]
    for match in list_matches:
        new_match = Matches(match_name=match['name'], max_players=match['max_players'],
                            is_public=match['public'], state=MatchState.WAITING.value, current_players=0)
        db_session.add(new_match)
        db_session.commit()
    matches2 = match_service.get_all_matches()
    assert len(matches2) == len(matches) + 3


def test_delete_match(match_service, db_session):
    match = match_service.create_match('Test Match', 4, public=True)
    number_matches = db_session.query(Matches).count()
    match_id = match_service.get_match_id(match)
    match_service.delete_match(match_id)
    new_number_matches = db_session.query(Matches).count()
    assert new_number_matches == number_matches - 1


def test_create_match(match_service, db_session):
    number_matches = db_session.query(Matches).count()
    match_service.create_match('Test Match', 4, public=True)
    new_number_matches = db_session.query(Matches).count()

    assert new_number_matches == number_matches + 1


def test_get_match_id(match_service, db_session):
    match = match_service.create_match('Test-Match-Id', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = db_session.query(Matches).filter(
        Matches.match_name == 'Test-Match-Id').first().id
    # Obtener el ID del match usando el servicio
    match_id2 = match_service.get_match_id(match)
    # Verificar que el ID del match devuelto es el esperado
    assert match_id == match_id2


def test_get_match_by_id(match_service):
    match = match_service.create_match('Test-Match-Id', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = match_service.get_match_id(match)
    # Obtener el match usando el servicio
    match2 = match_service.get_match_by_id(match_id)
    # Verificar que los valores del diccionario devuelto son los esperados
    assert match == match2


def test_update_match(match_service):
    match = match_service.create_match('Test-Match-Update', 4, public=True)
    # Obtener el ID del match recién creado
    match_id = match_service.get_match_id(match)
    # Actualizar el match
    match_service.update_match(
        match_id, new_state=MatchState.WAITING.value, new_amount_players=2)
    # chequeo que el match se haya actualizado
    match_info = match_service.get_match_by_id(match_id)
    assert match_info.current_players == 2
    assert match_info.state == MatchState.WAITING.value


def test_update_turn_success(match_service, db_session):
    # Crear un match para la prueba
    match_service.create_match('test_match', 4, True)
    match = db_session.query(Matches).filter(Matches.match_name == 'test_match').one()
    
    # Actualizar el turno del match
    new_turn = 2
    match_service.update_turn(match.id, new_turn)
    
    # Verificar que el turno se ha actualizado correctamente
    updated_match = db_session.query(Matches).filter(Matches.id == match.id).one()
    assert updated_match.current_player_turn == new_turn

def test_update_turn_failure(match_service):
    # Intentar actualizar el turno de un match que no existe
    non_existent_match_id = 9999
    new_turn = 2
    
    with pytest.raises(NoResultFound):
        match_service.update_turn(non_existent_match_id, new_turn)