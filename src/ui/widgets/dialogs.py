from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QCheckBox, QDialogButtonBox,
                            QTreeWidget, QTreeWidgetItem, QLabel)
from PyQt5.QtCore import Qt
from typing import List, Any
import json

class ColumnSelectionDialog(QDialog):
    """Dialog for selecting CSV columns to process"""
    
    def __init__(self, columns: List[str], parent=None):
        super().__init__(parent)
        self.columns = columns
        self.selected_columns = columns.copy()
        self.checkboxes = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Select Columns to Process")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # Instructions
        layout.addWidget(QLabel("Select which columns to process for PII:"))
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self.select_all)
        clear_all = QPushButton("Clear All")
        clear_all.clicked.connect(self.clear_all)
        button_layout.addWidget(select_all)
        button_layout.addWidget(clear_all)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Column checkboxes
        for col in self.columns:
            cb = QCheckBox(col)
            cb.setChecked(True)
            self.checkboxes.append(cb)
            layout.addWidget(cb)
            
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def select_all(self):
        """Select all columns"""
        for cb in self.checkboxes:
            cb.setChecked(True)
            
    def clear_all(self):
        """Clear all selections"""
        for cb in self.checkboxes:
            cb.setChecked(False)
            
    def get_selected_columns(self) -> List[str]:
        """Get list of selected column names"""
        return [
            self.columns[i] for i, cb in enumerate(self.checkboxes)
            if cb.isChecked()
        ]

class JsonTreeWidget(QTreeWidget):
    """Tree widget for JSON path selection"""
    
    def __init__(self):
        super().__init__()
        self.setHeaderLabel("JSON Structure (select paths to process)")
        self.itemChanged.connect(self.handle_item_change)
        
        # Improve visual styling for better checkbox visibility
        self.setStyleSheet("""
            QTreeWidget {
                font-size: 13px;
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTreeWidget::item:hover {
                background-color: #f5f5f5;
            }
            QTreeWidget::indicator {
                width: 18px;
                height: 18px;
            }
            QTreeWidget::indicator:unchecked {
                background-color: white;
                border: 2px solid #bbb;
                border-radius: 3px;
            }
            QTreeWidget::indicator:checked {
                background-color: #4caf50;
                border: 2px solid #4caf50;
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggMkw0IDZMMiA0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QTreeWidget::indicator:indeterminate {
                background-color: #ff9800;
                border: 2px solid #ff9800;
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIgNUw4IDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """)
        
    def load_json_structure(self, data: Any, parent=None, path=""):
        """Recursively load JSON structure into tree"""
        self.clear()
        if parent is None:
            parent = self.invisibleRootItem()
            
        self._build_tree(data, parent, path)
        self.expandAll()
        
    def _build_tree(self, data: Any, parent, path=""):
        """Recursively build tree structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                display_text = f"📁 {key}: {self._get_type_description(value)}" if isinstance(value, (dict, list)) else f"📄 {key}: {self._get_type_description(value)}"
                item = QTreeWidgetItem(parent, [display_text])
                item.setData(0, Qt.UserRole, current_path)
                item.setCheckState(0, Qt.Checked)
                
                # Add tooltip with path information
                item.setToolTip(0, f"Path: {current_path}\nType: {type(value).__name__}")
                
                # Recursively add children for nested structures
                if isinstance(value, (dict, list)):
                    self._build_tree(value, item, current_path)
                    
        elif isinstance(data, list) and data:
            # Show array structure with first element as example
            display_text = f"📋 [array of {len(data)} items]"
            item = QTreeWidgetItem(parent, [display_text])
            array_path = f"{path}[*]" if path else "[*]"
            item.setData(0, Qt.UserRole, array_path)
            item.setCheckState(0, Qt.Checked)
            item.setToolTip(0, f"Path: {array_path}\nType: array with {len(data)} items")
            
            # Show structure of first element
            if data:
                self._build_tree(data[0], item, f"{path}[0]" if path else "[0]")
                
    def _get_type_description(self, value):
        """Get user-friendly type description"""
        if isinstance(value, str):
            return f"string: '{value[:30]}...'" if len(str(value)) > 30 else f"string: '{value}'"
        elif isinstance(value, (int, float)):
            return f"number: {value}"
        elif isinstance(value, bool):
            return f"boolean: {value}"
        elif isinstance(value, dict):
            return f"object ({len(value)} keys)"
        elif isinstance(value, list):
            return f"array ({len(value)} items)"
        elif value is None:
            return "null"
        else:
            return str(type(value).__name__)
                
    def handle_item_change(self, item, column):
        """Handle checkbox state changes"""
        # Auto-check/uncheck children
        self._update_children(item, item.checkState(column))
        # Update parent if needed
        self._update_parent(item)
        
    def _update_children(self, item, state):
        """Update all child items to match parent state"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._update_children(child, state)
            
    def _update_parent(self, item):
        """Update parent state based on children"""
        parent = item.parent()
        if not parent:
            return
            
        # Check if all siblings have same state
        checked_count = 0
        total_count = parent.childCount()
        
        for i in range(total_count):
            if parent.child(i).checkState(0) == Qt.Checked:
                checked_count += 1
                
        if checked_count == 0:
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count:
            parent.setCheckState(0, Qt.Checked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)
            
        self._update_parent(parent)
        
    def get_selected_paths(self) -> List[str]:
        """Get all checked paths"""
        paths = []
        
        def collect_paths(item):
            if item.checkState(0) == Qt.Checked:
                path = item.data(0, Qt.UserRole)
                if path and not self._has_checked_children(item):
                    # Only include leaf nodes or nodes without checked children
                    paths.append(path)
            
            for i in range(item.childCount()):
                collect_paths(item.child(i))
                
        collect_paths(self.invisibleRootItem())
        return paths
        
    def _has_checked_children(self, item):
        """Check if item has any checked children"""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.checkState(0) == Qt.Checked:
                return True
        return False
        
    def select_all_items(self):
        """Select all items in the tree"""
        def set_all_checked(item):
            item.setCheckState(0, Qt.Checked)
            for i in range(item.childCount()):
                set_all_checked(item.child(i))
        
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            set_all_checked(root.child(i))
            
    def clear_all_items(self):
        """Clear all item selections"""
        def set_all_unchecked(item):
            item.setCheckState(0, Qt.Unchecked)
            for i in range(item.childCount()):
                set_all_unchecked(item.child(i))
        
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            set_all_unchecked(root.child(i))
            
    def select_text_fields_only(self):
        """Select only text/string fields, uncheck others"""
        def check_text_fields(item):
            # Get the display text to determine if this is a text field
            text = item.text(0)
            if "string:" in text:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
                
            for i in range(item.childCount()):
                check_text_fields(item.child(i))
        
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            check_text_fields(root.child(i))