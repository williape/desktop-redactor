from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton,
                            QGroupBox, QCheckBox, QSlider,
                            QComboBox, QLineEdit, QTextEdit,
                            QFileDialog, QMessageBox, QProgressBar,
                            QDialogButtonBox, QDialog, QFrame,
                            QTreeWidget, QTreeWidgetItem, QScrollArea,
                            QToolButton, QSizePolicy, QSplitter,
                            QStackedLayout, QLayoutItem, QLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve, QSize, QPoint, QRect
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap
import os
import sys
import logging
from pathlib import Path

# Import core processing classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.presidio_manager import PresidioManager
from core.file_processor import FileProcessor
from core.list_manager import ListManager
from core.encryption_manager import EncryptionManager
from ui.widgets.dialogs import ColumnSelectionDialog
from ui.widgets.list_widget import ListWidget
from utils.config_manager import ConfigManager

# Import Phase 3 styling system
from ui.styles import (COLORS, LAYOUT_DIMENSIONS, ENTITIES, NER_MODELS, 
                       PROCESSING_METHODS, SAMPLE_CSV_DATA,
                       get_sidebar_section_style, get_combo_box_style,
                       get_checkbox_style, get_preview_panel_style,
                       get_preview_header_style, get_preview_text_style,
                       get_progress_bar_style, get_primary_button_style,
                       get_small_button_style, get_splitter_style,
                       get_sidebar_scroll_style)

# Import Phase 3 components
from ui.components.preview_panel import PreviewPanel, SourcePreviewPanel, OutputPreviewPanel
from ui.components.findings_table import FindingsTable
from core.preview_manager import PreviewManager


class FlowLayout(QLayout):
    """Flow layout for arranging widgets in rows"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []
        
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
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size
    
    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        for item in self.item_list:
            widget = item.widget()
            space_x = self.spacing()
            space_y = self.spacing()
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - rect.y()

class ProcessingThread(QThread):
    """Background thread for file processing"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, output_path
    
    def __init__(self, file_processor, file_path, file_type, output_dir,
                 entities, confidence, operator_config, columns=None, paths=None):
        super().__init__()
        self.file_processor = file_processor
        self.file_path = file_path
        self.file_type = file_type
        self.output_dir = output_dir
        self.entities = entities
        self.confidence = confidence
        self.operator_config = operator_config
        self.columns = columns
        self.paths = paths
        
    def run(self):
        """Execute the file processing in background thread"""
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Starting file processing: {self.file_path}")
            logger.info(f"Entities: {self.entities}")
            logger.info(f"Confidence: {self.confidence}")
            logger.info(f"File type: {self.file_type}")
            
            self.status.emit("Starting file processing...")
            self.progress.emit(10)
            
            # Import datetime here to avoid import in main thread
            from datetime import datetime
            
            if self.file_type == 'csv':
                self.status.emit("Processing CSV file...")
                self.progress.emit(25)
                logger.info("Starting CSV processing")
                
                result = self.file_processor.process_csv(
                    self.file_path, self.columns, self.entities,
                    self.confidence, self.operator_config
                )
                
                self.progress.emit(75)
                self.status.emit("Saving processed CSV file...")
                
                # Generate output filename
                path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{path.stem}_redacted_{timestamp}.csv"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Saving CSV to: {output_path}")
                self.file_processor.save_csv(result, output_path)
                
            elif self.file_type == 'json':
                self.status.emit("Processing JSON file...")
                self.progress.emit(25)
                logger.info("Starting JSON processing")
                
                result = self.file_processor.process_json(
                    self.file_path, self.paths, self.entities,
                    self.confidence, self.operator_config
                )
                
                self.progress.emit(75)
                self.status.emit("Saving processed JSON file...")
                
                # Generate output filename
                path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{path.stem}_redacted_{timestamp}.json"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Saving JSON to: {output_path}")
                self.file_processor.save_json(result, output_path)
                
            elif self.file_type == 'txt':
                self.status.emit("Processing TXT file...")
                self.progress.emit(25)
                logger.info("Starting TXT processing")
                
                result = self.file_processor.process_txt(
                    self.file_path, self.entities,
                    self.confidence, self.operator_config
                )
                
                self.progress.emit(75)
                self.status.emit("Saving processed TXT file...")
                
                # Generate output filename
                path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{path.stem}_redacted_{timestamp}.txt"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Saving TXT to: {output_path}")
                self.file_processor.save_txt(result, output_path)
            
            self.progress.emit(100)
            self.status.emit("Processing completed successfully!")
            self.finished.emit(True, output_path)
            logger.info(f"Processing completed successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            self.error.emit(str(e))
            self.finished.emit(False, "")

class DropArea(QLabel):
    """Custom drop area for file drag and drop"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(200)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the drop area UI"""
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['surface']};
                color: {COLORS['text_secondary']};
                font-size: 16px;
                font-weight: 500;
            }}
        """)
        self.setText("Drag & Drop your file here, or click to browse\nSupported formats: .csv, .json, txt")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QLabel {{
                    border: 2px dashed {COLORS['primary']};
                    border-radius: 8px;
                    background: {COLORS['surface_hover']};
                    color: {COLORS['primary']};
                    font-size: 16px;
                    font-weight: 500;
                }}
            """)
        
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setup_ui()
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_dropped.emit(files[0])
        self.setup_ui()
        
    def mousePressEvent(self, event):
        """Handle mouse press for browse functionality"""
        if event.button() == Qt.LeftButton:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self, "Select File", "", 
                "Data Files (*.csv *.json *.txt);;CSV Files (*.csv);;JSON Files (*.json);;Text Files (*.txt)"
            )
            if file_path:
                self.file_dropped.emit(file_path)

class PresidioRedactorMainWindow(QMainWindow):
    """Phase 3 Main Window with sidebar layout"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Presidio Desktop Redactor")
        self.setMinimumSize(LAYOUT_DIMENSIONS['window_min_width'], 
                          LAYOUT_DIMENSIONS['window_min_height'])
        
        # Initialize core components
        self.presidio_manager = PresidioManager()
        self.file_processor = FileProcessor(self.presidio_manager)
        self.list_manager = ListManager()
        self.encryption_manager = EncryptionManager()
        self.config_manager = ConfigManager()
        self.preview_manager = PreviewManager(self.presidio_manager)
        
        # Initialize state
        self.current_file = None
        self.current_file_type = None
        self.processing_thread = None
        
        # UI References
        self.entity_checkboxes = {}
        self.threshold_slider = None
        self.ner_model_combo = None
        self.method_combo = None
        self.method_example = None
        self.encryption_section = None
        self.encryption_widget = None
        self.allowlist_widget = None
        self.denylist_widget = None
        self.source_preview = None
        self.output_preview = None
        self.findings_table = None
        self.progress_bar = None
        self.progress_label = None
        self.process_btn = None
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the main UI structure"""
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Vertical layout for header + content + action bar
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add components
        self.setup_header(main_layout)
        self.setup_split_content(main_layout)
        self.setup_action_bar(main_layout)
        
    def setup_header(self, parent_layout):
        """Setup header section"""
        header = QWidget()
        header.setFixedHeight(LAYOUT_DIMENSIONS['header_height'])
        header.setStyleSheet(f"""
            background: {COLORS['header']};
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        
        # Title and subtitle
        title_label = QLabel("Presidio Desktop Redactor")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 20px;
            font-weight: 600;
        """)
        
        subtitle_label = QLabel("Automatically detect and redact personally identifiable information (PII) from Text, CSV and JSON files")
        subtitle_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
        """)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        parent_layout.addWidget(header)
        
    def setup_split_content(self, parent_layout):
        """Setup splitter-based main content"""
        # Create splitter for resizable sidebar
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # Sidebar
        self.sidebar = self.create_sidebar()
        
        # Main content area
        self.main_content = self.create_main_content()
        
        # Add to splitter
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.main_content)
        
        # Set initial sizes (420px sidebar, rest for main)
        self.splitter.setSizes([LAYOUT_DIMENSIONS['sidebar_default_width'], 
                               LAYOUT_DIMENSIONS['window_min_width'] - LAYOUT_DIMENSIONS['sidebar_default_width']])
        
        # Set minimum widths
        self.splitter.setStretchFactor(0, 0)  # Sidebar doesn't stretch
        self.splitter.setStretchFactor(1, 1)  # Main content stretches
        
        # Style the splitter handle
        self.splitter.setStyleSheet(get_splitter_style())
        
        parent_layout.addWidget(self.splitter)
        
    def create_sidebar(self):
        """Create the sidebar with all control sections"""
        sidebar_widget = QWidget()
        sidebar_widget.setMinimumWidth(LAYOUT_DIMENSIONS['sidebar_min_width'])
        sidebar_widget.setMaximumWidth(LAYOUT_DIMENSIONS['sidebar_max_width'])
        sidebar_widget.setStyleSheet(f"""
            background: {COLORS['sidebar']};
            border-right: 1px solid {COLORS['border']};
        """)
        
        # Scroll area for sidebar content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(get_sidebar_scroll_style())
        
        # Container for sidebar content
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'])
        sidebar_layout.setSpacing(LAYOUT_DIMENSIONS['section_padding'])
        
        # Add sidebar sections
        sidebar_layout.addWidget(self.create_detect_entities_section())
        sidebar_layout.addWidget(self.create_processing_method_section())
        self.encryption_section = self.create_encryption_section()
        sidebar_layout.addWidget(self.encryption_section)
        sidebar_layout.addWidget(self.create_allowlist_section())
        sidebar_layout.addWidget(self.create_denylist_section())
        sidebar_layout.addStretch()
        
        scroll_area.setWidget(sidebar_content)
        
        # Main sidebar layout
        layout = QVBoxLayout(sidebar_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        return sidebar_widget
        
    def create_sidebar_section(self, title, widget=None):
        """Create a styled section for the sidebar"""
        section = QWidget()
        section.setStyleSheet(get_sidebar_section_style())
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'])
        layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Title with optional action widget
        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
        """)
        title_layout.addWidget(title_label)
        
        if widget:
            title_layout.addStretch()
            title_layout.addWidget(widget)
        
        layout.addLayout(title_layout)
        
        return section, layout
        
    def create_detect_entities_section(self):
        """Create the Detect Entities section with collapsible entity list"""
        # Create main section container
        section = QWidget()
        section.setStyleSheet(get_sidebar_section_style())
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'])
        layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Title with toggle button
        title_layout = QHBoxLayout()
        
        # Toggle button for showing/hiding entities
        self.entities_toggle_btn = QPushButton("Detect Entities")
        self.entities_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: 15px;
                font-weight: 500;
                text-align: left;
                padding: 0;
                margin: 0;
            }}
            QPushButton:hover {{
                color: {COLORS['primary']};
            }}
        """)
        self.entities_toggle_btn.clicked.connect(self.toggle_entities_section)
        title_layout.addWidget(self.entities_toggle_btn)
        
        # Arrow indicator
        self.entities_arrow = QLabel("▼")
        self.entities_arrow.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            margin-left: 8px;
        """)
        title_layout.addWidget(self.entities_arrow)
        
        title_layout.addStretch()
        
        # Select All button
        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet(get_small_button_style())
        select_all_btn.clicked.connect(self.select_all_entities)
        title_layout.addWidget(select_all_btn)
        
        layout.addLayout(title_layout)
        
        # Collapsible content container
        self.entities_content = QWidget()
        entities_content_layout = QVBoxLayout(self.entities_content)
        entities_content_layout.setContentsMargins(0, 8, 0, 0)
        entities_content_layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Entity checkboxes (single column in sidebar)
        self.entity_checkboxes = {}
        for entity_id, entity_name, is_australian in ENTITIES:
            checkbox = QCheckBox(entity_name)
            checkbox.setStyleSheet(get_checkbox_style(is_australian))
            checkbox.setChecked(True)  # Default to checked
            checkbox.stateChanged.connect(self.on_entity_selection_changed)
            self.entity_checkboxes[entity_id] = checkbox
            entities_content_layout.addWidget(checkbox)
        
        # Acceptance threshold
        threshold_widget = self.create_threshold_widget()
        entities_content_layout.addWidget(threshold_widget)
        
        # Phase 5: Enhanced NER model selection with multiple frameworks
        model_section = self.create_model_management_section()
        entities_content_layout.addWidget(model_section)
        
        layout.addWidget(self.entities_content)
        
        # Store initial state (expanded)
        self.entities_expanded = True
        
        return section
        
    def create_threshold_widget(self):
        """Create the threshold slider widget"""
        threshold_widget = QWidget()
        threshold_layout = QVBoxLayout(threshold_widget)
        threshold_layout.setContentsMargins(0, 8, 0, 0)
        threshold_layout.setSpacing(8)
        
        # Label
        threshold_label = QLabel("Acceptance Threshold")
        threshold_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        threshold_layout.addWidget(threshold_label)
        
        # Slider with value display
        slider_container = QHBoxLayout()
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(70)  # Default 0.7
        self.threshold_slider.setMinimumHeight(24)  # Ensure enough space for handle
        self.threshold_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 8px;
                background: {COLORS['background']};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                border: 1px solid {COLORS['primary']};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        
        self.threshold_value = QLabel("0.70")
        self.threshold_value.setStyleSheet(f"color: {COLORS['primary']}; font-size: 12px; font-weight: 500;")
        self.threshold_value.setMinimumWidth(30)
        
        slider_container.addWidget(self.threshold_slider)
        slider_container.addWidget(self.threshold_value)
        
        threshold_layout.addLayout(slider_container)
        
        # Tip text
        tip_label = QLabel("Lower - detect more, Higher - detect less")
        tip_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            font-style: italic;
            margin-top: 4px;
        """)
        threshold_layout.addWidget(tip_label)
        
        return threshold_widget
    
    def create_model_management_section(self):
        """Create the enhanced model management section for Phase 5"""
        model_widget = QWidget()
        model_layout = QVBoxLayout(model_widget)
        model_layout.setContentsMargins(0, 8, 0, 0)
        model_layout.setSpacing(8)
        
        # Model selection label
        model_label = QLabel("NER Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-top: 8px;")
        model_layout.addWidget(model_label)
        
        # Model dropdown
        self.ner_model_combo = QComboBox()
        self.ner_model_combo.setStyleSheet(get_combo_box_style())
        self.ner_model_combo.currentIndexChanged.connect(self.on_ner_model_changed)
        model_layout.addWidget(self.ner_model_combo)
        
        # Model status and actions layout
        actions_layout = QHBoxLayout()
        
        # Model status label
        self.model_status_label = QLabel("")
        self.model_status_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            font-style: italic;
        """)
        actions_layout.addWidget(self.model_status_label)
        
        actions_layout.addStretch()
        
        # Import model button
        self.import_model_btn = QPushButton("Import...")
        self.import_model_btn.setStyleSheet(get_small_button_style())
        self.import_model_btn.clicked.connect(self.on_import_model_clicked)
        actions_layout.addWidget(self.import_model_btn)
        
        # Refresh models button
        self.refresh_models_btn = QPushButton("⟳")
        self.refresh_models_btn.setToolTip("Refresh available models")
        self.refresh_models_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_secondary']};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 24px;
                max-width: 24px;
            }}
            QPushButton:hover {{
                background: {COLORS['background']};
                color: {COLORS['primary']};
            }}
        """)
        self.refresh_models_btn.clicked.connect(self.on_refresh_models_clicked)
        actions_layout.addWidget(self.refresh_models_btn)
        
        model_layout.addLayout(actions_layout)
        
        # Populate initial models
        self.populate_model_dropdown()
        
        return model_widget
        
    def create_processing_method_section(self):
        """Create the Processing Method section"""
        section, layout = self.create_sidebar_section("Processing Method")
        
        # Method dropdown
        self.method_combo = QComboBox()
        for method in PROCESSING_METHODS:
            self.method_combo.addItem(method['display'])
        
        self.method_combo.setStyleSheet(get_combo_box_style())
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        
        # Example display
        self.method_example = QLabel(PROCESSING_METHODS[0]['example'])
        self.method_example.setStyleSheet(f"""
            padding: 12px;
            background: {COLORS['background']};
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            color: {COLORS['text_muted']};
            text-align: center;
        """)
        
        layout.addWidget(self.method_combo)
        layout.addWidget(self.method_example)
        
        return section
        
    def create_encryption_section(self):
        """Create the simplified encryption section (initially hidden)"""
        section = QWidget()
        section.setStyleSheet(get_sidebar_section_style())
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'])
        layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Title
        title_label = QLabel("Encryption Settings")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
        """)
        layout.addLayout(self._create_title_layout(title_label))
        
        # Key input field
        self.encryption_key_input = QLineEdit()
        self.encryption_key_input.setPlaceholderText("Enter encryption key")
        self.encryption_key_input.setEchoMode(QLineEdit.Password)
        self.encryption_key_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_secondary']};
                padding: 10px 12px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
                background: {COLORS['surface_hover']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """)
        layout.addWidget(self.encryption_key_input)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Generate button
        self.generate_key_btn = QPushButton("Generate")
        self.generate_key_btn.setStyleSheet(get_small_button_style())
        self.generate_key_btn.clicked.connect(self._generate_encryption_key)
        buttons_layout.addWidget(self.generate_key_btn)
        
        # Import button
        self.import_key_btn = QPushButton("Import")
        self.import_key_btn.setStyleSheet(get_small_button_style())
        self.import_key_btn.clicked.connect(self._import_encryption_key)
        buttons_layout.addWidget(self.import_key_btn)
        
        # Export button
        self.export_key_btn = QPushButton("Export")
        self.export_key_btn.setStyleSheet(get_small_button_style())
        self.export_key_btn.clicked.connect(self._export_encryption_key)
        buttons_layout.addWidget(self.export_key_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connect key input changes
        self.encryption_key_input.textChanged.connect(self._on_encryption_key_changed)
        
        section.setVisible(False)  # Hidden by default
        
        return section
    
    def _create_title_layout(self, title_label):
        """Create a simple title layout"""
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        return title_layout
    
    def _generate_encryption_key(self):
        """Generate a new encryption key"""
        try:
            # Use the encryption manager to generate a secure key
            key = self.encryption_manager.generate_key(32)  # 32 character key
            
            self.encryption_key_input.setText(key)
            
            QMessageBox.information(self, "Key Generated", 
                                  "A new encryption key has been generated.")
            
        except Exception as e:
            logging.error(f"Error generating encryption key: {e}")
            QMessageBox.critical(self, "Generation Failed", 
                               f"Failed to generate encryption key: {str(e)}")
    
    def _import_encryption_key(self):
        """Import encryption key from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Encryption Key", "", 
            "Key files (*.key);;Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                # Use the encryption manager's import method
                success = self.encryption_manager.import_key_from_file(file_path)
                
                if success:
                    # Update the UI with the imported key
                    key_info = self.encryption_manager.get_key_info()
                    if key_info.get('has_key'):
                        # Get the key from the manager and display it (masked)
                        self.encryption_key_input.setText("●" * 32)  # Show masked key
                        QMessageBox.information(self, "Import Successful", 
                                              "Encryption key imported successfully.")
                    else:
                        QMessageBox.warning(self, "Import Failed", 
                                          "Failed to import the encryption key.")
                else:
                    QMessageBox.warning(self, "Import Failed", 
                                      "Failed to import encryption key from file.")
                    
            except Exception as e:
                logging.error(f"Error importing encryption key: {e}")
                QMessageBox.critical(self, "Import Failed", 
                                   f"Failed to import encryption key: {str(e)}")
    
    def _export_encryption_key(self):
        """Export encryption key to file"""
        # Check if we have a key
        key_info = self.encryption_manager.get_key_info()
        if not key_info.get('has_key'):
            QMessageBox.warning(self, "Export Failed", 
                              "No encryption key to export. Please enter or generate a key first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Encryption Key", "encryption_key.key",
            "Key files (*.key);;Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                # Use the encryption manager's export method
                success = self.encryption_manager.export_key_to_file(file_path)
                
                if success:
                    QMessageBox.information(self, "Export Successful", 
                                          "Encryption key exported successfully.")
                else:
                    QMessageBox.warning(self, "Export Failed", 
                                      "Failed to export encryption key.")
                                      
            except Exception as e:
                logging.error(f"Error exporting encryption key: {e}")
                QMessageBox.critical(self, "Export Failed", 
                                   f"Failed to export encryption key: {str(e)}")
    
    def _on_encryption_key_changed(self):
        """Handle encryption key input changes"""
        key = self.encryption_key_input.text().strip()
        
        # Update encryption manager
        if hasattr(self, 'encryption_manager') and self.encryption_manager:
            try:
                if key:
                    # Set the key in the encryption manager
                    success = self.encryption_manager.set_encryption_key(key)
                    if success:
                        # Link encryption manager to presidio manager
                        self.presidio_manager.set_encryption_manager(self.encryption_manager)
                        logging.debug("Encryption key updated")
                    else:
                        logging.warning("Failed to set encryption key")
                else:
                    # Clear the key - find the right method
                    self.encryption_manager._encryption_key = None
                    self.encryption_manager.encryption_enabled = False
                    logging.debug("Encryption key cleared")
                    
            except Exception as e:
                logging.error(f"Error updating encryption key: {e}")
        
        # Update preview if file is loaded
        if self.current_file:
            self.generate_output_preview()
    
    def get_encryption_key(self):
        """Get the current encryption key"""
        if hasattr(self, 'encryption_key_input'):
            return self.encryption_key_input.text().strip()
        return ""
        
    def create_allowlist_section(self):
        """Create the allowlist section with Import/Export buttons"""
        # Create header buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet(get_small_button_style())
        import_btn.clicked.connect(lambda: self._import_list("allowlist"))
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(get_small_button_style())
        export_btn.clicked.connect(lambda: self._export_list("allowlist"))
        
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(export_btn)
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        
        # Create section with buttons in header
        section = QWidget()
        section.setStyleSheet(get_sidebar_section_style())
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'])
        layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Title with buttons
        title_layout = QHBoxLayout()
        title_label = QLabel("Allowlist")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(buttons_widget)
        
        layout.addLayout(title_layout)
        
        # Create simplified allowlist widget
        self.allowlist_widget = self._create_simple_list_widget("Add terms to exclude (press Enter)")
        layout.addWidget(self.allowlist_widget)
        
        return section
        
    def create_denylist_section(self):
        """Create the denylist section with Import/Export buttons"""
        # Create header buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet(get_small_button_style())
        import_btn.clicked.connect(lambda: self._import_list("denylist"))
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(get_small_button_style())
        export_btn.clicked.connect(lambda: self._export_list("denylist"))
        
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(export_btn)
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        
        # Create section with buttons in header
        section = QWidget()
        section.setStyleSheet(get_sidebar_section_style())
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'], 
                                LAYOUT_DIMENSIONS['section_padding'])
        layout.setSpacing(LAYOUT_DIMENSIONS['widget_spacing'])
        
        # Title with buttons
        title_layout = QHBoxLayout()
        title_label = QLabel("Denylist")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(buttons_widget)
        
        layout.addLayout(title_layout)
        
        # Create simplified denylist widget
        self.denylist_widget = self._create_simple_list_widget("Add terms to detect (press Enter)")
        layout.addWidget(self.denylist_widget)
        
        return section
    
    def _create_simple_list_widget(self, placeholder_text):
        """Create a simplified list widget with just input and tags"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Input field
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_secondary']};
                padding: 10px 12px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
                background: {COLORS['surface_hover']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """)
        layout.addWidget(input_field)
        
        # Tags area
        tags_scroll = QScrollArea()
        tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tags_scroll.setMaximumHeight(120)
        tags_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        tags_container = QWidget()
        tags_layout = QVBoxLayout(tags_container)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(8)
        
        # Tags flow layout will be added dynamically
        tags_flow_widget = QWidget()
        tags_flow_layout = FlowLayout(tags_flow_widget)
        tags_flow_layout.setSpacing(8)
        tags_layout.addWidget(tags_flow_widget)
        tags_layout.addStretch()
        
        tags_scroll.setWidget(tags_container)
        tags_scroll.setWidgetResizable(True)
        layout.addWidget(tags_scroll)
        
        # Store references for later use
        widget.input_field = input_field
        widget.tags_flow_layout = tags_flow_layout
        widget.tags_flow_widget = tags_flow_widget
        widget.tags = set()
        
        # Connect input field
        input_field.returnPressed.connect(lambda: self._add_tag_from_input(widget))
        
        return widget
    
    def _add_tag_from_input(self, list_widget):
        """Add a tag from the input field"""
        text = list_widget.input_field.text().strip()
        if text and text not in list_widget.tags:
            self._add_tag(list_widget, text)
            list_widget.input_field.clear()
    
    def _add_tag(self, list_widget, text):
        """Add a tag to the list widget"""
        if text in list_widget.tags:
            return
            
        list_widget.tags.add(text)
        
        # Create tag widget
        tag = self._create_tag_widget(text, lambda: self._remove_tag(list_widget, text))
        list_widget.tags_flow_layout.addWidget(tag)
        
        # Update list manager and preview if file is loaded
        self._update_list_manager()
        if self.current_file:
            self.generate_output_preview()
    
    def _remove_tag(self, list_widget, text):
        """Remove a tag from the list widget"""
        if text not in list_widget.tags:
            return
            
        list_widget.tags.discard(text)
        
        # Remove tag widget from layout
        for i in range(list_widget.tags_flow_layout.count()):
            item = list_widget.tags_flow_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'text') and item.widget().text == text:
                widget = item.widget()
                list_widget.tags_flow_layout.removeWidget(widget)
                widget.deleteLater()
                break
        
        # Update list manager and preview if file is loaded
        self._update_list_manager()
        if self.current_file:
            self.generate_output_preview()
    
    def _create_tag_widget(self, text, remove_callback):
        """Create a styled tag widget"""
        tag = QWidget()
        tag.text = text  # Store text for reference
        tag.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['surface_hover']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                padding: 2px;
            }}
            QWidget:hover {{
                background: #333;
                border-color: {COLORS['primary']};
            }}
        """)
        
        layout = QHBoxLayout(tag)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(6)
        
        # Tag text
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                background: transparent;
                border: none;
                font-size: 12px;
            }}
        """)
        layout.addWidget(label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_muted']};
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {COLORS['error']};
                color: white;
            }}
        """)
        remove_btn.clicked.connect(remove_callback)
        layout.addWidget(remove_btn)
        
        return tag
    
    def _import_list(self, list_type):
        """Import list from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Import {list_type.title()}", "", 
            "Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    items = [line.strip() for line in f if line.strip()]
                
                list_widget = self.allowlist_widget if list_type == "allowlist" else self.denylist_widget
                for item in items:
                    self._add_tag(list_widget, item)
                    
                QMessageBox.information(self, "Import Successful", 
                                      f"Imported {len(items)} items to {list_type}")
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Failed to import {list_type}: {str(e)}")
    
    def _export_list(self, list_type):
        """Export list to file"""
        list_widget = self.allowlist_widget if list_type == "allowlist" else self.denylist_widget
        if not list_widget.tags:
            QMessageBox.information(self, "Export", f"No items in {list_type} to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export {list_type.title()}", f"{list_type}.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for item in sorted(list_widget.tags):
                        f.write(f"{item}\n")
                        
                QMessageBox.information(self, "Export Successful", 
                                      f"Exported {len(list_widget.tags)} items from {list_type}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export {list_type}: {str(e)}")
    
    def _update_list_manager(self):
        """Update the list manager with current allowlist/denylist terms"""
        try:
            # Update allowlist
            allowlist_terms = self.get_allowlist_terms()
            self.list_manager.allowlist.clear()
            for term in allowlist_terms:
                self.list_manager.add_to_allowlist(term)
            
            # Update denylist  
            denylist_terms = self.get_denylist_terms()
            self.list_manager.denylist.clear()
            for term in denylist_terms:
                self.list_manager.add_to_denylist(term, 'CUSTOM')  # Default entity type
            
            # Update presidio manager with list manager
            self.presidio_manager.set_list_manager(self.list_manager)
            
        except Exception as e:
            logging.error(f"Error updating list manager: {e}")
        
    def create_main_content(self):
        """Create the main content area"""
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {COLORS['background']};")
        
        # Scroll area for main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        # Content container
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'], 
                                        LAYOUT_DIMENSIONS['section_spacing'])
        content_layout.setSpacing(LAYOUT_DIMENSIONS['section_spacing'])
        
        # File input
        file_input = self.create_file_input()
        content_layout.addWidget(file_input)
        
        # Preview section (placeholder for now)
        preview_widget = self.create_preview_section()
        content_layout.addWidget(preview_widget)
        
        # Findings section with table
        findings_widget = self.create_findings_section()
        content_layout.addWidget(findings_widget)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_container)
        
        # Main layout
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        return content_widget
        
    def create_file_input(self):
        """Create the file input section"""
        file_section = QWidget()
        file_layout = QVBoxLayout(file_section)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(12)
        
        # Drop area
        self.drop_area = DropArea()
        file_layout.addWidget(self.drop_area)
        
        return file_section
        
    def create_preview_section(self):
        """Create preview section with new PreviewPanel components"""
        preview_widget = QWidget()
        preview_layout = QHBoxLayout(preview_widget)
        preview_layout.setSpacing(LAYOUT_DIMENSIONS['section_spacing'])
        
        # Source preview using new component
        self.source_preview = SourcePreviewPanel()
        
        # Output preview using new component  
        self.output_preview = OutputPreviewPanel()
        
        preview_layout.addWidget(self.source_preview)
        preview_layout.addWidget(self.output_preview)
        
        return preview_widget
        
        
    def create_findings_section(self):
        """Create findings section with table"""
        findings_widget = QWidget()
        findings_layout = QVBoxLayout(findings_widget)
        findings_layout.setContentsMargins(0, 0, 0, 0)
        findings_layout.setSpacing(16)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Title
        header_label = QLabel("Findings")
        header_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: 500;
        """)
        header_layout.addWidget(header_label)
        
        # Statistics label
        self.findings_stats_label = QLabel("No findings")
        self.findings_stats_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 13px;
        """)
        header_layout.addWidget(self.findings_stats_label)
        
        header_layout.addStretch()
        
        # Detailed analysis toggle
        self.detailed_analysis_checkbox = QCheckBox("Show detailed analysis")
        self.detailed_analysis_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
                padding: 4px 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {COLORS['border']};
                border-radius: 3px;
                background: {COLORS['background']};
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS['primary']};
                border-color: {COLORS['primary']};
                image: url("data:image/svg+xml;utf8,<svg width='10' height='8' viewBox='0 0 10 8' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M8.5 1L3.5 6L1.5 4' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>");
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.detailed_analysis_checkbox.stateChanged.connect(self.on_detailed_analysis_toggled)
        header_layout.addWidget(self.detailed_analysis_checkbox)
        
        # Export button
        export_findings_btn = QPushButton("Export")
        export_findings_btn.setStyleSheet(get_small_button_style())
        export_findings_btn.clicked.connect(self.export_findings_to_csv)
        header_layout.addWidget(export_findings_btn)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Confidence filter
        conf_label = QLabel("Min Confidence:")
        conf_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        filter_layout.addWidget(conf_label)
        
        self.findings_confidence_slider = QSlider(Qt.Horizontal)
        self.findings_confidence_slider.setRange(0, 100)
        self.findings_confidence_slider.setValue(70)
        self.findings_confidence_slider.setFixedWidth(100)
        filter_layout.addWidget(self.findings_confidence_slider)
        
        self.findings_confidence_label = QLabel("0.70")
        self.findings_confidence_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.findings_confidence_label.setFixedWidth(40)
        filter_layout.addWidget(self.findings_confidence_label)
        
        header_layout.addLayout(filter_layout)
        
        findings_layout.addLayout(header_layout)
        
        # Findings table
        self.findings_table = FindingsTable()
        self.findings_table.setMinimumHeight(300)
        findings_layout.addWidget(self.findings_table)
        
        return findings_widget
        
    def setup_action_bar(self, parent_layout):
        """Setup action bar with progress and process button"""
        action_bar = QWidget()
        action_bar.setFixedHeight(LAYOUT_DIMENSIONS['action_bar_height'])
        action_bar.setStyleSheet(f"""
            background: {COLORS['header']};
            border-top: 1px solid {COLORS['border']};
        """)
        
        layout = QHBoxLayout(action_bar)
        layout.setContentsMargins(LAYOUT_DIMENSIONS['section_spacing'], 16, 
                                LAYOUT_DIMENSIONS['section_spacing'], 16)
        layout.setSpacing(LAYOUT_DIMENSIONS['section_spacing'])
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(36)
        self.progress_bar.setStyleSheet(get_progress_bar_style())
        
        # Progress label overlay
        progress_container = QWidget()
        progress_layout = QStackedLayout(progress_container)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to process")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        progress_layout.addWidget(self.progress_label)
        progress_layout.setStackingMode(QStackedLayout.StackAll)
        
        # Process button
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.setFixedHeight(36)
        self.process_btn.setMinimumWidth(140)
        self.process_btn.setStyleSheet(get_primary_button_style())
        self.process_btn.setEnabled(False)  # Disabled until file is loaded
        
        layout.addWidget(progress_container, 1)
        layout.addWidget(self.process_btn, 0)
        
        parent_layout.addWidget(action_bar)
        
    def setup_connections(self):
        """Setup signal connections"""
        # File drop connection
        self.drop_area.file_dropped.connect(self.on_file_dropped)
        
        # Process button connection
        self.process_btn.clicked.connect(self.start_processing)
        
        # Findings table connections
        if hasattr(self, 'findings_table'):
            self.findings_table.finding_selected.connect(self.on_finding_selected)
        
        # Findings confidence slider
        if hasattr(self, 'findings_confidence_slider'):
            self.findings_confidence_slider.valueChanged.connect(self.on_findings_confidence_changed)
        
        # Initialize list manager integration
        self._update_list_manager()
        
        # Initialize encryption manager integration
        self.presidio_manager.set_encryption_manager(self.encryption_manager)
        
    def toggle_entities_section(self):
        """Toggle the visibility of the entities section"""
        self.entities_expanded = not self.entities_expanded
        
        if self.entities_expanded:
            self.entities_content.setVisible(True)
            self.entities_arrow.setText("▼")
            self.entities_toggle_btn.setText("Detect Entities")
        else:
            self.entities_content.setVisible(False)
            self.entities_arrow.setText("▶")
            self.entities_toggle_btn.setText("Detect Entities")
            
    def select_all_entities(self):
        """Select all entity checkboxes"""
        for checkbox in self.entity_checkboxes.values():
            checkbox.setChecked(True)
            
    def on_entity_selection_changed(self):
        """Handle entity selection changes"""
        # Update output preview when entities change
        if self.current_file:
            self.generate_output_preview()
        
    def on_threshold_changed(self, value):
        """Handle threshold slider changes"""
        threshold = value / 100.0
        self.threshold_value.setText(f"{threshold:.2f}")
        
        # Update output preview when threshold changes
        if self.current_file:
            self.generate_output_preview()
        
    def on_ner_model_changed(self):
        """Handle NER model selection changes (Phase 5 enhanced)"""
        try:
            # Get selected model ID
            selected_index = self.ner_model_combo.currentIndex()
            if selected_index < 0:
                return
            
            model_id = self.ner_model_combo.itemData(selected_index)
            if not model_id:
                return
            
            # Update the presidio manager to use the selected model
            success = self.presidio_manager.set_nlp_engine(model_id)
            
            if success:
                # Update status label
                engine_info = self.presidio_manager.get_current_engine_info()
                self.model_status_label.setText(f"{engine_info['framework']} • {engine_info['language']}")
                
                # Update output preview if file is loaded
                if self.current_file:
                    self.generate_output_preview()
                    
                logging.info(f"Switched to NER model: {model_id}")
            else:
                self.model_status_label.setText("Error loading model")
                QMessageBox.warning(self, "Model Error", f"Failed to load NER model: {model_id}")
                
        except Exception as e:
            logging.error(f"Error changing NER model: {e}")
            self.model_status_label.setText("Error")
            QMessageBox.warning(self, "Model Error", f"Error changing model: {str(e)}")
    
    def populate_model_dropdown(self):
        """Populate the model dropdown with available engines"""
        try:
            self.ner_model_combo.clear()
            
            # Get available engines from presidio manager
            available_engines = self.presidio_manager.get_available_engines()
            
            if not available_engines:
                # Fallback to default if no engines available
                self.ner_model_combo.addItem("Default spaCy Engine", "default")
                self.model_status_label.setText("Default engine")
                return
            
            # Add available engines to dropdown
            current_engine = self.presidio_manager.get_current_engine_info()
            current_index = 0
            
            for i, engine in enumerate(available_engines):
                display_name = f"{engine['name']} ({engine['framework']})"
                self.ner_model_combo.addItem(display_name, engine['id'])
                
                # Set current selection
                if engine['id'] == current_engine['id']:
                    current_index = i
            
            # Set current selection
            self.ner_model_combo.setCurrentIndex(current_index)
            
            # Update status
            if current_engine:
                self.model_status_label.setText(f"{current_engine['framework']} • {current_engine.get('language', 'en')}")
            
            logging.info(f"Populated model dropdown with {len(available_engines)} engines")
            
        except Exception as e:
            logging.error(f"Error populating model dropdown: {e}")
            self.ner_model_combo.addItem("Error loading models", "error")
            self.model_status_label.setText("Error")
    
    def on_import_model_clicked(self):
        """Handle import model button click"""
        try:
            from ui.widgets.model_import_dialog import ModelImportDialog
            
            dialog = ModelImportDialog(self.presidio_manager.get_model_manager(), self)
            if dialog.exec_() == QDialog.Accepted:
                # Refresh the model dropdown
                self.on_refresh_models_clicked()
                QMessageBox.information(self, "Success", "Model imported successfully!")
                
        except ImportError:
            # Create a simple import dialog if the dedicated one doesn't exist yet
            self._show_simple_import_dialog()
        except Exception as e:
            logging.error(f"Error importing model: {e}")
            QMessageBox.warning(self, "Import Error", f"Failed to import model: {str(e)}")
    
    def _show_simple_import_dialog(self):
        """Show a simple model import dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Model")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Framework selection
        layout.addWidget(QLabel("Framework:"))
        framework_combo = QComboBox()
        framework_combo.addItems(["spacy", "transformers", "flair", "stanza"])
        layout.addWidget(framework_combo)
        
        # Path selection
        layout.addWidget(QLabel("Model Path:"))
        path_layout = QHBoxLayout()
        path_input = QLineEdit()
        browse_btn = QPushButton("Browse...")
        
        def browse_path():
            path = QFileDialog.getExistingDirectory(dialog, "Select Model Directory")
            if path:
                path_input.setText(path)
        
        browse_btn.clicked.connect(browse_path)
        path_layout.addWidget(path_input)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        import_btn = QPushButton("Import")
        cancel_btn = QPushButton("Cancel")
        
        def do_import():
            framework = framework_combo.currentText()
            path = path_input.text()
            
            if not path:
                QMessageBox.warning(dialog, "Error", "Please select a model path")
                return
            
            try:
                success = self.presidio_manager.import_model(path, framework)
                if success:
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Error", "Failed to import model")
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Import failed: {str(e)}")
        
        import_btn.clicked.connect(do_import)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(import_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def on_refresh_models_clicked(self):
        """Handle refresh models button click"""
        try:
            # Refresh models in presidio manager
            success = self.presidio_manager.refresh_nlp_engines()
            
            if success:
                # Repopulate dropdown
                self.populate_model_dropdown()
                self.model_status_label.setText("Models refreshed")
                logging.info("Models refreshed successfully")
            else:
                self.model_status_label.setText("Refresh failed")
                QMessageBox.warning(self, "Refresh Error", "Failed to refresh models")
                
        except Exception as e:
            logging.error(f"Error refreshing models: {e}")
            self.model_status_label.setText("Refresh error")
            QMessageBox.warning(self, "Refresh Error", f"Error refreshing models: {str(e)}")
        
    def on_method_changed(self, index):
        """Handle processing method changes"""
        if index < len(PROCESSING_METHODS):
            method = PROCESSING_METHODS[index]
            self.method_example.setText(method['example'])
            
            # Show/hide encryption section
            show_encryption = method['id'] == 'encrypt'
            self.encryption_section.setVisible(show_encryption)
            
            # Update output preview when method changes
            if self.current_file:
                self.generate_output_preview()
    
    def on_finding_selected(self, finding):
        """Handle finding selection in the table"""
        # This will highlight the finding in the preview panels
        # Implementation will connect to preview highlights
        pass
    
    def on_findings_confidence_changed(self, value):
        """Handle findings confidence filter changes"""
        confidence = value / 100.0
        self.findings_confidence_label.setText(f"{confidence:.2f}")
        
        # Filter findings table by confidence
        if hasattr(self, 'findings_table'):
            self.findings_table.filter_by_confidence(confidence)
            
        # Update statistics
        self.update_findings_statistics()
    
    def on_detailed_analysis_toggled(self, state):
        """Handle detailed analysis toggle changes"""
        enabled = state == 2  # Qt.Checked
        
        # Update findings table mode
        if hasattr(self, 'findings_table'):
            self.findings_table.toggle_detailed_analysis(enabled)
        
        # Regenerate preview with detailed analysis if file is loaded
        if self.current_file:
            self.generate_output_preview()
    
    def export_findings_to_csv(self):
        """Export findings table data to CSV file"""
        if not hasattr(self, 'findings_table') or not self.findings_table:
            QMessageBox.information(self, "Export", "No findings table available to export.")
            return
        
        # Check if there are any findings to export
        visible_findings = self.findings_table.export_to_list()
        if not visible_findings:
            QMessageBox.information(self, "Export", "No findings to export. Load a file and analyze it first.")
            return
        
        # Get export file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Findings", "findings_export.csv",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            from datetime import datetime
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Determine column names based on detailed analysis mode
                if self.findings_table.detailed_analysis:
                    fieldnames = [
                        'entity_type', 'text', 'start', 'end', 'confidence', 'recognizer',
                        'pattern_name', 'pattern', 'original_score', 'score',
                        'textual_explanation', 'score_context_improvement', 
                        'supportive_context_word', 'validation_result', 'regex_flags'
                    ]
                else:
                    fieldnames = [
                        'entity_type', 'text', 'start', 'end', 'confidence', 
                        'recognizer', 'pattern_name', 'pattern'
                    ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write findings data
                for finding in visible_findings:
                    # Create row with only the fields we want to export
                    row = {field: finding.get(field, '') for field in fieldnames}
                    
                    # Format confidence as number
                    if 'confidence' in row and row['confidence']:
                        try:
                            row['confidence'] = f"{float(row['confidence']):.3f}"
                        except (ValueError, TypeError):
                            pass
                    
                    # Format numeric fields
                    for numeric_field in ['original_score', 'score', 'score_context_improvement']:
                        if numeric_field in row and row[numeric_field]:
                            try:
                                row[numeric_field] = f"{float(row[numeric_field]):.3f}"
                            except (ValueError, TypeError):
                                pass
                    
                    writer.writerow(row)
            
            # Show success message
            exported_count = len(visible_findings)
            analysis_mode = "detailed" if self.findings_table.detailed_analysis else "basic"
            QMessageBox.information(
                self, "Export Successful", 
                f"Exported {exported_count} findings to CSV file in {analysis_mode} mode.\n\nFile saved as:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export findings to CSV: {str(e)}")
    
    def update_findings_statistics(self):
        """Update the findings statistics display"""
        if not hasattr(self, 'findings_table') or not self.findings_table:
            return
            
        stats = self.findings_table.get_statistics()
        total = stats.get('total_findings', 0)
        visible = stats.get('visible_findings', 0)
        
        if total == 0:
            self.findings_stats_label.setText("No findings")
        elif total == visible:
            self.findings_stats_label.setText(f"{total} findings")
        else:
            self.findings_stats_label.setText(f"{visible} of {total} findings")
    
    def generate_output_preview(self):
        """Generate output preview with current settings"""
        if not self.current_file or not hasattr(self, 'preview_manager'):
            return
            
        try:
            # Get current settings
            entities = self.get_selected_entities()
            confidence = self.threshold_slider.value() / 100.0 if self.threshold_slider else 0.7
            method = self.get_selected_method()
            detailed_analysis = self.detailed_analysis_checkbox.isChecked() if hasattr(self, 'detailed_analysis_checkbox') else False
            
            # Process preview
            success, processed_data, findings = self.preview_manager.process_preview(
                entities, confidence, method, detailed_analysis
            )
            
            if success:
                # Update output preview
                if hasattr(self, 'output_preview'):
                    self.output_preview.set_content(processed_data)
                
                # Update findings table
                if hasattr(self, 'findings_table'):
                    self.findings_table.clear_findings()
                    if findings and len(findings.findings) > 0:
                        findings_data = [f.to_dict() for f in findings.findings]
                        self.findings_table.add_findings(findings_data)
                        
                        # Apply current confidence filter
                        current_confidence = self.findings_confidence_slider.value() / 100.0
                        self.findings_table.filter_by_confidence(current_confidence)
                        
                        # Update statistics
                        self.update_findings_statistics()
                    else:
                        self.findings_stats_label.setText("No findings")
            else:
                logging.error(f"Preview generation failed: {processed_data}")
                
        except Exception as e:
            logging.error(f"Error generating output preview: {e}")
    
    def get_selected_entities(self):
        """Get list of selected entity types"""
        selected = []
        for entity_type, checkbox in self.entity_checkboxes.items():
            if checkbox.isChecked():
                selected.append(entity_type)
        return selected
    
    def get_allowlist_terms(self):
        """Get current allowlist terms"""
        if hasattr(self, 'allowlist_widget') and self.allowlist_widget:
            return list(self.allowlist_widget.tags)
        return []
    
    def get_denylist_terms(self):
        """Get current denylist terms"""
        if hasattr(self, 'denylist_widget') and self.denylist_widget:
            return list(self.denylist_widget.tags)
        return []
    
    def get_selected_method(self):
        """Get selected processing method"""
        if hasattr(self, 'method_combo') and self.method_combo:
            index = self.method_combo.currentIndex()
            if 0 <= index < len(PROCESSING_METHODS):
                return PROCESSING_METHODS[index]['id']
        return 'replace'
            
    def on_file_dropped(self, file_path):
        """Handle file drop event"""
        try:
            # Validate file
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "File does not exist.")
                return
                
            # Check file size (10MB limit)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                reply = QMessageBox.question(
                    self, "Large File Warning",
                    f"File size is {file_size / (1024*1024):.1f}MB. "
                    "Processing may be slow. Continue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Determine file type
            ext = Path(file_path).suffix.lower()
            if ext == '.csv':
                self.current_file_type = 'csv'
            elif ext == '.json':
                self.current_file_type = 'json'
            elif ext in ['.txt', '.text']:
                self.current_file_type = 'txt'
            else:
                QMessageBox.warning(self, "Error", "Unsupported file format. Please use CSV, JSON, or TXT files.")
                return
                
            self.current_file = file_path
            self.process_btn.setEnabled(True)
            self.progress_label.setText(f"File loaded: {Path(file_path).name}")
            
            # Update drop area text
            self.drop_area.setText(f"File loaded: {Path(file_path).name}\nClick here to select a different file")
            
            # Load file preview
            self.load_file_preview(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            
    def load_file_preview(self, file_path: str):
        """Load preview of the selected file"""
        try:
            # Load sample data using preview manager
            success, sample_data = self.preview_manager.load_file_sample(file_path)
            
            if success:
                # Update source preview
                self.source_preview.set_content(sample_data)
                
                # Generate output preview with current settings
                self.generate_output_preview()
            else:
                self.source_preview.set_content(f"Error loading file: {sample_data}")
                
        except Exception as e:
            self.source_preview.set_content(f"Error loading file preview: {str(e)}")
            

    def start_processing(self):
        """Start file processing"""
        if not self.current_file:
            QMessageBox.warning(self, "Error", "Please select a file first.")
            return
            
        try:
            # Get selected entities
            selected_entities = []
            for entity_id, checkbox in self.entity_checkboxes.items():
                if checkbox.isChecked():
                    selected_entities.append(entity_id)
                    
            if not selected_entities:
                QMessageBox.warning(self, "Error", "Please select at least one entity type.")
                return
                
            # Get confidence threshold
            confidence = self.threshold_slider.value() / 100.0
            
            # Get processing method
            method_index = self.method_combo.currentIndex()
            if method_index < len(PROCESSING_METHODS):
                method = PROCESSING_METHODS[method_index]['operator']
            else:
                method = 'replace'
                
            # Setup operator config using PresidioManager
            operator_config = self.presidio_manager.get_default_operator_config(method)
            
            # Get output directory
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if not output_dir:
                return
                
            # Disable UI during processing
            self.process_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.progress_label.setText("Initializing...")
            
            # Start processing thread
            self.processing_thread = ProcessingThread(
                self.file_processor, self.current_file, self.current_file_type,
                output_dir, selected_entities, confidence, operator_config
            )
            
            # Connect thread signals
            self.processing_thread.progress.connect(self.progress_bar.setValue)
            self.processing_thread.status.connect(self.progress_label.setText)
            self.processing_thread.error.connect(self.on_processing_error)
            self.processing_thread.finished.connect(self.on_processing_finished)
            
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
            self.process_btn.setEnabled(True)
            
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        QMessageBox.critical(self, "Processing Error", error_message)
        self.process_btn.setEnabled(True)
        self.progress_label.setText("Processing failed")
        
    def on_processing_finished(self, success, output_path):
        """Handle processing completion"""
        self.process_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "Success", 
                f"File processed successfully!\nOutput saved to:\n{output_path}"
            )
            self.progress_label.setText("Processing completed")
        else:
            self.progress_label.setText("Processing failed")
            
    def load_settings(self):
        """Load saved settings"""
        # This will be implemented to restore user preferences
        pass
        
    def save_settings(self):
        """Save current settings"""
        # This will be implemented to persist user preferences
        pass
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        event.accept()