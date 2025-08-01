from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

class FindingsTable(QTableWidget):
    finding_selected = pyqtSignal(dict)  # Emit when finding is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.findings_data = []
        self.detailed_analysis = False  # Track detailed analysis mode
        self.setup_table()
        self.setup_styling()
        
    def setup_table(self):
        # Configure table structure based on detailed analysis mode
        self.update_table_structure()
        
    def update_table_structure(self):
        """Update table structure based on detailed analysis mode"""
        if self.detailed_analysis:
            # Detailed analysis mode - include all columns
            self.setColumnCount(15)
            headers = [
                'Entity Type', 'Text', 'Start', 'End', 'Confidence', 'Recognizer',
                'Pattern Name', 'Pattern', 'Original Score', 'Score',
                'Textual Explanation', 'Score Context Improvement', 
                'Supportive Context Word', 'Validation Result', 'Regex Flags'
            ]
        else:
            # Basic mode - standard columns
            self.setColumnCount(8)
            headers = [
                'Entity Type', 'Text', 'Start', 'End', 'Confidence', 
                'Recognizer', 'Pattern Name', 'Pattern'
            ]
        
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table behavior
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        
        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set column widths based on mode
        self.set_column_widths()
        
        # Connect selection signal
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
    def set_column_widths(self):
        """Set appropriate column widths based on detailed analysis mode"""
        if self.detailed_analysis:
            # Detailed mode column widths
            widths = [100, 120, 50, 50, 80, 100, 100, 120, 80, 80, 150, 120, 120, 80, 80]
            for i, width in enumerate(widths):
                if i < self.columnCount():
                    self.setColumnWidth(i, width)
        else:
            # Basic mode column widths
            self.setColumnWidth(0, 120)  # Entity Type
            self.setColumnWidth(1, 150)  # Text
            self.setColumnWidth(2, 60)   # Start
            self.setColumnWidth(3, 60)   # End
            self.setColumnWidth(4, 90)   # Confidence
            self.setColumnWidth(5, 120)  # Recognizer
            self.setColumnWidth(6, 120)  # Pattern Name
            # Pattern column will stretch
            
    def toggle_detailed_analysis(self, enabled: bool):
        """Toggle detailed analysis mode and refresh table"""
        if self.detailed_analysis != enabled:
            self.detailed_analysis = enabled
            
            # Store current data
            current_data = self.findings_data.copy()
            
            # Clear and rebuild table structure
            self.clear_findings()
            self.update_table_structure()
            self.set_column_widths()
            
            # Repopulate with stored data
            self.findings_data = current_data
            for finding in current_data:
                self._add_finding_to_table(finding)
        
    def setup_styling(self):
        # Get colors from technical specs
        COLORS = {
            'background': '#0a0a0a',
            'surface': '#1a1a1a',
            'surface_hover': '#2a2a2a',
            'border': '#333333',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'text_muted': '#888888',
            'primary': '#00cccc'
        }
        
        style = f"""
            QTableWidget {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
                color: {COLORS['text_secondary']};
                selection-background-color: {COLORS['primary']};
                selection-color: #0a0a0a;
                font-size: 13px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
                outline: none;
            }}
            QTableWidget::item:selected {{
                background: {COLORS['primary']} !important;
                color: #0a0a0a !important;
            }}
            QTableWidget::item:selected:active {{
                background: {COLORS['primary']} !important;
                color: #0a0a0a !important;
            }}
            QTableWidget::item:selected:!active {{
                background: {COLORS['primary']} !important;
                color: #0a0a0a !important;
            }}
            QTableWidget::item:hover:!selected {{
                background: {COLORS['surface_hover']};
            }}
            QHeaderView::section {{
                background: {COLORS['background']};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                font-weight: 500;
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QHeaderView::section:hover {{
                background: {COLORS['surface_hover']};
            }}
            QTableWidget::item:alternate {{
                background: {COLORS['background']};
            }}
            QTableWidget::item:alternate:selected {{
                background: {COLORS['primary']} !important;
                color: #0a0a0a !important;
            }}
        """
        self.setStyleSheet(style)
        
        # Set font
        font = QFont('SF Pro Display', 13)
        self.setFont(font)
        
    def add_finding(self, finding):
        """Add a finding to the table"""
        if not isinstance(finding, dict):
            return
            
        self.findings_data.append(finding)
        self._add_finding_to_table(finding)
        
    def _add_finding_to_table(self, finding):
        """Internal method to add a finding to the table display"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Basic columns always present
        basic_items = [
            QTableWidgetItem(str(finding.get('entity_type', ''))),
            QTableWidgetItem(str(finding.get('text', ''))),
            QTableWidgetItem(str(finding.get('start', ''))),
            QTableWidgetItem(str(finding.get('end', ''))),
            QTableWidgetItem(f"{finding.get('confidence', 0):.3f}"),
            QTableWidgetItem(str(finding.get('recognizer', ''))),
            QTableWidgetItem(str(finding.get('pattern_name', '') or '')),
            QTableWidgetItem(str(finding.get('pattern', '') or ''))
        ]
        
        items = basic_items
        
        # Add detailed analysis columns if enabled
        if self.detailed_analysis:
            detailed_items = [
                QTableWidgetItem(str(finding.get('original_score', '') or '')),
                QTableWidgetItem(str(finding.get('score', '') or '')),
                QTableWidgetItem(str(finding.get('textual_explanation', '') or '')),
                QTableWidgetItem(str(finding.get('score_context_improvement', '') or '')),
                QTableWidgetItem(str(finding.get('supportive_context_word', '') or '')),
                QTableWidgetItem(str(finding.get('validation_result', '') or '')),
                QTableWidgetItem(str(finding.get('regex_flags', '') or ''))
            ]
            items.extend(detailed_items)
        
        for col, item in enumerate(items):
            # Make items read-only
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, col, item)
            
        # Auto-resize rows
        self.resizeRowToContents(row)
        
    def add_findings(self, findings):
        """Add multiple findings to the table"""
        for finding in findings:
            self.add_finding(finding)
            
    def clear_findings(self):
        """Clear all findings from the table"""
        self.setRowCount(0)
        self.findings_data.clear()
        
    def filter_by_confidence(self, min_confidence):
        """Filter findings by confidence threshold"""
        for row in range(self.rowCount()):
            confidence_item = self.item(row, 4)  # Confidence column
            if confidence_item:
                try:
                    confidence = float(confidence_item.text())
                    self.setRowHidden(row, confidence < min_confidence)
                except ValueError:
                    self.setRowHidden(row, True)
                    
    def filter_by_entity_type(self, entity_types):
        """Filter findings by entity types"""
        if not entity_types:
            # Show all rows if no filter
            for row in range(self.rowCount()):
                self.setRowHidden(row, False)
            return
            
        for row in range(self.rowCount()):
            entity_item = self.item(row, 0)  # Entity Type column
            if entity_item:
                entity_type = entity_item.text()
                self.setRowHidden(row, entity_type not in entity_types)
                
    def search_text(self, search_term):
        """Search for text in the findings"""
        search_term = search_term.lower()
        for row in range(self.rowCount()):
            match_found = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and search_term in item.text().lower():
                    match_found = True
                    break
            self.setRowHidden(row, not match_found)
            
    def get_selected_finding(self):
        """Get the currently selected finding"""
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.findings_data):
            return self.findings_data[current_row]
        return None
        
    def _on_selection_changed(self):
        """Handle selection changes"""
        finding = self.get_selected_finding()
        if finding:
            self.finding_selected.emit(finding)
            
    def export_to_list(self):
        """Export visible findings to a list"""
        visible_findings = []
        for row in range(self.rowCount()):
            if not self.isRowHidden(row) and row < len(self.findings_data):
                visible_findings.append(self.findings_data[row])
        return visible_findings
        
    def get_statistics(self):
        """Get statistics about the findings"""
        total_findings = len(self.findings_data)
        visible_findings = len(self.export_to_list())
        
        # Count by entity type
        entity_counts = {}
        for finding in self.findings_data:
            entity_type = finding.get('entity_type', 'Unknown')
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
        # Average confidence
        confidences = [f.get('confidence', 0) for f in self.findings_data]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total_findings': total_findings,
            'visible_findings': visible_findings,
            'entity_counts': entity_counts,
            'average_confidence': avg_confidence
        }