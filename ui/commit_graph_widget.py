from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPainterPath, QPixmap
import math

class CommitGraphWidget(QWidget):
    commit_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.commits = []
        self.colors = [
            QColor("#007acc"),
            QColor("#4ec9b0"),
            QColor("#dcdcaa"),
            QColor("#ce9178"),
            QColor("#c586c0"),
            QColor("#9cdcfe"),
            QColor("#b5cea8"),
            QColor("#f48771"),
        ]
        self.branch_colors = {}
        self.node_radius = 8
        self.row_height = 70
        self.left_margin = 20
        self.graph_width = 200
        self.avatar_size = 32
        self.setMinimumHeight(400)
        self.selected_commit = None
        self.avatars = {}
        
    def set_commits(self, commits):
        self.commits = commits
        self.branch_colors = {}
        self.calculate_positions()
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
            
    def paintEvent(self, event):
        if not self.commits:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for i, commit in enumerate(self.commits):
            self.draw_commit(painter, commit, i)
            
    def draw_commit(self, painter, commit, index):
        column = commit.get('column', 0)
        row = commit.get('row', index)
        branch = commit.get('branch', 'main')
        
        x = self.left_margin + column * 30
        y = 30 + row * self.row_height
        
        color = self.branch_colors.get(branch, self.colors[0])
        
        if index < len(self.commits) - 1:
            next_commit = self.commits[index + 1]
            next_column = next_commit.get('column', 0)
            next_y = 30 + (index + 1) * self.row_height
            
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            if column == next_column:
                painter.drawLine(x, y + self.node_radius, x, next_y - self.node_radius)
            else:
                next_x = self.left_margin + next_column * 30
                path = QPainterPath()
                path.moveTo(x, y + self.node_radius)
                
                ctrl_y = y + (next_y - y) / 2
                path.cubicTo(x, ctrl_y, next_x, ctrl_y, next_x, next_y - self.node_radius)
                painter.drawPath(path)
        
        is_selected = self.selected_commit == commit.get('hash', '')
        
        if is_selected:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - self.node_radius - 2, y - self.node_radius - 2, 
                              (self.node_radius + 2) * 2, (self.node_radius + 2) * 2)
        else:
            painter.setPen(QPen(color.darker(120), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - self.node_radius, y - self.node_radius, 
                              self.node_radius * 2, self.node_radius * 2)
        
        email = commit.get('email', '')
        avatar_x = self.graph_width - self.avatar_size - 10
        avatar_y = y - self.avatar_size // 2
        
        if email in self.avatars:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addEllipse(avatar_x, avatar_y, self.avatar_size, self.avatar_size)
            painter.setClipPath(path)
            
            painter.drawPixmap(avatar_x, avatar_y, self.avatars[email])
            painter.restore()
        else:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            author = commit.get('author', 'Unknown')
            colors = ['#4ec9b0', '#007acc', '#c586c0', '#dcdcaa', '#ce9178', '#4fc1ff', '#b5cea8']
            color_index = sum(ord(c) for c in author) % len(colors)
            bg_color = QColor(colors[color_index])
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(avatar_x, avatar_y, self.avatar_size, self.avatar_size)
            
            initials = self.get_initials(author)
            painter.setPen(QColor('#ffffff'))
            font = QFont('Arial', 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(avatar_x, avatar_y, self.avatar_size, self.avatar_size, 
                           Qt.AlignmentFlag.AlignCenter, initials)
            painter.restore()
        
        text_x = self.graph_width + 10
        text_y = y - 20
        
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        message = commit.get('message', 'No message')[:60]
        if len(commit.get('message', '')) > 60:
            message += "..."
        painter.drawText(text_x, text_y, message)
        
        painter.setPen(QPen(QColor("#888888")))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        author = commit.get('author', 'Unknown')
        date = commit.get('date', '')
        hash_short = commit.get('hash', '')[:7]
        
        info_text = f"{author}  •  {date}  •  {hash_short}"
        painter.drawText(text_x, text_y + 20, info_text)
    
    def get_initials(self, name):
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) > 0:
            return parts[0][0].upper()
        return "?"
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for commit in self.commits:
                column = commit.get('column', 0)
                row = commit.get('row', 0)
                
                x = self.left_margin + column * 30
                y = 30 + row * self.row_height
                
                distance = math.sqrt((event.pos().x() - x)**2 + (event.pos().y() - y)**2)
                
                if distance <= self.node_radius * 2:
                    self.selected_commit = commit.get('hash', '')
                    self.commit_clicked.emit(commit.get('hash', ''))
                    self.update()
                    return
                    
                text_x = self.graph_width
                text_y = y - 25
                text_rect = QRect(text_x, text_y, self.width() - text_x, 50)
                
                if text_rect.contains(event.pos()):
                    self.selected_commit = commit.get('hash', '')
                    self.commit_clicked.emit(commit.get('hash', ''))
                    self.update()
                    return
    
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        height = max(400, len(self.commits) * self.row_height + 60)
        return QSize(800, height)
    
    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(600, 400)
