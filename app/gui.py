from datetime import datetime
from pathlib import Path

import pandas as pd

from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QFont, QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import proj3d

from app.state import AppState
from app.simulation import build_frame_state, build_live_state
from app.render_3d import render_scene
from app.weather_data import WeatherRepository


def _safe_local_time_text(value, target_tzinfo):
    if value is None:
        return "--:--:--"

    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime(warn=False)

    if not hasattr(value, "strftime"):
        return str(value)

    if getattr(value, "tzinfo", None) is None or target_tzinfo is None:
        return value.strftime("%H:%M:%S")

    return value.astimezone(target_tzinfo).strftime("%H:%M:%S")


LIGHT_STYLESHEET = """
QWidget {
    background-color: #F5F7FA;
    color: #1F2937;
    font-size: 13px;
}

QMainWindow {
    background-color: #F5F7FA;
}

QFrame#Sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #D8DEE8;
}

QGroupBox {
    border: 1px solid #D8DEE8;
    border-radius: 12px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #FFFFFF;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px 0 4px;
    color: #111827;
}

QLabel#Title {
    font-size: 20px;
    font-weight: 700;
    color: #111827;
}

QLabel#SubTitle {
    font-size: 12px;
    color: #6B7280;
}

QLabel#StatusBar {
    background-color: #FFFFFF;
    border: 1px solid #D8DEE8;
    border-radius: 10px;
    padding: 10px;
    color: #1F2937;
}

QPushButton {
    background-color: #EEF2F7;
    border: 1px solid #D4DCE7;
    border-radius: 10px;
    padding: 10px 14px;
    color: #111827;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #E6ECF3;
}

QPushButton:pressed {
    background-color: #DCE5EF;
}

QPushButton#Primary {
    background-color: #F4B400;
    color: #111111;
    border: none;
}

QPushButton#Primary:hover {
    background-color: #F7C233;
}

QPushButton#Danger {
    background-color: #D9534F;
    color: white;
    border: none;
}

QPushButton#Danger:hover {
    background-color: #C94440;
}

QComboBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #D4DCE7;
    border-radius: 10px;
    padding: 8px;
    min-height: 18px;
    color: #111827;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #D9E2EC;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #F4B400;
    border: none;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::groove:vertical {
    width: 8px;
    background: #D9E2EC;
    border-radius: 4px;
}

QSlider::handle:vertical {
    background: #F4B400;
    border: none;
    height: 16px;
    margin: 0 -5px;
    border-radius: 8px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #AEB8C5;
    background: #FFFFFF;
    border-radius: 4px;
}

QCheckBox::indicator:checked {
    border: 1px solid #F4B400;
    background: #F4B400;
    border-radius: 4px;
}

QFrame#Card {
    background-color: #FFFFFF;
    border: 1px solid #D8DEE8;
    border-radius: 14px;
}

QWidget#CanvasHost {
    background-color: #FFFFFF;
    border: 1px solid #D8DEE8;
    border-radius: 14px;
}
"""


class VerticalTimeSlider(QWidget):
    valueChanged = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        labels_layout = QVBoxLayout()
        labels_layout.setContentsMargins(0, 4, 0, 4)
        labels_layout.setSpacing(0)

        for text in ["24:00", "18:00", "12:00", "06:00", "00:00"]:
            label = QLabel(text)
            label.setStyleSheet("color:#6B7280;")
            if text == "24:00":
                label.setAlignment(Qt.AlignTop | Qt.AlignRight)
            elif text == "00:00":
                label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
            else:
                label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            labels_layout.addWidget(label, 1)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 96)
        self.slider.setInvertedAppearance(True)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.slider.setMinimumHeight(250)

        layout.addWidget(self.slider)
        layout.addLayout(labels_layout)

    def setValue(self, value: int):
        self.slider.setValue(value)

    def value(self) -> int:
        return self.slider.value()

    def blockSignals(self, block: bool):
        return self.slider.blockSignals(block)


class Mpl3DCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(10, 7), facecolor="#FFFFFF")
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.figure.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
        self.latest_analysis = None
        self.zoom_factor = 1.0
        self.view_elev = 28
        self.view_azim = -58
        self.update_theme()

    def update_theme(self):
        self.figure.patch.set_facecolor("#0F1115")
        self.ax.set_facecolor("#0F1115")

    def redraw_scene(self, frame_state, app_state, weather_bundle=None):
        self.latest_analysis = render_scene(
            self.ax,
            frame_state,
            app_state,
            weather_bundle=weather_bundle,
            zoom_factor=self.zoom_factor,
            view_elev=self.view_elev,
            view_azim=self.view_azim,
        )
        self._style_3d_axes()
        self.figure.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
        self.draw_idle()



    def store_current_view(self):
        try:
            self.view_elev = float(self.ax.elev)
            self.view_azim = float(self.ax.azim)
        except Exception:
            pass

    def zoom_in(self):
        self.zoom_factor = min(6.0, self.zoom_factor * 1.25)

    def zoom_out(self):
        self.zoom_factor = max(1.0, self.zoom_factor / 1.25)

    def reset_zoom(self):
        self.zoom_factor = 1.0

    def _style_3d_axes(self):
        ax = self.ax

        try:
            ax.xaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
            ax.yaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
            ax.zaxis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
        except Exception:
            pass

        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
            try:
                axis.line.set_color("#7A8699")
            except Exception:
                pass

        ax.tick_params(colors="#374151")
        ax.xaxis.label.set_color("#1F2937")
        ax.yaxis.label.set_color("#1F2937")
        ax.zaxis.label.set_color("#1F2937")
        ax.title.set_color("#111827")

        try:
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor("#FFFFFF")
                legend.get_frame().set_edgecolor("#D8DEE8")
                legend.get_frame().set_alpha(0.98)
                for text in legend.get_texts():
                    text.set_color("#111827")
        except Exception:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        now = datetime.now()
        self.app_state = AppState(
            selected_date=now.date(),
            hour=now.hour + now.minute / 60.0 + now.second / 3600.0,
        )

        self.base_dir = Path(__file__).resolve().parent.parent
        data_dir = self.base_dir / "data"
        self.export_dir = self.base_dir / "exports"
        self.export_dir.mkdir(exist_ok=True)

        self.current_point_analysis = None
        self.selected_point_payload = None
        self.simulation_records = []
        self.last_recorded_frame_key = None
        self.last_export_path = None

        self.weather_repo = None
        try:
            self.weather_repo = WeatherRepository(
                station_csv=data_dir / "s_t_400_2025_podpisane_wybrane_kolumny_POPRAWNE_OPAD.csv",
                model_csv=data_dir / "zielona_gora_2025_polaczone_celsius.csv",
                extra_rain_csv=data_dir / "zielona_gora_opady_godzinowe_2025.csv",
            )
        except Exception:
            self.weather_repo = None

        self.setWindowTitle("SunCalc 3D — Live i Symulacja")
        self.resize(1600, 950)

        self.live_timer = QTimer(self)
        self.live_timer.timeout.connect(self.refresh_live)
        self.live_timer.start(1000)

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.advance_simulation)

        self._build_ui()
        self._build_actions()
        self._connect_signals()
        self.canvas.mpl_connect("pick_event", self.on_canvas_pick)
        self.canvas.mpl_connect("motion_notify_event", self.on_canvas_hover)
        self.canvas.mpl_connect("button_release_event", self.on_canvas_release)
        self.redraw()

    def _build_actions(self):
        toggle_fullscreen_action = QAction("Przełącz fullscreen", self)
        toggle_fullscreen_action.setShortcut(QKeySequence("F11"))
        toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(toggle_fullscreen_action)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(390)
        self.sidebar.setMaximumWidth(430)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(14)

        title = QLabel("SunCalc 3D")
        title.setObjectName("Title")

        subtitle = QLabel("Live + symulacja słońca, księżyca, światła, cienia oraz pogody")
        subtitle.setObjectName("SubTitle")
        subtitle.setWordWrap(True)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(subtitle)

        mode_group = QGroupBox("Tryb pracy")
        mode_layout = QGridLayout(mode_group)

        self.btn_live = QPushButton("Live")
        self.btn_live.setObjectName("Primary")
        self.btn_sim = QPushButton("Symulacja")
        self.btn_fullscreen = QPushButton("Fullscreen")

        mode_layout.addWidget(self.btn_live, 0, 0)
        mode_layout.addWidget(self.btn_sim, 0, 1)
        mode_layout.addWidget(self.btn_fullscreen, 1, 0, 1, 2)

        sidebar_layout.addWidget(mode_group)

        time_group = QGroupBox("Czas")
        time_layout = QVBoxLayout(time_group)
        time_layout.setSpacing(10)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate(self.app_state.selected_date.year, self.app_state.selected_date.month, self.app_state.selected_date.day))

        self.hour_slider = VerticalTimeSlider()
        self.hour_slider.setValue(int(round(self.app_state.hour * 4)))

        initial_hour = int(self.app_state.hour)
        initial_minute = int(round((self.app_state.hour - initial_hour) * 60))
        if initial_minute == 60:
            initial_hour += 1
            initial_minute = 0
        self.hour_label = QLabel(f"{initial_hour:02d}:{initial_minute:02d}")
        self.hour_label.setAlignment(Qt.AlignCenter)
        self.hour_label.setStyleSheet("font-size:20px; font-weight:700; color:#111827;")

        self.step_combo = QComboBox()
        self.step_combo.addItems(["1 h", "30 min", "15 min"])
        self.step_combo.setCurrentIndex(0)

        self.btn_now = QPushButton("Teraz")
        self.btn_play = QPushButton("Play")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("Danger")

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Data"))
        date_row.addWidget(self.date_edit, 1)

        time_layout.addLayout(date_row)
        time_layout.addWidget(QLabel("Godzina"))
        time_layout.addWidget(self.hour_label)

        slider_controls_row = QHBoxLayout()
        slider_controls_row.setSpacing(12)
        slider_controls_row.addWidget(self.hour_slider, 0, Qt.AlignLeft)

        controls_col = QVBoxLayout()
        controls_col.setSpacing(8)
        controls_col.addWidget(QLabel("Krok"))
        controls_col.addWidget(self.step_combo)
        controls_col.addWidget(self.btn_now)
        controls_col.addWidget(self.btn_play)
        controls_col.addWidget(self.btn_stop)
        controls_col.addStretch()

        slider_controls_row.addLayout(controls_col, 1)
        time_layout.addLayout(slider_controls_row)

        sidebar_layout.addWidget(time_group)

        view_group = QGroupBox("Widok")
        view_layout = QVBoxLayout(view_group)

        self.chk_sun = QCheckBox("Pokaż słońce")
        self.chk_sun.setChecked(True)
        self.chk_moon = QCheckBox("Pokaż księżyc")
        self.chk_moon.setChecked(True)
        self.chk_shadows = QCheckBox("Pokaż cień")
        self.chk_shadows.setChecked(True)
        self.chk_light = QCheckBox("Pokaż strefy światła")
        self.chk_light.setChecked(True)
        self.chk_infield = QCheckBox("Uwzględnij środek toru")
        self.chk_infield.setChecked(True)

        for w in [self.chk_sun, self.chk_moon, self.chk_shadows, self.chk_light, self.chk_infield]:
            view_layout.addWidget(w)

        sidebar_layout.addWidget(view_group)

        weather_group = QGroupBox("Pogoda")
        weather_layout = QVBoxLayout(weather_group)

        self.chk_weather = QCheckBox("Włącz warstwę pogody")
        self.chk_weather.setChecked(True)
        self.chk_clouds = QCheckBox("Pokaż chmury")
        self.chk_clouds.setChecked(True)
        self.chk_rain = QCheckBox("Pokaż deszcz")
        self.chk_rain.setChecked(True)

        self.weather_source_combo = QComboBox()
        self.weather_source_combo.addItems(["best", "openmeteo", "station", "model", "extra"])
        self.weather_source_combo.setCurrentText("best")

        self.weather_info = QLabel(
            "Źródło danych: hybrydowe (Open-Meteo + lokalne CSV)" if self.weather_repo is not None else "Źródło danych: brak / nie udało się wczytać"
        )
        self.weather_info.setWordWrap(True)
        self.weather_info.setStyleSheet("color:#6B7280;")

        weather_layout.addWidget(self.chk_weather)
        weather_layout.addWidget(self.chk_clouds)
        weather_layout.addWidget(self.chk_rain)
        weather_layout.addWidget(QLabel("Źródło danych pogody"))
        weather_layout.addWidget(self.weather_source_combo)
        weather_layout.addWidget(self.weather_info)

        sidebar_layout.addWidget(weather_group)

        status_group = QGroupBox("Status aplikacji")
        status_layout = QVBoxLayout(status_group)

        self.status_box = QLabel()
        self.status_box.setObjectName("StatusBar")
        self.status_box.setWordWrap(True)

        self.point_info_box = QLabel("Kliknij punkt na torze, aby zobaczyć jego dane.")
        self.point_info_box.setObjectName("StatusBar")
        self.point_info_box.setWordWrap(True)

        status_layout.addWidget(self.status_box)
        status_layout.addWidget(self.point_info_box)
        sidebar_layout.addWidget(status_group)

        sidebar_layout.addStretch()

        right_wrap = QWidget()
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(16, 12, 16, 12)

        self.header_label = QLabel("Widok 3D")
        self.header_label.setFont(QFont("Segoe UI", 13, QFont.Bold))

        self.header_info = QLabel("Tryb live")
        self.header_info.setStyleSheet("color:#AAB2BF;")

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_reset = QPushButton("100%")

        top_layout.addWidget(self.header_label)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_zoom_out)
        top_layout.addWidget(self.btn_zoom_in)
        top_layout.addWidget(self.btn_zoom_reset)
        top_layout.addWidget(self.header_info)

        canvas_card = QFrame()
        canvas_card.setObjectName("CanvasHost")
        canvas_layout = QVBoxLayout(canvas_card)
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = Mpl3DCanvas()
        canvas_layout.addWidget(self.canvas)

        right_layout.addWidget(top_card)
        right_layout.addWidget(canvas_card, 1)

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setWidget(self.sidebar)
        sidebar_scroll.setMinimumWidth(400)
        sidebar_scroll.setMaximumWidth(440)

        main_layout.addWidget(sidebar_scroll)
        main_layout.addWidget(right_wrap, 1)

    def _connect_signals(self):
        self.btn_live.clicked.connect(self.set_live_mode)
        self.btn_sim.clicked.connect(self.set_sim_mode)
        self.btn_now.clicked.connect(self.set_now)
        self.btn_play.clicked.connect(self.start_playback)
        self.btn_stop.clicked.connect(self.stop_playback)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        self.btn_zoom_in.clicked.connect(self.on_zoom_in)
        self.btn_zoom_out.clicked.connect(self.on_zoom_out)
        self.btn_zoom_reset.clicked.connect(self.on_zoom_reset)

        self.hour_slider.valueChanged.connect(self.on_hour_changed)
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.step_combo.currentIndexChanged.connect(self.on_step_changed)

        self.chk_sun.toggled.connect(self.on_view_changed)
        self.chk_moon.toggled.connect(self.on_view_changed)
        self.chk_shadows.toggled.connect(self.on_view_changed)
        self.chk_light.toggled.connect(self.on_view_changed)
        self.chk_infield.toggled.connect(self.on_view_changed)

        self.chk_weather.toggled.connect(self.on_weather_changed)
        self.chk_clouds.toggled.connect(self.on_weather_changed)
        self.chk_rain.toggled.connect(self.on_weather_changed)
        self.weather_source_combo.currentIndexChanged.connect(self.on_weather_changed)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def set_live_mode(self):
        self.app_state.mode = "live"
        self.app_state.playing = False
        self.play_timer.stop()
        self.btn_live.setObjectName("Primary")
        self.btn_sim.setObjectName("")
        self._refresh_button_styles()
        self.redraw()

    def set_sim_mode(self):
        self.app_state.mode = "simulation"
        self.btn_live.setObjectName("")
        self.btn_sim.setObjectName("Primary")
        self._refresh_button_styles()
        self.redraw()

    def _refresh_button_styles(self):
        for btn in [self.btn_live, self.btn_sim, self.btn_fullscreen, self.btn_stop]:
            self.style().unpolish(btn)
            self.style().polish(btn)

    def _sync_time_controls(self):
        d = self.app_state.selected_date
        self.date_edit.blockSignals(True)
        self.date_edit.setDate(QDate(d.year, d.month, d.day))
        self.date_edit.blockSignals(False)

        slider_value = int(round(self.app_state.hour * 4))
        self.hour_slider.blockSignals(True)
        self.hour_slider.setValue(slider_value)
        self.hour_slider.blockSignals(False)
        self._update_hour_label()

    def _update_hour_label(self):
        hour = int(self.app_state.hour)
        minute = int(round((self.app_state.hour - hour) * 60))
        if minute == 60:
            hour += 1
            minute = 0
        if hour == 24:
            hour = 0
        self.hour_label.setText(f"{hour:02d}:{minute:02d}")

    def set_now(self):
        self.app_state.reset_to_now()
        self._sync_time_controls()
        self.redraw()

    def start_playback(self):
        self.app_state.mode = "simulation"
        self.app_state.playing = True
        self.app_state.frame_hour = self.app_state.hour
        self.simulation_records = []
        self.last_recorded_frame_key = None
        self.last_export_path = None
        self.play_timer.start(900)
        self.btn_live.setObjectName("")
        self.btn_sim.setObjectName("Primary")
        self._refresh_button_styles()
        self.redraw()

    def stop_playback(self):
        was_playing = self.app_state.playing
        self.app_state.playing = False
        self.play_timer.stop()
        if was_playing:
            self._export_simulation_csv()
        self.redraw()

    def on_hour_changed(self, value):
        self.app_state.hour = value / 4.0
        self._update_hour_label()

        if self.app_state.mode == "simulation" and not self.app_state.playing:
            self.redraw()

    def on_date_changed(self, qdate):
        self.app_state.selected_date = qdate.toPython()
        if self.app_state.mode == "simulation" and not self.app_state.playing:
            self.redraw()

    def on_step_changed(self, index):
        if index == 0:
            self.app_state.time_step_hours = 1
        elif index == 1:
            self.app_state.time_step_hours = 0.5
        else:
            self.app_state.time_step_hours = 0.25

    def on_view_changed(self):
        self.app_state.show_sun = self.chk_sun.isChecked()
        self.app_state.show_moon = self.chk_moon.isChecked()
        self.app_state.show_shadows = self.chk_shadows.isChecked()
        self.app_state.show_light_map = self.chk_light.isChecked()
        self.app_state.include_infield = self.chk_infield.isChecked()
        self.redraw()

    def on_weather_changed(self):
        self.app_state.show_weather = self.chk_weather.isChecked()
        self.app_state.show_clouds = self.chk_clouds.isChecked()
        self.app_state.show_rain = self.chk_rain.isChecked()
        self.app_state.weather_source = self.weather_source_combo.currentText()
        self.redraw()

    def refresh_live(self):
        if self.app_state.mode == "live" and not self.app_state.playing:
            self.app_state.reset_to_now()
            self._sync_time_controls()
            self.redraw()

    def advance_simulation(self):
        if not self.app_state.playing:
            self.play_timer.stop()
            return

        self.app_state.hour = self.app_state.frame_hour
        self._sync_time_controls()
        self.redraw()

        self.app_state.frame_hour += self.app_state.time_step_hours
        if self.app_state.frame_hour >= 24:
            self.app_state.playing = False
            self.play_timer.stop()
            self.app_state.frame_hour = 23.75
            self.app_state.hour = 23.75
            self._sync_time_controls()
            self._export_simulation_csv()



    def on_canvas_release(self, event):
        if event.inaxes == self.canvas.ax:
            self.canvas.store_current_view()

    def on_canvas_hover(self, event):
        if event.inaxes != self.canvas.ax:
            return

        analysis = self.current_point_analysis or self.canvas.latest_analysis
        if not analysis:
            return

        points = analysis.get("all", [])
        if not points:
            return

        mouse_x = event.x
        mouse_y = event.y
        best_item = None
        best_dist = None

        for item in points:
            x2, y2, _ = proj3d.proj_transform(item["x"], item["y"], 0.0, self.canvas.ax.get_proj())
            xdisp, ydisp = self.canvas.ax.transData.transform((x2, y2))
            dist = ((xdisp - mouse_x) ** 2 + (ydisp - mouse_y) ** 2) ** 0.5
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_item = item

        if best_item is not None and best_dist is not None and best_dist <= 14:
            self.selected_point_payload = best_item
            self._update_point_info_box()

    def on_zoom_in(self):
        self.canvas.zoom_in()
        self.redraw()

    def on_zoom_out(self):
        self.canvas.zoom_out()
        self.redraw()

    def on_zoom_reset(self):
        self.canvas.reset_zoom()
        self.redraw()

    def on_canvas_pick(self, event):
        artist = getattr(event, "artist", None)
        payload = getattr(artist, "_point_payload", None)
        indices = getattr(event, "ind", None)
        if payload is None or len(payload) == 0 or indices is None or len(indices) == 0:
            return

        idx = int(indices[0])
        if idx >= len(payload):
            return

        self.selected_point_payload = payload[idx]
        self._update_point_info_box()

    def _update_point_info_box(self):
        item = self.selected_point_payload
        if not item:
            if self.last_export_path:
                self.point_info_box.setText(f"Kliknij punkt na torze, aby zobaczyć jego dane.\nOstatni eksport CSV: {self.last_export_path}")
            else:
                self.point_info_box.setText("Kliknij punkt na torze, aby zobaczyć jego dane.")
            return

        shade_txt = "cień" if item.get("is_shaded") else "słońce"
        point_temp = item.get("estimated_point_temperature_c")
        point_temp_txt = "brak" if point_temp is None else f"{point_temp:.2f} °C"
        air_temp = item.get("air_temperature_c")
        air_temp_txt = "brak" if air_temp is None else f"{air_temp:.2f} °C"
        cloud_value = item.get("cloud_cover")
        cloud_unit = item.get("cloud_unit") or ""
        cloud_txt = "brak" if cloud_value is None else f"{cloud_value:.1f} {cloud_unit}"

        text = (
            f"Punkt: X={item['x']:.1f}, Y={item['y']:.1f}\n"
            f"Obszar: {item.get('point_type', '-') }\n"
            f"Stan: {shade_txt}\n"
            f"Nasłonecznienie: {item.get('solar_exposure_pct', 0.0):.1f}%\n"
            f"Temp. powietrza: {air_temp_txt}\n"
            f"Szac. temp. punktu: {point_temp_txt}\n"
            f"Opad na punkt: {item.get('rain_mm_h', 0.0):.2f} mm/h\n"
            f"Zachmurzenie: {cloud_txt}"
        )
        if self.last_export_path:
            text += f"\nCSV: {self.last_export_path}"
        self.point_info_box.setText(text)

    def _collect_simulation_records(self, frame_state):
        analysis = self.canvas.latest_analysis
        if not analysis:
            return

        frame_key = frame_state["dt_local"].strftime("%Y-%m-%d %H:%M:%S")
        if frame_key == self.last_recorded_frame_key:
            return

        for item in analysis.get("all", []):
            self.simulation_records.append({
                "frame_local_time": frame_key,
                "date": frame_state["dt_local"].strftime("%Y-%m-%d"),
                "time": frame_state["dt_local"].strftime("%H:%M:%S"),
                "x": item.get("x"),
                "y": item.get("y"),
                "point_type": item.get("point_type"),
                "is_shaded": item.get("is_shaded"),
                "solar_exposure_pct": item.get("solar_exposure_pct"),
                "air_temperature_c": item.get("air_temperature_c"),
                "estimated_point_temperature_c": item.get("estimated_point_temperature_c"),
                "rain_mm_h": item.get("rain_mm_h"),
                "cloud_cover": item.get("cloud_cover"),
                "cloud_unit": item.get("cloud_unit"),
            })

        self.last_recorded_frame_key = frame_key

    def _export_simulation_csv(self):
        if not self.simulation_records:
            return

        df = pd.DataFrame(self.simulation_records)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"symulacja_punktow_{stamp}.csv"
        path = self.export_dir / filename
        df.to_csv(path, index=False, encoding="utf-8-sig")
        self.last_export_path = str(path)
        self._update_point_info_box()

    def _get_weather_bundle(self, frame_state):
        if not self.app_state.show_weather or self.weather_repo is None:
            return None
        try:
            return self.weather_repo.get_weather_bundle(
                frame_state["dt_local"],
                source=self.app_state.weather_source,
            )
        except Exception as exc:
            self.weather_info.setText(f"Źródło danych: błąd pobierania ({exc})")
            return None

    def redraw(self):
        if self.app_state.mode == "live":
            frame_state = build_live_state()
            self.header_info.setText("Tryb live")
        else:
            frame_state = build_frame_state(self.app_state.selected_date, self.app_state.hour)
            self.header_info.setText("Tryb symulacji")

        weather_bundle = self._get_weather_bundle(frame_state)
        if self.weather_repo is not None:
            base_text = "Źródło danych: hybrydowe (Open-Meteo + lokalne CSV)"
            if weather_bundle and isinstance(weather_bundle.get("meta"), dict):
                status_text = weather_bundle["meta"].get("openmeteo_status")
                error_text = weather_bundle["meta"].get("openmeteo_error")
                if status_text:
                    base_text = f"{base_text}\n{status_text}"
                if error_text:
                    base_text = f"{base_text}\nSzczegóły: {error_text}"
            self.weather_info.setText(base_text)

        self.canvas.redraw_scene(frame_state, self.app_state, weather_bundle=weather_bundle)
        self.current_point_analysis = self.canvas.latest_analysis
        if self.app_state.mode == "simulation" and self.app_state.playing:
            self._collect_simulation_records(frame_state)
        self._update_status(frame_state, weather_bundle)
        self._update_point_info_box()

    def _update_status(self, frame_state, weather_bundle=None):
        dt_local = frame_state["dt_local"]
        sun_info = frame_state["sun_info"]
        moon_info = frame_state["moon_info"]
        shadow_info = frame_state["shadow_info"]
        day_info = frame_state["day_info"]

        mode_text = "LIVE" if self.app_state.mode == "live" else "SYMULACJA"

        weather_lines = "\n\nPogoda\n• brak danych"
        if weather_bundle:
            clouds = weather_bundle.get("clouds")
            rain = weather_bundle.get("rain")
            temp = weather_bundle.get("temperature")
            meta = weather_bundle.get("meta") or {}

            cloud_val = "brak" if clouds is None or clouds.value is None else f"{clouds.value:.1f} {clouds.unit}"
            rain_val = "brak" if rain is None or rain.value is None else f"{rain.value:.2f} {rain.unit}"
            temp_val = "brak" if temp is None or temp.value is None else f"{temp.value:.1f} {temp.unit}"
            source_val = meta.get("source", self.app_state.weather_source)

            weather_lines = (
                "\n\nPogoda\n"
                f"• źródło: {source_val}\n"
                f"• chmury: {cloud_val}\n"
                f"• opad: {rain_val}\n"
                f"• temperatura: {temp_val}"
            )

        sun_alt = sun_info.get("altitude_deg")
        moon_alt = moon_info.get("altitude_deg")
        sunrise = day_info.get("sunrise")
        sunset = day_info.get("sunset")
        sunrise_txt = _safe_local_time_text(sunrise, dt_local.tzinfo)
        sunset_txt = _safe_local_time_text(sunset, dt_local.tzinfo)

        self.status_box.setText(
            f"Tryb: {mode_text}\n"
            f"Data i czas lokalny: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Azymut słońca: {shadow_info['sun_bearing_deg']:.1f}°\n"
            f"Wysokość słońca: {sun_alt:.2f}°\n"
            f"Wysokość księżyca: {moon_alt:.2f}°\n"
            f"Kierunek cienia: {shadow_info['shadow_bearing_deg']:.1f}°\n"
            f"Wschód słońca: {sunrise_txt}\n"
            f"Zachód słońca: {sunset_txt}"
            f"{weather_lines}"
        )


def run_app():
    app = QApplication([])
    app.setStyleSheet(LIGHT_STYLESHEET)
    window = MainWindow()
    window.show()
    app.exec()
