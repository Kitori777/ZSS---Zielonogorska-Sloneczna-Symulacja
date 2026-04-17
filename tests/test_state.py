from datetime import date

from app.state import AppState


def test_reset_to_now_updates_fields():
    state = AppState(selected_date=date(2020, 1, 1), hour=0.0)
    state.reset_to_now()
    assert state.selected_date is not None
    assert 0 <= state.hour < 24
    assert state.playing is False
    assert state.frame_hour == 0.0
