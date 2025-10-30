from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QAbstractAnimation, QPoint, QRect, QVariantAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QPushButton, QWidget
from PyQt6.QtGui import QColor

class AnimationManager:
    @staticmethod
    def fade_in(widget, duration=200):
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        
        widget._fade_animation = animation
        return animation
    
    @staticmethod
    def fade_out(widget, duration=200):
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        
        widget._fade_animation = animation
        return animation
    
    @staticmethod
    def slide_in(widget, start_pos, end_pos, duration=250):
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(QPoint(start_pos[0], start_pos[1]))
        animation.setEndValue(QPoint(end_pos[0], end_pos[1]))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        
        widget._slide_animation = animation
        return animation
    
    @staticmethod
    def expand(widget, start_rect, end_rect, duration=250):
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(QRect(*start_rect))
        animation.setEndValue(QRect(*end_rect))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        
        widget._expand_animation = animation
        return animation
    
    @staticmethod
    def apply_hover_effect(button):
        if not isinstance(button, QPushButton):
            return
        
        original_style = button.styleSheet()
        
        def on_enter(event):
            button.setGraphicsEffect(None)
            QPushButton.enterEvent(button, event)
        
        def on_leave(event):
            button.setGraphicsEffect(None)
            QPushButton.leaveEvent(button, event)
        
        button.enterEvent = on_enter
        button.leaveEvent = on_leave
    
    @staticmethod
    def create_fade_group(widgets, duration=200, delay=50):
        group = QSequentialAnimationGroup()
        
        for i, widget in enumerate(widgets):
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)
            
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            if i > 0:
                pause = QPropertyAnimation(effect, b"opacity")
                pause.setDuration(delay)
                group.addAnimation(pause)
            
            group.addAnimation(animation)
        
        return group
