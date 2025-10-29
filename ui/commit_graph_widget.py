from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPainterPath
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
        self.row_height = 60
        self.left_margin = 20
        self.graph_width = 200
        self.setMinimumHeight(400)
        self.selected_commit = None
        
    def set_commits(self, commits):
        self.commits = commits
        self.branch_colors = {}
        self.calculate_positions()
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
        
        text_x = self.graph_width
        text_y = y - 15
        
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
