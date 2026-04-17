import pytest

PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from app.gui import Mpl3DCanvas, _safe_local_time_text


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_safe_local_time_text_returns_string():
    assert isinstance(_safe_local_time_text(None, None), str)


def test_mpl_canvas_zoom_methods(qapp):
    canvas = Mpl3DCanvas()
    assert canvas.zoom_factor == 1.0
    canvas.zoom_in()
    assert canvas.zoom_factor > 1.0
    canvas.zoom_out()
    canvas.reset_zoom()
    assert canvas.zoom_factor == 1.0
