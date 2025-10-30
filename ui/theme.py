from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication

class Theme:
    def __init__(self, name="Dark"):
        self.name = name
        self.colors = {}
        self.fonts = {}
        self.spacing = {}
        self.borders = {}
        self.load_theme()
    
    def load_theme(self):
        if self.name == "Dark":
            self.colors = {
                'primary': '#4ec9b0',
                'primary_hover': '#5fd9c0',
                'primary_pressed': '#3db89f',
                
                'secondary': '#0e639c',
                'secondary_hover': '#1177bb',
                'secondary_pressed': '#0a4f7d',
                
                'success': '#238636',
                'success_hover': '#2ea043',
                'success_pressed': '#1a7f37',
                
                'danger': '#c42b1c',
                'danger_hover': '#d32f2f',
                'danger_pressed': '#a52315',
                
                'warning': '#f59e0b',
                'warning_hover': '#fbbf24',
                'warning_pressed': '#d97706',
                
                'background': '#1e1e1e',
                'background_secondary': '#252526',
                'background_tertiary': '#2d2d2d',
                'background_elevated': '#3d3d3d',
                
                'surface': '#2d2d2d',
                'surface_hover': '#3d3d3d',
                'surface_selected': '#094771',
                
                'border': '#3d3d3d',
                'border_focus': '#4ec9b0',
                'border_error': '#c42b1c',
                
                'text': '#cccccc',
                'text_secondary': '#999999',
                'text_disabled': '#666666',
                'text_inverse': '#ffffff',
                'text_link': '#4ec9b0',
                
                'input_bg': '#252526',
                'input_border': '#3d3d3d',
                'input_focus': '#4ec9b0',
                
                'scrollbar': '#424242',
                'scrollbar_hover': '#4e4e4e',
                
                'shadow': 'rgba(0, 0, 0, 0.3)',
                
                'unreal': '#0E1128',
                'github': '#238636',
                'gitlab': '#FC6D26',
            }
            
            self.fonts = {
                'family': 'Segoe UI, Ubuntu, sans-serif',
                'size_xs': 10,
                'size_sm': 11,
                'size_base': 12,
                'size_md': 13,
                'size_lg': 14,
                'size_xl': 16,
                'size_2xl': 20,
                'size_3xl': 24,
                'weight_normal': 400,
                'weight_medium': 500,
                'weight_bold': 700,
            }
            
            self.spacing = {
                'xs': 4,
                'sm': 8,
                'md': 12,
                'lg': 16,
                'xl': 20,
                '2xl': 24,
                '3xl': 32,
            }
            
            self.borders = {
                'radius_sm': 4,
                'radius_md': 5,
                'radius_lg': 8,
                'radius_xl': 10,
                'width_thin': 1,
                'width_medium': 2,
                'width_thick': 3,
            }
    
    def get_stylesheet(self):
        return f"""
            /* Global styles */
            * {{
                font-family: {self.fonts['family']};
                font-size: {self.fonts['size_base']}px;
            }}
            
            QMainWindow {{
                background-color: {self.colors['background']};
            }}
            
            QWidget {{
                color: {self.colors['text']};
                background-color: transparent;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {self.colors['surface']};
                color: {self.colors['text']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['sm']}px {self.spacing['md']}px;
                font-size: {self.fonts['size_md']}px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['surface_hover']};
                border-color: {self.colors['primary']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['background_secondary']};
            }}
            
            QPushButton:disabled {{
                color: {self.colors['text_disabled']};
                border-color: {self.colors['border']};
            }}
            
            QPushButton.primary {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_inverse']};
                border: none;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QPushButton.primary:hover {{
                background-color: {self.colors['primary_hover']};
            }}
            
            QPushButton.primary:pressed {{
                background-color: {self.colors['primary_pressed']};
            }}
            
            QPushButton.success {{
                background-color: {self.colors['success']};
                color: {self.colors['text_inverse']};
                border: none;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QPushButton.success:hover {{
                background-color: {self.colors['success_hover']};
            }}
            
            QPushButton.success:pressed {{
                background-color: {self.colors['success_pressed']};
            }}
            
            QPushButton.danger {{
                background-color: {self.colors['danger']};
                color: {self.colors['text_inverse']};
                border: none;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QPushButton.danger:hover {{
                background-color: {self.colors['danger_hover']};
            }}
            
            QPushButton.danger:pressed {{
                background-color: {self.colors['danger_pressed']};
            }}
            
            /* Input fields */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {self.colors['input_bg']};
                color: {self.colors['text']};
                border: {self.borders['width_thin']}px solid {self.colors['input_border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['sm']}px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {self.colors['input_focus']};
            }}
            
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
                color: {self.colors['text_disabled']};
                background-color: {self.colors['background_secondary']};
            }}
            
            /* Lists */
            QListWidget {{
                background-color: {self.colors['background_secondary']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['xs']}px;
            }}
            
            QListWidget::item {{
                padding: {self.spacing['md']}px;
                border-radius: {self.borders['radius_sm']}px;
                margin: {self.spacing['xs']}px;
            }}
            
            QListWidget::item:hover {{
                background-color: {self.colors['surface']};
            }}
            
            QListWidget::item:selected {{
                background-color: {self.colors['surface_selected']};
                color: {self.colors['text_inverse']};
            }}
            
            /* Tables */
            QTableWidget {{
                background-color: {self.colors['background_secondary']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                gridline-color: {self.colors['border']};
            }}
            
            QTableWidget::item {{
                padding: {self.spacing['sm']}px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.colors['surface_selected']};
            }}
            
            QHeaderView::section {{
                background-color: {self.colors['surface']};
                color: {self.colors['text']};
                padding: {self.spacing['sm']}px;
                border: none;
                border-bottom: {self.borders['width_thin']}px solid {self.colors['border']};
                font-weight: {self.fonts['weight_bold']};
            }}
            
            /* Tabs */
            QTabWidget::pane {{
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                background-color: {self.colors['background']};
                border-radius: {self.borders['radius_md']}px;
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['surface']};
                color: {self.colors['text']};
                padding: {self.spacing['sm']}px {self.spacing['lg']}px;
                margin-right: {self.spacing['xs']}px;
                border-top-left-radius: {self.borders['radius_md']}px;
                border-top-right-radius: {self.borders['radius_md']}px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['background']};
                color: {self.colors['primary']};
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {self.colors['surface_hover']};
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {self.colors['background_secondary']};
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.colors['scrollbar']};
                min-height: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['scrollbar_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.colors['background_secondary']};
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.colors['scrollbar']};
                min-width: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.colors['scrollbar_hover']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            /* Menus */
            QMenu {{
                background-color: {self.colors['surface']};
                border: {self.borders['width_thin']}px solid {self.colors['border_focus']};
                padding: {self.spacing['xs']}px;
                border-radius: {self.borders['radius_md']}px;
            }}
            
            QMenu::item {{
                padding: {self.spacing['sm']}px {self.spacing['xl']}px;
                color: {self.colors['text']};
                border-radius: {self.borders['radius_sm']}px;
            }}
            
            QMenu::item:selected {{
                background-color: {self.colors['surface_selected']};
                color: {self.colors['text_inverse']};
            }}
            
            QMenu::separator {{
                height: {self.borders['width_thin']}px;
                background-color: {self.colors['border']};
                margin: {self.spacing['xs']}px 0px;
            }}
            
            /* Status bar */
            QStatusBar {{
                background-color: {self.colors['background_secondary']};
                color: {self.colors['text_secondary']};
                border-top: {self.borders['width_thin']}px solid {self.colors['border']};
            }}
            
            /* Labels */
            QLabel {{
                color: {self.colors['text']};
            }}
            
            QLabel[class="secondary"] {{
                color: {self.colors['text_secondary']};
            }}
            
            QLabel[class="title"] {{
                font-size: {self.fonts['size_2xl']}px;
                font-weight: {self.fonts['weight_bold']};
                color: {self.colors['primary']};
            }}
            
            QLabel[class="heading"] {{
                font-size: {self.fonts['size_xl']}px;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            /* Group boxes */
            QGroupBox {{
                font-weight: {self.fonts['weight_bold']};
                border: {self.borders['width_medium']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_lg']}px;
                margin-top: {self.spacing['md']}px;
                padding-top: {self.spacing['md']}px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {self.spacing['md']}px;
                padding: 0 {self.spacing['xs']}px;
            }}
            
            /* Progress bar */
            QProgressBar {{
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                text-align: center;
                background-color: {self.colors['background_secondary']};
            }}
            
            QProgressBar::chunk {{
                background-color: {self.colors['primary']};
                border-radius: {self.borders['radius_sm']}px;
            }}
            
            /* Tooltips */
            QToolTip {{
                background-color: {self.colors['background_elevated']};
                color: {self.colors['text']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_sm']}px;
                padding: {self.spacing['xs']}px {self.spacing['sm']}px;
            }}
            
            /* Checkboxes and Radio buttons */
            QCheckBox, QRadioButton {{
                spacing: {self.spacing['sm']}px;
            }}
            
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            
            QCheckBox::indicator {{
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_sm']}px;
                background-color: {self.colors['input_bg']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary']};
                border-color: {self.colors['primary']};
            }}
            
            QRadioButton::indicator {{
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: 8px;
                background-color: {self.colors['input_bg']};
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {self.colors['primary']};
                border-color: {self.colors['primary']};
            }}
            
            /* Combo box */
            QComboBox {{
                background-color: {self.colors['input_bg']};
                border: {self.borders['width_thin']}px solid {self.colors['input_border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['sm']}px;
                min-width: 80px;
            }}
            
            QComboBox:hover {{
                border-color: {self.colors['primary']};
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.colors['surface']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                selection-background-color: {self.colors['surface_selected']};
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {self.colors['border']};
            }}
            
            QSplitter::handle:hover {{
                background-color: {self.colors['primary']};
            }}
        """
    
    def apply_to_app(self, app: QApplication):
        app.setStyleSheet(self.get_stylesheet())
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors['background']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors['text']))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors['background_secondary']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors['surface']))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors['text']))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors['surface']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors['text']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors['surface_selected']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors['text_inverse']))
        
        app.setPalette(palette)
        
        font = QFont(self.fonts['family'].split(',')[0])
        font.setPointSize(self.fonts['size_base'])
        app.setFont(font)

theme = Theme("Dark")
