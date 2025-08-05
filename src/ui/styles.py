# Phase 3 UI Styling System
# Centralized styling constants and helper functions for the new sidebar-based UI

COLORS = {
    'background': '#0a0a0a',        # Main background
    'surface': '#1a1a1a',          # Card/panel backgrounds
    'surface_hover': '#2a2a2a',    # Hover states
    'header': '#0f0f0f',           # Header background  
    'sidebar': '#181818',          # Sidebar background
    'border': '#333333',           # Border colors
    'text_primary': '#ffffff',     # Primary text
    'text_secondary': '#cccccc',   # Secondary text
    'text_muted': '#888888',       # Muted text
    'text_disabled': '#555555',    # Disabled text
    'primary': '#00cccc',          # Primary accent (cyan)
    'primary_hover': '#00e6e6',    # Primary hover
    'warning': '#ff9500',          # Warning/Australian entity marker
    'error': '#ff4444',            # Error states
    'success': '#44ff44'           # Success states
}

LAYOUT_DIMENSIONS = {
    'window_min_width': 1400,
    'window_min_height': 900,
    'sidebar_min_width': 320,
    'sidebar_max_width': 600,
    'sidebar_default_width': 420,
    'action_bar_height': 68,
    'preview_panel_height': 320,
    'header_height': 80,
    'section_spacing': 24,
    'section_padding': 20,
    'widget_spacing': 16
}

ENTITIES = [
    # Standard Entities
    ('PERSON', 'Person Name', False),
    ('EMAIL_ADDRESS', 'Email Address', False),
    ('PHONE_NUMBER', 'Phone Number', False),
    ('CREDIT_CARD', 'Credit Card', False),
    ('IP_ADDRESS', 'IP Address', False),
    ('URL', 'URL', False),
    
    # Australian Entities (marked with warning color)
    ('AU_ABN', 'AU ABN', True),
    ('AU_ACN', 'AU ACN', True),
    ('AU_TFN', 'AU TFN', True),
    ('AU_MEDICARE', 'AU Medicare', True),
    ('AU_MEDICAREPROVIDER', 'AU Medicare Provider', True),
    ('AU_DVA', 'AU DVA', True),
    ('AU_CRN', 'AU CRN', True),
    ('AU_PASSPORT', 'AU Passport', True),
    ('AU_DRIVERSLICENSE', 'AU Driver\'s License', True)
]

NER_MODELS = [
    {
        'id': 'spacy_lg',
        'display': 'spaCy/en_core_web_lg',
        'package': 'en_core_web_lg',
        'type': 'spacy',
        'default': False  # Not bundled in PyInstaller builds
    },
    {
        'id': 'spacy_md', 
        'display': 'spaCy/en_core_web_md',
        'package': 'en_core_web_md',
        'type': 'spacy',
        'default': True  # Default for PyInstaller builds
    },
    {
        'id': 'spacy_sm',
        'display': 'spaCy/en_core_web_sm', 
        'package': 'en_core_web_sm',
        'type': 'spacy'
    },
    {
        'id': 'bert_ner',
        'display': 'Transformers/dslim/bert-base-NER',
        'package': 'dslim/bert-base-NER',
        'type': 'transformers'
    }
]

PROCESSING_METHODS = [
    {
        'id': 'replace',
        'display': 'Replace',
        'example': 'John Doe → <PERSON>',
        'operator': 'replace'
    },
    {
        'id': 'redact',
        'display': 'Redact', 
        'example': 'John Doe → ████████',
        'operator': 'redact'
    },
    {
        'id': 'mask',
        'display': 'Mask',
        'example': 'John Doe → J*** D**',
        'operator': 'mask'
    },
    {
        'id': 'hash',
        'display': 'Hash',
        'example': 'John Doe → a1b2c3d4',
        'operator': 'hash'
    },
    {
        'id': 'encrypt',
        'display': 'Encrypt',
        'example': 'John Doe → U2FsdGVk...',
        'operator': 'encrypt'
    }
]

def get_sidebar_section_style():
    return f"""
        QWidget {{
            background: {COLORS['surface']};
            border-radius: 8px;
        }}
    """

def get_combo_box_style():
    return f"""
        QComboBox {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            color: {COLORS['text_secondary']};
            padding: 10px 12px;
            border-radius: 4px;
            font-size: 13px;
        }}
        QComboBox:hover {{
            border-color: {COLORS['primary']};
            background: {COLORS['surface_hover']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            selection-background-color: {COLORS['primary']};
            selection-color: #0a0a0a;
        }}
    """

def get_checkbox_style(is_australian=False):
    australian_border = f"border-left: 3px solid {COLORS['warning']};" if is_australian else ""
    return f"""
        QCheckBox {{
            padding: 10px 12px;
            background: {COLORS['background']};
            border-radius: 4px;
            color: {COLORS['text_primary']};
            font-size: 13px;
            {australian_border}
        }}
        QCheckBox:hover {{
            background: {COLORS['surface_hover']};
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
    """

def get_preview_panel_style():
    return f"""
        QWidget {{
            background: {COLORS['surface']};
            border-radius: 8px;
        }}
    """

def get_preview_header_style():
    return f"""
        QLabel {{
            background: {COLORS['background']};
            padding: 12px 20px;
            border-bottom: 1px solid {COLORS['border']};
            font-weight: 500;
            color: {COLORS['text_primary']};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
    """

def get_preview_text_style():
    return f"""
        QTextEdit {{
            background: {COLORS['surface']};
            border: none;
            padding: 16px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: {COLORS['text_secondary']};
            line-height: 1.6;
        }}"""

def get_output_preview_text_style():
    return f"""
        QTextEdit {{
            background: {COLORS['surface']};
            border: none;
            padding: 16px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: {COLORS['primary']};
            line-height: 1.6;
        }}
    """

def get_findings_table_style():
    return f"""
        QTableWidget {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            gridline-color: {COLORS['border']};
        }}
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {COLORS['border']};
        }}
        QTableWidget::item:selected {{
            background: {COLORS['primary']};
            color: #0a0a0a;
        }}
        QHeaderView::section {{
            background: {COLORS['background']};
            padding: 12px 8px;
            border: none;
            border-bottom: 2px solid {COLORS['border']};
            font-weight: 500;
            color: {COLORS['text_primary']};
        }}
    """

def get_progress_bar_style():
    return f"""
        QProgressBar {{
            background: {COLORS['surface']};
            border-radius: 18px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 #00a0a0);
            border-radius: 18px;
        }}
    """

def get_primary_button_style():
    return f"""
        QPushButton {{
            background: {COLORS['primary']};
            border: none;
            border-radius: 6px;
            color: #0a0a0a;
            font-weight: 600;
            font-size: 14px;
            padding: 0 28px;
        }}
        QPushButton:hover {{
            background: {COLORS['primary_hover']};
        }}
        QPushButton:disabled {{
            background: {COLORS['border']};
            color: {COLORS['text_disabled']};
        }}
    """

def get_small_button_style():
    return f"""
        QPushButton {{
            background: {COLORS['surface_hover']};
            border: 1px solid {COLORS['border']};
            color: {COLORS['primary']};
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background: #333;
            border-color: {COLORS['primary']};
        }}
    """

def get_splitter_style():
    return f"""
        QSplitter::handle {{
            background: {COLORS['border']};
            width: 1px;
        }}
        QSplitter::handle:hover {{
            background: {COLORS['primary']};
            width: 4px;
        }}
    """

def get_sidebar_scroll_style():
    return f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {COLORS['sidebar']};
            width: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLORS['border']};
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {COLORS['primary']};
        }}
    """

SAMPLE_CSV_DATA = """id,name,email,phone,ssn,address
1,John Smith,john.smith@example.com,+61 2 345 678,123-45-6789,123 Main St Brisbane
2,Jane Doe,jane.doe@company.com,+61 456 789 012,987-65-4321,456 Oak Ave Melbourne  
3,Robert Johnson,rob@email.com,+61 3 654 321,456-78-9012,789 Pine St Sydney
4,Sarah Davis,sarah.davis@corp.com,+61 7 987 654,789-01-2345,321 Elm St Perth
5,Michael Brown,mike@domain.org,+61 8 321 987,234-56-7890,654 Maple Ave Adelaide
6,Emily Wilson,emily.w@site.net,+61 467 123 456,567-89-0123,987 Cedar Ln Canberra
7,David Miller,d.miller@example.net,+61 3 789 012,890-12-3456,147 Birch Dr Darwin
8,Lisa Taylor,lisa@company.au,+61 421 654 987,345-67-8901,258 Spruce St Hobart"""

SAMPLE_JSON_DATA = {
    "users": [
        {"id": 1, "name": "John Smith", "email": "john.smith@example.com", "phone": "+61 2 345 678"},
        {"id": 2, "name": "Jane Doe", "email": "jane.doe@company.com", "phone": "+61 456 789 012"},
        {"id": 3, "name": "Robert Johnson", "email": "rob@email.com", "phone": "+61 3 654 321"}
    ]
}