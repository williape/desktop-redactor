from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QToolButton, QFrame, QSizePolicy, QLabel)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont

class CollapsibleBox(QWidget):
    """A collapsible widget that can show/hide its content"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_button = QToolButton()
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.clicked.connect(self.on_pressed)
        
        # Style the toggle button
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
                text-align: left;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        
        self.content_area = QFrame()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setFrameShape(QFrame.Box)
        self.content_area.setFrameShadow(QFrame.Raised)
        self.content_area.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
                margin-top: 2px;
            }
        """)
        
        self.toggle_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.toggle_animation.setDuration(300)
        self.toggle_animation.setEasingCurve(QEasingCurve.InOutQuart)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_area.setLayout(self.content_layout)
        
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.toggle_animation.setDirection(
            QPropertyAnimation.Forward if checked else QPropertyAnimation.Backward
        )
        self.toggle_animation.start()
        self.toggled.emit(checked)
        
    def set_content_layout(self, widget_or_layout):
        """Set the layout or widget for the collapsible content"""
        # Clear existing content
        self._clear_content()
                
        # Add new layout/widget
        if hasattr(widget_or_layout, 'addWidget') and hasattr(widget_or_layout, 'count'):  # It's a layout
            container = QWidget()
            container.setLayout(widget_or_layout)
            self.content_layout.addWidget(container)
        else:  # It's a widget
            self.content_layout.addWidget(widget_or_layout)
            
        # Update animation heights
        self._update_animation_heights()
    
    def _clear_content(self):
        """Clear existing content from the layout"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
    
    def _clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
    
    def _update_animation_heights(self):
        """Update the animation start and end values based on content"""
        # Force layout update
        self.content_area.updateGeometry()
        
        # Get the size hint with content visible
        was_collapsed = self.content_area.maximumHeight() == 0
        if was_collapsed:
            self.content_area.setMaximumHeight(16777215)
        
        # Process events to ensure layout is updated
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Get the actual content height
        content_height = self.content_area.sizeHint().height()
        
        # Restore collapsed state if it was collapsed
        if was_collapsed:
            self.content_area.setMaximumHeight(0)
        
        # Set animation values
        self.toggle_animation.setStartValue(0)
        self.toggle_animation.setEndValue(max(content_height, 100))  # Minimum height
        
    def add_widget(self, widget):
        """Add a widget to the collapsible content"""
        self.content_layout.addWidget(widget)
        self._update_animation_heights()
        
    def set_expanded(self, expanded):
        """Programmatically expand or collapse"""
        self.toggle_button.setChecked(expanded)
        self.on_pressed()