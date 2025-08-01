"""
Preview Panel Component for Phase 3
Reusable preview panel widget for displaying source and output data
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from ui.styles import (COLORS, LAYOUT_DIMENSIONS, get_preview_panel_style, 
                       get_preview_header_style, get_preview_text_style, get_output_preview_text_style)

class PreviewPanel(QWidget):
    """
    Reusable preview panel widget with header and text area
    Used for both source and output previews
    """
    
    content_changed = pyqtSignal(str)  # Emitted when content changes
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.text_edit = None
        self.header_label = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the preview panel UI"""
        # Apply panel styling
        self.setStyleSheet(get_preview_panel_style())
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header_label = QLabel(self.title)
        self.header_label.setStyleSheet(get_preview_header_style())
        
        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(get_preview_text_style())
        self.text_edit.setFixedHeight(LAYOUT_DIMENSIONS['preview_panel_height'])
        
        # Set monospace font for better data display
        font = QFont("Courier New", 13)
        font.setStyleHint(QFont.Monospace)
        self.text_edit.setFont(font)
        
        # Connect signals
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.header_label)
        layout.addWidget(self.text_edit)
        
    def set_content(self, content: str, format: str = 'plain'):
        """
        Set text content in the panel
        
        Args:
            content: The text content to display
            format: Either 'plain' or 'html' for content formatting
        """
        if format == 'html':
            self.text_edit.setHtml(content)
        else:
            self.text_edit.setPlainText(content)
            
    def get_content(self) -> str:
        """Get the current content as plain text"""
        return self.text_edit.toPlainText()
        
    def clear(self):
        """Clear the content"""
        self.text_edit.clear()
        
    def set_title(self, title: str):
        """Update the panel title"""
        self.title = title
        if self.header_label:
            self.header_label.setText(title)
            
    def set_placeholder(self, placeholder: str):
        """Set placeholder text"""
        self.text_edit.setPlaceholderText(placeholder)
        
    def append_content(self, content: str):
        """Append content to existing text"""
        self.text_edit.append(content)
        
    def set_read_only(self, readonly: bool):
        """Set whether the text area is read-only"""
        self.text_edit.setReadOnly(readonly)
        
    def scroll_to_top(self):
        """Scroll to the top of the content"""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.Start)
        self.text_edit.setTextCursor(cursor)
        
    def scroll_to_bottom(self):
        """Scroll to the bottom of the content"""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        self.text_edit.setTextCursor(cursor)
        
    def highlight_text(self, text: str, color: str = None):
        """
        Highlight specific text in the content
        
        Args:
            text: Text to highlight
            color: Highlight color (defaults to primary color)
        """
        if color is None:
            color = COLORS['primary']
            
        # Get current content
        content = self.text_edit.toPlainText()
        
        # Create HTML with highlighted text
        highlighted_content = content.replace(
            text, 
            f'<span style="background-color: {color}; color: #0a0a0a; padding: 2px 4px; border-radius: 2px;">{text}</span>'
        )
        
        # Set as HTML
        self.set_content(highlighted_content, 'html')
        
    def remove_highlights(self):
        """Remove all highlights and return to plain text"""
        content = self.text_edit.toPlainText()
        self.set_content(content, 'plain')
        
    def set_line_height(self, line_height: float):
        """Set custom line height for the text"""
        font = self.text_edit.font()
        self.text_edit.setStyleSheet(get_preview_text_style() + f"""
            QTextEdit {{
                line-height: {line_height};
            }}
        """)
        
    def _on_text_changed(self):
        """Internal handler for text changes"""
        content = self.get_content()
        self.content_changed.emit(content)
        
    def get_line_count(self) -> int:
        """Get the number of lines in the content"""
        return self.text_edit.document().blockCount()
        
    def get_character_count(self) -> int:
        """Get the number of characters in the content"""
        return len(self.get_content())
        
    def set_word_wrap(self, wrap: bool):
        """Enable or disable word wrapping"""
        if wrap:
            self.text_edit.setWordWrapMode(self.text_edit.WidgetWidth)
        else:
            self.text_edit.setWordWrapMode(self.text_edit.NoWrap)

class SourcePreviewPanel(PreviewPanel):
    """Specialized preview panel for source data"""
    
    def __init__(self, parent=None):
        super().__init__("Preview Source", parent)
        self.set_placeholder("Source data will appear here when a file is loaded...")
        
    def load_file_preview(self, file_path: str, max_lines: int = 15) -> bool:
        """
        Load a preview of a file (first N lines)
        
        Args:
            file_path: Path to the file to preview
            max_lines: Maximum number of lines to show
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
                    
                content = '\n'.join(lines)
                if i >= max_lines - 1:  # We hit the limit
                    content += f'\n\n... (showing first {max_lines} lines)'
                    
                self.set_content(content)
                return True
                
        except Exception as e:
            self.set_content(f"Error loading file preview: {str(e)}")
            return False

class OutputPreviewPanel(PreviewPanel):
    """Specialized preview panel for processed output data"""
    
    def __init__(self, parent=None):
        super().__init__("Preview Output", parent)
        # Override with teal text style for output preview
        self.text_edit.setStyleSheet(get_output_preview_text_style())
        self.set_placeholder("Processed output will appear here...")
    
    def set_line_height(self, line_height: float):
        """Set custom line height for the text (override to use teal style)"""
        font = self.text_edit.font()
        self.text_edit.setStyleSheet(get_output_preview_text_style() + f"""
            QTextEdit {{
                line-height: {line_height};
            }}
        """)
        
    def show_processed_data(self, original_data: str, findings: list):
        """
        Show processed data with entity highlighting
        
        Args:
            original_data: The original text data
            findings: List of entity findings with positions
        """
        # Start with original data
        content = original_data
        
        # Sort findings by start position (reverse order for proper replacement)
        sorted_findings = sorted(findings, key=lambda x: x.get('start', 0), reverse=True)
        
        # Apply highlighting for each finding
        for finding in sorted_findings:
            start = finding.get('start', 0)
            end = finding.get('end', 0)
            entity_type = finding.get('entity_type', 'UNKNOWN')
            confidence = finding.get('confidence', 0.0)
            
            # Get entity-specific color
            color = self._get_entity_color(entity_type)
            
            # Extract the original text
            original_text = content[start:end]
            
            # Create highlighted replacement
            highlighted_text = f'<span style="background-color: {color}; color: #0a0a0a; padding: 2px 4px; border-radius: 2px; font-weight: 500;" title="{entity_type} (confidence: {confidence:.2f})">{original_text}</span>'
            
            # Replace in content
            content = content[:start] + highlighted_text + content[end:]
            
        # Set as HTML content
        self.set_content(content, 'html')
        
    def _get_entity_color(self, entity_type: str) -> str:
        """Get color for specific entity type"""
        entity_colors = {
            'PERSON': '#ff6b6b',           # Red
            'EMAIL_ADDRESS': '#4ecdc4',    # Teal
            'PHONE_NUMBER': '#45b7d1',     # Blue
            'CREDIT_CARD': '#f9ca24',      # Yellow
            'IP_ADDRESS': '#6c5ce7',       # Purple
            'URL': '#fd79a8',              # Pink
            'AU_ABN': COLORS['warning'],   # Orange (Australian entities)
            'AU_ACN': COLORS['warning'],
            'AU_TFN': COLORS['warning'],
            'AU_MEDICARE': COLORS['warning'],
            'AU_MEDICAREPROVIDER': COLORS['warning'],
            'AU_DVA': COLORS['warning'],
            'AU_CRN': COLORS['warning'],
        }
        
        return entity_colors.get(entity_type, COLORS['primary'])  # Default to primary color