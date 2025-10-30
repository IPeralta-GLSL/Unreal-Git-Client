from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication

class Theme:
    def __init__(self, name="Dark"):
        self.name = name
        self.colors = {}
        self.fonts = {}
        self.spacing = {}
        self.borders = {}
        self.shadows = {}
        self.animations = {}
        self.load_theme()
    
    def load_theme(self):
        if self.name == "Dark":
            self.colors = {
                'primary': '#4ade80',
                'primary_hover': '#5ef090',
                'primary_pressed': '#3bc970',
                'primary_text': '#ffffff',
                
                'secondary': '#0e639c',
                'secondary_hover': '#1177bb',
                'secondary_pressed': '#0a4f7d',
                
                'success': '#22c55e',
                'success_hover': '#2dd36c',
                'success_pressed': '#16a34a',
                
                'danger': '#ef4444',
                'danger_hover': '#f87171',
                'danger_pressed': '#dc2626',
                
                'warning': '#f59e0b',
                'warning_hover': '#fbbf24',
                'warning_pressed': '#d97706',
                
                'background': '#1e1e1e',
                'background_secondary': '#252526',
                'background_tertiary': '#2d2d2d',
                'background_elevated': '#3d3d3d',
                
                'surface': '#2d2d2d',
                'surface_hover': '#3d3d3d',
                'surface_selected': '#166534',
                
                'border': '#3d3d3d',
                'border_focus': '#4ade80',
                'border_error': '#ef4444',
                
                'text': '#cccccc',
                'text_secondary': '#999999',
                'text_disabled': '#666666',
                'text_inverse': '#ffffff',
                'text_link': '#4ade80',
                
                'input_bg': '#252526',
                'input_border': '#3d3d3d',
                'input_focus': '#4ade80',
                
                'scrollbar': '#424242',
                'scrollbar_hover': '#4e4e4e',
                
                'shadow': 'rgba(0, 0, 0, 0.3)',
                
                'unreal': '#0E1128',
                'github': '#22c55e',
                'gitlab': '#FC6D26',
            }
        
        elif self.name == "Light":
            self.colors = {
                'primary': '#0078d4',
                'primary_hover': '#106ebe',
                'primary_pressed': '#005a9e',
                
                'secondary': '#4ade80',
                'secondary_hover': '#5ef090',
                'secondary_pressed': '#3bc970',
                
                'success': '#107c10',
                'success_hover': '#0e6b0e',
                'success_pressed': '#0c5a0c',
                
                'danger': '#d13438',
                'danger_hover': '#a72b2e',
                'danger_pressed': '#8d2325',
                
                'warning': '#ca5010',
                'warning_hover': '#a74109',
                'warning_pressed': '#8a3508',
                
                'background': '#f3f3f3',
                'background_secondary': '#ffffff',
                'background_tertiary': '#f8f8f8',
                'background_elevated': '#ffffff',
                
                'surface': '#ffffff',
                'surface_hover': '#f3f3f3',
                'surface_selected': '#cce8ff',
                
                'border': '#e0e0e0',
                'border_focus': '#0078d4',
                'border_error': '#d13438',
                
                'text': '#1f1f1f',
                'text_secondary': '#616161',
                'text_disabled': '#a6a6a6',
                'text_inverse': '#ffffff',
                'text_link': '#0078d4',
                
                'input_bg': '#ffffff',
                'input_border': '#d0d0d0',
                'input_focus': '#0078d4',
                
                'scrollbar': '#c0c0c0',
                'scrollbar_hover': '#a0a0a0',
                
                'shadow': 'rgba(0, 0, 0, 0.1)',
                
                'unreal': '#0E1128',
                'github': '#238636',
                'gitlab': '#FC6D26',
            }
        
        # Fuentes, espaciado y bordes son iguales para todos los temas
        if not self.fonts:
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
        
        if not self.spacing:
            self.spacing = {
                'xs': 4,
                'sm': 8,
                'md': 12,
                'lg': 16,
                'xl': 20,
                '2xl': 24,
                '3xl': 32,
            }
        
        if not self.borders:
            self.borders = {
                'radius_sm': 4,
                'radius_md': 6,
                'radius_lg': 8,
                'radius_xl': 12,
                'radius_2xl': 16,
                'width_thin': 1,
                'width_medium': 2,
                'width_thick': 3,
            }
        
        if not self.shadows:
            self.shadows = {
                'sm': 'box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);',
                'md': 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);',
                'lg': 'box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);',
                'xl': 'box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);',
            }
        
        if not self.animations:
            self.animations = {
                'duration_fast': 150,      # ms - para interacciones rápidas como hover
                'duration_normal': 250,     # ms - para transiciones normales
                'duration_slow': 350,       # ms - para animaciones más elaboradas
                'easing': 'ease-in-out',   # tipo de curva de animación
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
            
            QDialog {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            QFileDialog {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            QMessageBox {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            
            QWidget {{
                color: {self.colors['text']};
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
            
            QPushButton.github {{
                background-color: {self.colors['github']};
                color: {self.colors['text_inverse']};
                border: none;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QPushButton.github:hover {{
                background-color: #2ea043;
            }}
            
            QPushButton.github:pressed {{
                background-color: #1a7f37;
            }}
            
            QPushButton.gitlab {{
                background-color: {self.colors['gitlab']};
                color: {self.colors['text_inverse']};
                border: none;
                font-weight: {self.fonts['weight_bold']};
            }}
            
            QPushButton.gitlab:hover {{
                background-color: #FCA326;
            }}
            
            QPushButton.gitlab:pressed {{
                background-color: #E24329;
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
        global current_theme
        current_theme = self
        
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

    def get_button_style(self, variant='default'):
        base_style = f"""
            QPushButton {{
                background-color: {self.colors['surface']};
                color: {self.colors['primary']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['sm']}px {self.spacing['lg']}px;
                font-size: {self.fonts['size_md']}px;
                font-weight: {self.fonts['weight_bold']};
                min-height: 28px;
                
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
        """
        
        if variant == 'primary':
            return f"""
                QPushButton {{
                    background-color: {self.colors['primary']};
                    color: {self.colors['primary_text']};
                    border: none;
                    border-radius: {self.borders['radius_md']}px;
                    padding: {self.spacing['sm']}px {self.spacing['lg']}px;
                    font-size: {self.fonts['size_md']}px;
                    font-weight: {self.fonts['weight_bold']};
                    
                }}
                QPushButton:hover {{
                    background-color: {self.colors['primary_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors['primary_pressed']};
                }}
            """
        elif variant == 'success':
            return f"""
                QPushButton {{
                    background-color: {self.colors['success']};
                    color: {self.colors['text_inverse']};
                    border: none;
                    border-radius: {self.borders['radius_md']}px;
                    padding: {self.spacing['sm']}px {self.spacing['lg']}px;
                    font-size: {self.fonts['size_md']}px;
                    font-weight: {self.fonts['weight_bold']};
                    
                }}
                QPushButton:hover {{
                    background-color: {self.colors['success_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors['success_pressed']};
                }}
            """
        elif variant == 'danger':
            return f"""
                QPushButton {{
                    background-color: {self.colors['danger']};
                    color: {self.colors['text_inverse']};
                    border: none;
                    border-radius: {self.borders['radius_md']}px;
                    padding: {self.spacing['sm']}px {self.spacing['lg']}px;
                    font-size: {self.fonts['size_md']}px;
                    font-weight: {self.fonts['weight_bold']};
                    
                }}
                QPushButton:hover {{
                    background-color: {self.colors['danger_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors['danger_pressed']};
                }}
            """
        
        return base_style
    
    def get_section_header_style(self):
        return f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border-bottom: {self.borders['width_medium']}px solid {self.colors['primary']};
                border-radius: {self.borders['radius_sm']}px {self.borders['radius_sm']}px 0px 0px;
            }}
        """
    
    def get_input_style(self):
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {self.colors['input_bg']};
                color: {self.colors['text']};
                border: {self.borders['width_thin']}px solid {self.colors['input_border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['sm']}px;
                selection-background-color: {self.colors['surface_selected']};
                
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {self.colors['input_focus']};
                border-width: {self.borders['width_medium']}px;
            }}
        """
    
    def get_list_style(self):
        return f"""
            QListWidget {{
                background-color: {self.colors['background_secondary']};
                border: {self.borders['width_thin']}px solid {self.colors['border']};
                border-radius: {self.borders['radius_md']}px;
                padding: {self.spacing['xs']}px;
            }}
            QListWidget::item {{
                padding: {self.spacing['md']}px;
                border-radius: {self.borders['radius_sm']}px;
                margin: {self.spacing['xs']}px 0px;
                
            }}
            QListWidget::item:hover {{
                background-color: {self.colors['surface']};
            }}
            QListWidget::item:selected {{
                background-color: {self.colors['surface_selected']};
                color: {self.colors['text_inverse']};
            }}
        """

current_theme = None

def get_current_theme():
    global current_theme
    if current_theme is None:
        current_theme = Theme("Dark")
    return current_theme
