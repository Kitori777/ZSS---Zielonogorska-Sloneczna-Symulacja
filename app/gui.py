from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QFont
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
    QSlider,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.state import AppState
from app.simulation import build_frame_state, build_live_state
from app.render_3d import render_scene


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

class Mpl3DCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(10, 7), facecolor="#FFFFFF")
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.update_theme()

    def update_theme(self):
        self.figure.patch.set_facecolor("#0F1115")
        self.ax.set_facecolor("#0F1115")

    def redraw_scene(self, frame_state, app_state):
        render_scene(self.ax, frame_state, app_state)
        self._style_3d_axes()
        self.draw_idle()

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
            hour=now.hour,
        )

        self.setWindowTitle("SunCalc 3D — Live i Symulacja")
        self.resize(1600, 950)

        self.live_timer = QTimer(self)
        self.live_timer.timeout.connect(self.refresh_live)
        self.live_timer.start(500)

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.advance_simulation)

        self._build_ui()
        self._connect_signals()
        self.redraw()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(370)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(14)

        title = QLabel("SunCalc 3D")
        title.setObjectName("Title")

        subtitle = QLabel("Live + symulacja słońca, księżyca, światła i cienia")
        subtitle.setObjectName("SubTitle")
        subtitle.setWordWrap(True)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(subtitle)

        # TRYB
        mode_group = QGroupBox("Tryb pracy")
        mode_layout = QGridLayout(mode_group)

        self.btn_live = QPushButton("Live")
        self.btn_live.setObjectName("Primary")
        self.btn_sim = QPushButton("Symulacja")

        mode_layout.addWidget(self.btn_live, 0, 0)
        mode_layout.addWidget(self.btn_sim, 0, 1)

        sidebar_layout.addWidget(mode_group)

        # CZAS
        time_group = QGroupBox("Czas")
        time_layout = QGridLayout(time_group)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate(self.app_state.selected_date.year, self.app_state.selected_date.month, self.app_state.selected_date.day))

        self.hour_slider = QSlider(Qt.Horizontal)
        self.hour_slider.setRange(0, 96)
        self.hour_slider.setValue(int(round(self.app_state.hour * 4)))

        initial_hour = int(self.app_state.hour)
        initial_minute = int(round((self.app_state.hour - initial_hour) * 60))
        self.hour_label = QLabel(f"{initial_hour:02d}:{initial_minute:02d}")
        self.hour_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.step_combo = QComboBox()
        self.step_combo.addItems(["1 h", "30 min", "15 min"])
        self.step_combo.setCurrentIndex(0)

        self.btn_now = QPushButton("Teraz")
        self.btn_play = QPushButton("Play")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("Danger")

        time_layout.addWidget(QLabel("Data"), 0, 0)
        time_layout.addWidget(self.date_edit, 0, 1, 1, 2)

        time_layout.addWidget(QLabel("Godzina"), 1, 0)
        time_layout.addWidget(self.hour_slider, 1, 1)
        time_layout.addWidget(self.hour_label, 1, 2)

        time_layout.addWidget(QLabel("Krok"), 2, 0)
        time_layout.addWidget(self.step_combo, 2, 1, 1, 2)

        time_layout.addWidget(self.btn_now, 3, 0)
        time_layout.addWidget(self.btn_play, 3, 1)
        time_layout.addWidget(self.btn_stop, 3, 2)

        sidebar_layout.addWidget(time_group)

        # WIDOK
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

        # STATUS
        status_group = QGroupBox("Status aplikacji")
        status_layout = QVBoxLayout(status_group)

        self.status_box = QLabel()
        self.status_box.setObjectName("StatusBar")
        self.status_box.setWordWrap(True)

        status_layout.addWidget(self.status_box)
        sidebar_layout.addWidget(status_group)

        sidebar_layout.addStretch()

        # PRAWA CZĘŚĆ
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

        top_layout.addWidget(self.header_label)
        top_layout.addStretch()
        top_layout.addWidget(self.header_info)

        canvas_card = QFrame()
        canvas_card.setObjectName("CanvasHost")
        canvas_layout = QVBoxLayout(canvas_card)
        canvas_layout.setContentsMargins(10, 10, 10, 10)

        self.canvas = Mpl3DCanvas()
        canvas_layout.addWidget(self.canvas)

        right_layout.addWidget(top_card)
        right_layout.addWidget(canvas_card, 1)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(right_wrap, 1)

    def _connect_signals(self):
        self.btn_live.clicked.connect(self.set_live_mode)
        self.btn_sim.clicked.connect(self.set_sim_mode)
        self.btn_now.clicked.connect(self.set_now)
        self.btn_play.clicked.connect(self.start_playback)
        self.btn_stop.clicked.connect(self.stop_playback)

        self.hour_slider.valueChanged.connect(self.on_hour_changed)
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.step_combo.currentIndexChanged.connect(self.on_step_changed)

        self.chk_sun.toggled.connect(self.on_view_changed)
        self.chk_moon.toggled.connect(self.on_view_changed)
        self.chk_shadows.toggled.connect(self.on_view_changed)
        self.chk_light.toggled.connect(self.on_view_changed)
        self.chk_infield.toggled.connect(self.on_view_changed)

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
        self.style().unpolish(self.btn_live)
        self.style().polish(self.btn_live)
        self.style().unpolish(self.btn_sim)
        self.style().polish(self.btn_sim)

    def set_now(self):
        self.app_state.reset_to_now()
        d = self.app_state.selected_date
        self.date_edit.setDate(QDate(d.year, d.month, d.day))
        self.hour_slider.setValue(self.app_state.hour)
        self.redraw()

    def start_playback(self):
        self.app_state.mode = "simulation"
        self.app_state.playing = True
        self.app_state.frame_hour = 0.0
        self.hour_slider.setValue(0)
        self.play_timer.start(900)
        self.btn_live.setObjectName("")
        self.btn_sim.setObjectName("Primary")
        self._refresh_button_styles()
        self.redraw()

    def stop_playback(self):
        self.app_state.playing = False
        self.play_timer.stop()
        self.redraw()

    def on_hour_changed(self, value):
        self.app_state.hour = value / 4.0

        hour = int(self.app_state.hour)
        minute = int(round((self.app_state.hour - hour) * 60))
        if minute == 60:
            hour += 1
            minute = 0

        self.hour_label.setText(f"{hour:02d}:{minute:02d}")

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

    def refresh_live(self):
        if self.app_state.mode == "live" and not self.app_state.playing:
            self.redraw()

    def advance_simulation(self):
        if not self.app_state.playing:
            self.play_timer.stop()
            return

        current_hour = self.app_state.frame_hour
        self.app_state.hour = current_hour
        self.hour_slider.setValue(int(round(current_hour * 4)))

        self.redraw()

        self.app_state.frame_hour += self.app_state.time_step_hours
        if self.app_state.frame_hour >= 24:
            self.app_state.playing = False
            self.play_timer.stop()
            self.app_state.frame_hour = 0.0

    def redraw(self):
        if self.app_state.mode == "live":
            frame_state = build_live_state()
            self.header_info.setText("Tryb live")
        else:
            frame_state = build_frame_state(self.app_state.selected_date, self.app_state.hour)
            self.header_info.setText("Tryb symulacji")

        self.canvas.redraw_scene(frame_state, self.app_state)
        self._update_status(frame_state)

    def _update_status(self, frame_state):
        dt_local = frame_state["dt_local"]
        sun_info = frame_state["sun_info"]
        moon_info = frame_state["moon_info"]
        shadow_info = frame_state["shadow_info"]
        day_info = frame_state["day_info"]

        mode_text = "LIVE" if self.app_state.mode == "live" else "SYMULACJA"

        self.status_box.setText(
            f"Tryb: {mode_text}\n"
            f"Data: {dt_local.strftime('%Y-%m-%d')}\n"
            f"Godzina: {dt_local.strftime('%H:%M:%S')}\n\n"
            f"Słońce\n"
            f"• azymut: {shadow_info['sun_bearing_deg']:.1f}°\n"
            f"• wysokość: {sun_info['altitude_deg']:.1f}°\n"
            f"• cień: {shadow_info['shadow_bearing_deg']:.1f}°\n\n"
            f"Księżyc\n"
            f"• azymut: {moon_info['bearing_deg']:.1f}°\n"
            f"• wysokość: {moon_info['altitude_deg']:.1f}°\n\n"
            f"Dzień\n"
            f"• wschód: {day_info['sunrise'].strftime('%H:%M')}\n"
            f"• zachód: {day_info['sunset'].strftime('%H:%M')}"
        )


def run_app():
    app = QApplication([])
    app.setStyleSheet(LIGHT_STYLESHEET)

    window = MainWindow()
    window.show()

    app.exec()
