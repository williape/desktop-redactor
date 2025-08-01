"""
List Widget for Presidio Desktop Redactor

Tag-based UI widget for managing allowlists and denylists.
Provides intuitive interface for adding, removing, and organizing list entries.
"""

import os
import sys
from typing import List, Set, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QScrollArea, QFileDialog,
    QMessageBox, QMenu, QAction, QSizePolicy, QSpacerItem,
    QToolButton, QDialog, QDialogButtonBox, QTextEdit, QLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QTimer, QSize, QRect, QPoint
from PyQt5.QtGui import QFont, QPixmap, QDragEnterEvent, QDropEvent, QPalette


class TagWidget(QFrame):
    """Individual tag widget with remove button"""
    
    remove_requested = pyqtSignal(str)  # Emitted when remove button is clicked
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the tag UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            TagWidget {
                background-color: #e1f5fe;
                border: 1px solid #81d4fa;
                border-radius: 12px;
                padding: 2px;
                margin: 2px;
            }
            TagWidget:hover {
                background-color: #b3e5fc;
                border-color: #4fc3f7;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(4)
        
        # Tag text label
        self.label = QLabel(self.text)
        self.label.setStyleSheet("QLabel { border: none; background: transparent; }")
        layout.addWidget(self.label)
        
        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5722;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #d84315;
            }
            QPushButton:pressed {
                background-color: #bf360c;
            }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.text))
        layout.addWidget(self.remove_btn)
        
        self.setLayout(layout)


class FlowLayout(QLayout):
    """Custom layout that flows items left to right, wrapping to new lines"""
    
    def __init__(self, parent=None, margin=0, spacing=2):
        super().__init__(parent)
        self.item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
    
    def addItem(self, item):
        self.item_list.append(item)
    
    def count(self):
        return len(self.item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self.do_layout(None, width, True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect, rect.width(), False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size
    
    def do_layout(self, rect, width, test_only):
        x = self.contentsMargins().left()
        y = self.contentsMargins().top()
        line_height = 0
        
        for item in self.item_list:
            widget = item.widget()
            space_x = self.spacing()
            space_y = self.spacing()
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > width and line_height > 0:
                x = self.contentsMargins().left()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - self.contentsMargins().top()


class ListWidget(QWidget):
    """
    Widget for managing lists of words/phrases with tag-based UI
    
    Features:
    - Add/remove entries with visual feedback
    - Import/export functionality
    - Search and filter
    - Drag and drop support for files
    """
    
    list_changed = pyqtSignal()  # Emitted when list contents change
    
    def __init__(self, title: str = "List", allow_entity_types: bool = False, parent=None):
        super().__init__(parent)
        self.title = title
        self.allow_entity_types = allow_entity_types  # For denylist with entity types
        self.entries: Set[str] = set()
        self.entry_data: dict = {}  # For storing additional data like entity types
        
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Title and controls header
        header_layout = QHBoxLayout()
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        # Entry count label
        self.count_label = QLabel("(0 entries)")
        self.count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.import_btn = QToolButton()
        self.import_btn.setText("📥")
        self.import_btn.setToolTip("Import from file")
        self.import_btn.clicked.connect(self.import_from_file)
        header_layout.addWidget(self.import_btn)
        
        self.export_btn = QToolButton()
        self.export_btn.setText("📤")
        self.export_btn.setToolTip("Export to file")
        self.export_btn.clicked.connect(self.export_to_file)
        header_layout.addWidget(self.export_btn)
        
        self.clear_btn = QToolButton()
        self.clear_btn.setText("🗑️")
        self.clear_btn.setToolTip("Clear all entries")
        self.clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Add entry input
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type and press Enter to add...")
        self.input_field.returnPressed.connect(self.add_entry_from_input)
        input_layout.addWidget(self.input_field)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_entry_from_input)
        input_layout.addWidget(self.add_btn)
        
        layout.addLayout(input_layout)
        
        # Tags display area
        self.setup_tags_area(layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Timer for status messages
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(lambda: self.status_label.setText(""))
        
        self.update_count()
    
    def setup_tags_area(self, parent_layout):
        """Setup the scrollable tags display area"""
        # Create scroll area for tags
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(100)
        self.scroll_area.setMaximumHeight(200)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """)
        
        # Widget to contain tags
        self.tags_widget = QWidget()
        self.tags_layout = FlowLayout(self.tags_widget)
        self.tags_widget.setLayout(self.tags_layout)
        
        self.scroll_area.setWidget(self.tags_widget)
        parent_layout.addWidget(self.scroll_area)
    
    def add_entry(self, text: str, entity_type: str = None) -> bool:
        """
        Add entry to the list
        
        Args:
            text: Text to add
            entity_type: Entity type (for denylist entries)
            
        Returns:
            True if added successfully, False if already exists or invalid
        """
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        if not text:
            return False
        
        # Check for duplicates
        if text in self.entries:
            self.show_status(f"'{text}' already exists", is_error=True)
            return False
        
        # Add to entries
        self.entries.add(text)
        
        # Store additional data if provided
        if entity_type and self.allow_entity_types:
            self.entry_data[text] = {"entity_type": entity_type}
        
        # Create and add tag widget
        tag_widget = TagWidget(text)
        tag_widget.remove_requested.connect(self.remove_entry)
        self.tags_layout.addWidget(tag_widget)
        
        self.update_count()
        self.show_status(f"Added '{text}'")
        self.list_changed.emit()
        return True
    
    def remove_entry(self, text: str) -> bool:
        """
        Remove entry from the list
        
        Args:
            text: Text to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if text not in self.entries:
            return False
        
        self.entries.remove(text)
        if text in self.entry_data:
            del self.entry_data[text]
        
        # Remove tag widget
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                tag_widget = item.widget()
                if isinstance(tag_widget, TagWidget) and tag_widget.text == text:
                    self.tags_layout.removeWidget(tag_widget)
                    tag_widget.deleteLater()
                    break
        
        self.update_count()
        self.show_status(f"Removed '{text}'")
        self.list_changed.emit()
        return True
    
    def add_entry_from_input(self):
        """Add entry from input field"""
        text = self.input_field.text().strip()
        if text:
            if self.add_entry(text):
                self.input_field.clear()
    
    def clear_all(self):
        """Clear all entries after confirmation"""
        if not self.entries:
            return
        
        reply = QMessageBox.question(
            self, "Clear All", 
            f"Are you sure you want to clear all {len(self.entries)} entries?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.entries.clear()
            self.entry_data.clear()
            
            # Remove all tag widgets
            while self.tags_layout.count():
                item = self.tags_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            
            self.update_count()
            self.show_status("All entries cleared")
            self.list_changed.emit()
    
    def get_entries(self) -> List[str]:
        """Get list of all entries"""
        return sorted(list(self.entries))
    
    def set_entries(self, entries: List[str]) -> None:
        """
        Set entries from list
        
        Args:
            entries: List of strings to set as entries
        """
        self.clear_all_silent()
        for entry in entries:
            if isinstance(entry, str):
                self.add_entry(entry)
    
    def clear_all_silent(self):
        """Clear all entries without confirmation or signals"""
        self.entries.clear()
        self.entry_data.clear()
        
        # Remove all tag widgets
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        self.update_count()
    
    def import_from_file(self):
        """Import entries from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Import {self.title}",
            "", "Text files (*.txt);;CSV files (*.csv);;JSON files (*.json);;All files (*)"
        )
        
        if file_path:
            try:
                imported_count = self._import_from_file_path(file_path)
                self.show_status(f"Imported {imported_count} entries from {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import file:\n{str(e)}")
    
    def _import_from_file_path(self, file_path: str) -> int:
        """Import from specific file path"""
        imported_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.lower().endswith('.txt'):
                    # Simple text file, one entry per line
                    for line in f:
                        line = line.strip()
                        if line and self.add_entry(line):
                            imported_count += 1
                
                elif file_path.lower().endswith('.csv'):
                    # CSV file, assume first column is the word
                    import csv
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].strip():
                            if self.add_entry(row[0].strip()):
                                imported_count += 1
                
                elif file_path.lower().endswith('.json'):
                    # JSON file
                    import json
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        # Simple list of strings
                        for item in data:
                            if isinstance(item, str) and self.add_entry(item):
                                imported_count += 1
                    elif isinstance(data, dict):
                        # Handle various JSON formats
                        for key in ['words', 'entries', 'allowlist', 'denylist']:
                            if key in data:
                                if isinstance(data[key], list):
                                    for item in data[key]:
                                        if isinstance(item, str) and self.add_entry(item):
                                            imported_count += 1
                                        elif isinstance(item, dict) and 'word' in item:
                                            if self.add_entry(item['word']):
                                                imported_count += 1
                                break
        
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
        
        return imported_count
    
    def export_to_file(self):
        """Export entries to file"""
        if not self.entries:
            QMessageBox.information(self, "Export", "No entries to export")
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, f"Export {self.title}",
            f"{self.title.lower().replace(' ', '_')}_export.txt",
            "Text files (*.txt);;CSV files (*.csv);;JSON files (*.json)"
        )
        
        if file_path:
            try:
                self._export_to_file_path(file_path, selected_filter)
                self.show_status(f"Exported {len(self.entries)} entries to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export file:\n{str(e)}")
    
    def _export_to_file_path(self, file_path: str, file_filter: str):
        """Export to specific file path"""
        entries_list = self.get_entries()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if 'Text files' in file_filter or file_path.lower().endswith('.txt'):
                # Simple text file
                for entry in entries_list:
                    f.write(f"{entry}\n")
            
            elif 'CSV files' in file_filter or file_path.lower().endswith('.csv'):
                # CSV file
                import csv
                writer = csv.writer(f)
                writer.writerow(['word'])  # Header
                for entry in entries_list:
                    writer.writerow([entry])
            
            elif 'JSON files' in file_filter or file_path.lower().endswith('.json'):
                # JSON file
                import json
                export_data = {
                    'entries': entries_list,
                    'count': len(entries_list),
                    'exported_at': __import__('datetime').datetime.now().isoformat()
                }
                json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.txt', '.csv', '.json')):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            try:
                imported_count = self._import_from_file_path(file_path)
                self.show_status(f"Imported {imported_count} entries from dropped file")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import dropped file:\n{str(e)}")
    
    def update_count(self):
        """Update the entry count display"""
        count = len(self.entries)
        self.count_label.setText(f"({count} {'entry' if count == 1 else 'entries'})")
        
        # Update export button state
        self.export_btn.setEnabled(count > 0)
        self.clear_btn.setEnabled(count > 0)
    
    def show_status(self, message: str, is_error: bool = False):
        """Show status message temporarily"""
        if is_error:
            self.status_label.setStyleSheet("color: #f44336; font-size: 9px;")
        else:
            self.status_label.setStyleSheet("color: #4caf50; font-size: 9px;")
        
        self.status_label.setText(message)
        self.status_timer.start(3000)  # Clear after 3 seconds