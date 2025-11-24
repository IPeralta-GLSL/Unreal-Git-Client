from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPainterPath, QPixmap
from ui.theme import get_current_theme
import math

class CommitGraphWidget(QWidget):
    commit_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.commits = []
        
        theme = get_current_theme()
        self.colors = [QColor(c) for c in theme.colors.get('graph_colors', [])]
        if not self.colors:
            self.colors = [
                QColor("#007acc"), QColor("#4ec9b0"), QColor("#dcdcaa"), QColor("#ce9178"),
                QColor("#c586c0"), QColor("#9cdcfe"), QColor("#b5cea8"), QColor("#f48771")
            ]
            
        self.branch_colors = {}
        self.node_radius = 6
        self.row_height = 55
        self.left_margin = 20
        self.graph_width = 130
        self.avatar_size = 36
        self.selected_commit = None
        self.hovered_commit = None
        self.avatars = {}
        
    def set_commits(self, commits):
        self.commits = commits
        self.branch_colors = {}
        self.calculate_positions()
        
        height = max(400, len(self.commits) * self.row_height + 60)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        
        self.update()
    
    def set_avatar(self, email, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(self.avatar_size, self.avatar_size, 
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
            self.avatars[email] = scaled
            self.update()
        
    def calculate_positions(self):
        columns = {}
        next_column = 0
        
        for i, commit in enumerate(self.commits):
            branch = commit.get('branch', 'main')
            
            if branch not in columns:
                if branch not in self.branch_colors:
                    color_index = len(self.branch_colors) % len(self.colors)
                    self.branch_colors[branch] = self.colors[color_index]
                columns[branch] = next_column
                next_column += 1
            
            commit['column'] = columns[branch]
            commit['row'] = i
            
    def mouseMoveEvent(self, event):
        y = event.pos().y()
        # Calculate row based on y position
        # y = 30 + row * row_height
        # row = (y - 30 + row_height/2) / row_height
        row = int((y - 30 + self.row_height / 2) / self.row_height)
        
        hovered = None
        if 0 <= row < len(self.commits):
            hovered = self.commits[row].get('hash')
            
        if self.hovered_commit != hovered:
            self.hovered_commit = hovered
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_commit = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        if not self.commits:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw backgrounds first
        for i, commit in enumerate(self.commits):
            self.draw_row_background(painter, commit, i)

        # Draw graph lines
        for i, commit in enumerate(self.commits):
            self.draw_graph_lines(painter, commit, i)

        # Draw nodes and content
        for i, commit in enumerate(self.commits):
            self.draw_commit_node(painter, commit, i)
            self.draw_commit_content(painter, commit, i)
            
    def draw_row_background(self, painter, commit, index):
        row = commit.get('row', index)
        y = 30 + row * self.row_height
        rect = QRect(0, int(y - self.row_height/2), self.width(), self.row_height)
        
        theme = get_current_theme()
        # Use theme colors for selection/hover
        if self.selected_commit == commit.get('hash'):
            # Use surface_selected color with transparency
            c = QColor(theme.colors['surface_selected'])
            c.setAlpha(40)
            painter.fillRect(rect, c)
        elif self.hovered_commit == commit.get('hash'):
            # Use text color with very low opacity for hover
            c = QColor(theme.colors['text'])
            c.setAlpha(15)
            painter.fillRect(rect, c)

    def draw_graph_lines(self, painter, commit, index):
        column = commit.get('column', 0)
        row = commit.get('row', index)
        branch = commit.get('branch', 'main')
        
        x = self.left_margin + column * 24  # Reduced spacing between lines
        y = 30 + row * self.row_height
        
        color = self.branch_colors.get(branch, self.colors[0])
        
        if index < len(self.commits) - 1:
            next_commit = self.commits[index + 1]
            next_column = next_commit.get('column', 0)
            next_y = 30 + (index + 1) * self.row_height
            
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            if column == next_column:
                painter.drawLine(int(x), int(y), int(x), int(next_y))
            else:
                next_x = self.left_margin + next_column * 24
                path = QPainterPath()
                path.moveTo(x, y)
                
                ctrl_y = y + (next_y - y) / 2
                path.cubicTo(x, ctrl_y, next_x, ctrl_y, next_x, next_y)
                painter.drawPath(path)

    def draw_commit_node(self, painter, commit, index):
        column = commit.get('column', 0)
        row = commit.get('row', index)
        branch = commit.get('branch', 'main')
        
        x = self.left_margin + column * 24
        y = 30 + row * self.row_height
        
        color = self.branch_colors.get(branch, self.colors[0])
        is_selected = self.selected_commit == commit.get('hash', '')
        
        if is_selected:
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPoint(int(x), int(y)), self.node_radius + 1, self.node_radius + 1)
        else:
            painter.setPen(QPen(color.darker(120), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPoint(int(x), int(y)), self.node_radius, self.node_radius)

    def draw_commit_content(self, painter, commit, index):
        row = commit.get('row', index)
        y = 30 + row * self.row_height
        
        # Avatar
        email = commit.get('email', '')
        avatar_x = self.graph_width - self.avatar_size - 10
        avatar_y = int(y - self.avatar_size / 2)
        
        if email in self.avatars:
            painter.save()
            path = QPainterPath()
            path.addEllipse(avatar_x, avatar_y, self.avatar_size, self.avatar_size)
            painter.setClipPath(path)
            painter.drawPixmap(avatar_x, avatar_y, self.avatars[email])
            painter.restore()
        else:
            painter.save()
            author = commit.get('author', 'Unknown')
            colors = ['#4ec9b0', '#007acc', '#c586c0', '#dcdcaa', '#ce9178', '#4fc1ff', '#b5cea8']
            color_index = sum(ord(c) for c in author) % len(colors)
            bg_color = QColor(colors[color_index])
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(avatar_x, avatar_y, self.avatar_size, self.avatar_size)
            
            initials = self.get_initials(author)
            painter.setPen(QColor('#ffffff'))
            font = QFont('Segoe UI', 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(avatar_x, avatar_y, self.avatar_size, self.avatar_size, 
                           Qt.AlignmentFlag.AlignCenter, initials)
            painter.restore()
        
        # Text Content
        text_x = self.graph_width + 10
        
        # Message
        text_color = self.palette().color(self.palette().ColorRole.WindowText)
        painter.setPen(QPen(text_color))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        message = commit.get('message', 'No message')
        # Simple truncation
        metrics = painter.fontMetrics()
        elided_message = metrics.elidedText(message, Qt.TextElideMode.ElideRight, self.width() - text_x - 20)
        painter.drawText(text_x, int(y - 5), elided_message)
        
        # Meta info (Author, Date, Hash)
        secondary_color = self.palette().color(self.palette().ColorRole.Text)
        secondary_color.setAlpha(180) # Make it slightly dimmer
        painter.setPen(QPen(secondary_color))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        author = commit.get('author', 'Unknown')
        date = commit.get('date', '')
        hash_short = commit.get('hash', '')[:7]
        
        # Draw author
        author_rect = metrics.boundingRect(author)
        painter.drawText(text_x, int(y + 15), author)
        
        # Draw dot separator
        dot_x = text_x + metrics.horizontalAdvance(author) + 8
        painter.drawText(dot_x, int(y + 15), "•")
        
        # Draw date
        date_x = dot_x + 12
        painter.drawText(date_x, int(y + 15), date)
        
        # Draw hash (right aligned or after date)
        # Let's put hash at the end with a different style maybe?
        # Or keep the current format but cleaner
        
        hash_x = date_x + metrics.horizontalAdvance(date) + 12
        painter.drawText(hash_x, int(y + 15), "•")
        
        hash_final_x = hash_x + 12
        
        # Draw hash with monospace font
        painter.save()
        mono_font = QFont("Consolas", 9)
        painter.setFont(mono_font)
        
        # Use theme primary color or a specific hash color
        theme = get_current_theme()
        hash_color = QColor(theme.colors.get('text_link', '#4ec9b0'))
        painter.setPen(QPen(hash_color)) 
        
        painter.drawText(hash_final_x, int(y + 15), hash_short)
        painter.restore()

    def draw_commit(self, painter, commit, index):
        # Legacy method kept for compatibility if needed, but paintEvent now calls specific methods
        pass
    
    def get_initials(self, name):
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) > 0:
            return parts[0][0].upper()
        return "?"
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for row click first (easier and covers everything)
            y = event.pos().y()
            row = int((y - 30 + self.row_height / 2) / self.row_height)
            
            if 0 <= row < len(self.commits):
                commit = self.commits[row]
                self.selected_commit = commit.get('hash', '')
                self.commit_clicked.emit(commit.get('hash', ''))
                self.update()
                return

            # Fallback to specific node click if needed (though row click covers it)
            for commit in self.commits:
                column = commit.get('column', 0)
                row = commit.get('row', 0)
                
                x = self.left_margin + column * 24
                y = 30 + row * self.row_height
                
                distance = math.sqrt((event.pos().x() - x)**2 + (event.pos().y() - y)**2)
                
                if distance <= self.node_radius * 2:
                    self.selected_commit = commit.get('hash', '')
                    self.commit_clicked.emit(commit.get('hash', ''))
                    self.update()
                    return
    
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        height = max(400, len(self.commits) * self.row_height + 60)
        return QSize(self.width(), height)
    
    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        height = max(400, len(self.commits) * self.row_height + 60)
        return QSize(600, height)
