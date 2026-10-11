APP_STYLE = r"""
* {
    font-family: "Segoe UI";
}
QWidget {
    background: #0b1420;
    color: #dbe7f5;
    font-size: 14px;
}
QMainWindow {
    background: #08111b;
}
QFrame#sidebar {
    background: #09131e;
    border-right: 1px solid #26384a;
}
QFrame#header {
    background: #0d1723;
    border-bottom: 1px solid #314154;
}
QFrame#pageHeader {
    background: #111d2a;
    border: 1px solid #1e3041;
    border-radius: 12px;
}
QFrame#sectionCard {
    background: #111d2a;
    border: 1px solid #3a4b5d;
    border-radius: 10px;
}
QFrame#sectionLine {
    color: #35485a;
    background: #35485a;
    min-height: 1px;
    max-height: 1px;
    border: none;
}
QFrame#headerDivider {
    color: #43576b;
}
QLabel#appLogo {
    color: #22d3ee;
    font-size: 43px;
    font-weight: 900;
}
QLabel#appTitle {
    color: #f3f7fb;
    font-size: 27px;
    font-weight: 850;
}
QLabel#headerMode {
    color: #22d3ee;
    font-size: 16px;
    font-weight: 850;
    padding: 0 12px;
}
QLabel#headerClock {
    color: #f3f7fb;
    font-size: 15px;
    font-weight: 800;
    padding-left: 12px;
}
QLabel#sidebarBrand {
    color: #55e7f2;
    font-size: 20px;
    font-weight: 900;
    padding: 10px 24px 24px 24px;
}
QLabel#sidebarVersion {
    color: #8ea4ba;
    font-size: 13px;
    padding: 14px 22px;
}
QLabel#pageTitle {
    color: #f5f8fb;
    font-size: 31px;
    font-weight: 850;
}
QLabel#pageSubtitle {
    color: #a8b6c7;
    font-size: 14px;
}
QLabel#pageIcon {
    color: #22d3ee;
    font-size: 34px;
    font-weight: 700;
}
QLabel#sectionTitle {
    color: #eef5ff;
    font-size: 16px;
    font-weight: 850;
}
QLabel#sectionIcon {
    color: #c8d8ec;
    font-size: 19px;
}
QLabel#muted, QLabel#metricCaption {
    color: #94a8bd;
}
QFrame#metricPanel {
    background: #0d1825;
    border: 1px solid #2b4054;
    border-radius: 8px;
    padding: 8px;
}
QLabel#metricValue {
    color: #21d7ee;
    font-size: 27px;
    font-weight: 850;
}
QLabel#metricUnit {
    color: #9eb0c3;
    font-size: 14px;
}
QLabel#counterName {
    color: #e4edf7;
    font-size: 15px;
}
QLabel#counterValue {
    color: #25d7ee;
    background: #08111b;
    border: 1px solid #172638;
    border-radius: 5px;
    min-width: 82px;
    padding: 5px 8px;
    font-family: "Consolas";
    font-size: 24px;
    font-weight: 850;
}
QLabel#deviceFieldName {
    color: #9eb0c3;
    font-size: 14px;
}
QLabel#deviceFieldValue {
    color: #e9f2fb;
    font-size: 15px;
    font-weight: 750;
}
QLabel#totalCounterValue {
    color: #22d3ee;
    background: #08111b;
    border: 1px solid #172638;
    border-radius: 5px;
    min-width: 82px;
    padding: 5px 8px;
    font-family: "Consolas";
    font-size: 25px;
    font-weight: 900;
}
QLabel#modeBadge {
    color: #07121c;
    background: #22d3ee;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 24px;
    font-weight: 900;
}
QLabel#statusText {
    color: #dce8f4;
    font-size: 14px;
}
QLabel#cameraView {
    background: #03080d;
    color: #71859a;
    border: 1px solid #435568;
    border-radius: 7px;
}
QPushButton {
    background: #17283a;
    color: #e6eef8;
    border: 1px solid #40556c;
    border-radius: 7px;
    padding: 9px 14px;
    font-size: 14px;
    font-weight: 650;
}
QPushButton:hover {
    background: #20364d;
    border-color: #5a7692;
}
QPushButton:pressed {
    background: #102235;
}
QPushButton:disabled {
    background: #101923;
    color: #617387;
    border-color: #283747;
}
QPushButton#navButton {
    background: transparent;
    border: 0;
    border-radius: 0;
    text-align: left;
    padding: 15px 24px;
    color: #c5d3e3;
    font-size: 21px;
    font-weight: 650;
    min-height: 34px;
}
QPushButton#navButton:hover {
    background: #102131;
}
QPushButton#navButton[active="true"] {
    background: #102c3d;
    color: #22d3ee;
    border-left: 5px solid #20e6ef;
    padding-left: 19px;
    font-weight: 800;
}
QPushButton#startButton {
    background: #0f9f5d;
    border-color: #24d083;
    color: white;
    font-size: 18px;
    font-weight: 800;
    padding: 14px;
}
QPushButton#pauseButton {
    background: #d59a05;
    border-color: #ffd23f;
    color: white;
    font-size: 18px;
    font-weight: 800;
    padding: 14px;
}
QPushButton#stopButton {
    background: #d13b36;
    border-color: #ff625c;
    color: white;
    font-size: 18px;
    font-weight: 800;
    padding: 14px;
}
QPushButton#resetButton {
    background: #1475cb;
    border-color: #3699ee;
    color: white;
    font-size: 18px;
    font-weight: 800;
    padding: 14px;
}
QPushButton#manualButton {
    background: #075da8;
    border-color: #1885e3;
    color: #ffffff;
    font-size: 17px;
    font-weight: 800;
    min-height: 52px;
}
QPushButton#positiveButton {
    background: #078653;
    border-color: #16c97a;
}
QPushButton#negativeButton {
    background: #c93333;
    border-color: #ef5350;
}
QPushButton#cameraOnButton {
    background: #079d61;
    border-color: #20cd83;
}
QPushButton#secondaryBlueButton {
    background: #1476cb;
    border-color: #339cf0;
}
QPushButton#secondaryYellowButton {
    background: #d59808;
    border-color: #f7c832;
}
QPushButton#secondaryRedButton {
    background: #cc3935;
    border-color: #ef5a54;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0b1724;
    color: #eef5ff;
    border: 1px solid #41566d;
    border-radius: 6px;
    padding: 7px 9px;
    min-height: 24px;
}
QComboBox::drop-down {
    border: 0;
    width: 28px;
}
QTableWidget {
    background: #0c1723;
    alternate-background-color: #101e2c;
    border: 1px solid #3d5166;
    border-radius: 5px;
    gridline-color: #273a4e;
    selection-background-color: #143a50;
    selection-color: #ffffff;
}
QHeaderView::section {
    background: #1a2a3b;
    color: #dbe8f4;
    padding: 7px;
    border: 0;
    border-right: 1px solid #31475b;
    font-weight: 700;
}
QScrollBar:vertical {
    background: #0a1520;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #40566c;
    border-radius: 5px;
    min-height: 30px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #263d54;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    margin: -5px 0;
    background: #f0f6ff;
    border: 2px solid #8da4bb;
    border-radius: 8px;
}
QCheckBox {
    spacing: 8px;
}
"""
