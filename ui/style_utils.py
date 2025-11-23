from PyQt6.QtWidgets import QPushButton, QLabel, QWidget, QLineEdit, QTextEdit
from ui.theme import get_current_theme

def apply_primary_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'primary')

def apply_success_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'success')

def apply_danger_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'danger')

def apply_github_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'github')

def apply_gitlab_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'gitlab')

def apply_icon_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'icon')

def apply_default_button(button: QPushButton):
    theme = get_current_theme()
    theme.apply_button_style(button, 'default')

def apply_title_label(label: QLabel):
    theme = get_current_theme()
    label.setStyleSheet(theme.get_title_label_style())

def apply_heading_label(label: QLabel):
    theme = get_current_theme()
    label.setStyleSheet(theme.get_heading_label_style())

def apply_secondary_label(label: QLabel):
    theme = get_current_theme()
    label.setStyleSheet(theme.get_secondary_label_style())

def apply_card_style(widget: QWidget):
    theme = get_current_theme()
    widget.setStyleSheet(theme.get_card_style())

def apply_input_style(input_widget):
    theme = get_current_theme()
    input_widget.setStyleSheet(theme.get_input_style())

def get_theme():
    return get_current_theme()
