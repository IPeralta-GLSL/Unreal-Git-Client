from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QApplication, QGraphicsDropShadowEffect,
                             QSizeGrip, QWidget)
from PyQt6.QtCore import Qt, QPoint, QSize, QEvent
from PyQt6.QtGui import QFont, QCursor, QColor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr


class AIChatPopup(QFrame):
    """Floating popup for AI Chat assistant."""
    
    def __init__(self, plugin_manager, repo_path, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.repo_path = repo_path
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        self.chat_widget = None
        self._drag_pos = None
        
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.load_chat_widget()
        
    def setup_ui(self):
        theme = self.theme
        
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(380, 500)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Content frame
        self.content = QFrame()
        self.content.setObjectName("popupContent")
        self.content.setStyleSheet(f"""
            QFrame#popupContent {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 12px;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.content.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header (draggable)
        header = QFrame()
        header.setObjectName("chatHeader")
        header.setStyleSheet(f"""
            QFrame#chatHeader {{
                background-color: {theme.colors['surface']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        header.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 10, 10)
        header_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_icon("lightbulb", size=18).pixmap(18, 18))
        header_layout.addWidget(icon_label)
        
        # Title
        title = QLabel("AI Assistant")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.colors['text_secondary']};
                border: none;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {theme.colors['text']};
                background-color: {theme.colors['surface_hover']};
                border-radius: 12px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        content_layout.addWidget(header)
        
        # Chat widget container
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet(f"background-color: {theme.colors['background']};")
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_container_layout.setSpacing(0)
        
        content_layout.addWidget(self.chat_container, 1)
        
        main_layout.addWidget(self.content)
    
    def _header_mouse_press(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def _header_mouse_move(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def load_chat_widget(self):
        """Load the chat widget from the AI assistant plugin."""
        if not self.plugin_manager or not self.repo_path:
            self._show_no_plugin_message()
            return
        
        plugins = self.plugin_manager.get_all_plugins()
        for name, plugin in plugins.items():
            if hasattr(plugin, 'get_sidebar_widget'):
                widget = plugin.get_sidebar_widget(self.repo_path)
                if widget:
                    self.chat_widget = widget
                    self.chat_container_layout.addWidget(widget)
                    return
        
        self._show_no_plugin_message()
    
    def _show_no_plugin_message(self):
        """Show message when no AI plugin is available."""
        theme = self.theme
        
        msg = QLabel("AI Assistant not available")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {theme.colors['text_secondary']}; padding: 40px;")
        self.chat_container_layout.addWidget(msg)
    
    def show_at(self, global_pos: QPoint):
        """Show popup at specified position."""
        self.adjustSize()
        
        screen = QApplication.screenAt(global_pos)
        if screen:
            screen_rect = screen.availableGeometry()
        else:
            screen_rect = QApplication.primaryScreen().availableGeometry()
        
        # Position to the left of the button, aligned with bottom
        x = global_pos.x() - self.width()
        y = global_pos.y() - self.height() + 40
        
        # Keep within screen
        if x < screen_rect.left():
            x = global_pos.x() + 10
        if y < screen_rect.top():
            y = screen_rect.top() + 10
        if y + self.height() > screen_rect.bottom():
            y = screen_rect.bottom() - self.height() - 10
        
        self.move(x, y)
        self.show()
        
        # Focus the input field if available
        if self.chat_widget and hasattr(self.chat_widget, 'input_field'):
            self.chat_widget.input_field.setFocus()
    
    def keyPressEvent(self, event):
        """Handle key press - close on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
