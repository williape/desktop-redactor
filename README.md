# Presidio Desktop Redactor

A desktop application for automatically detecting and redacting personally identifiable information (PII) from CSV, JSON, and TXT files using Microsoft Presidio. Designed for data analysts who need to process sensitive data before analysis in external tools or LLM frameworks. The current build is tailored specifically for Australian data.

## 📋 Features

### Core Functionality
- **Real-Time Preview System**: Live source and output previews with instant updates
- **Comprehensive Findings Analysis**: Detailed findings table with sorting, filtering, and statistics
- **File Support**: CSV, JSON, and TXT files up to 10MB (soft limit with warning)
- **PII Detection**: 15 entity types including Australian-specific patterns
- **Background Processing**: Non-blocking UI with real-time progress tracking
- **Multiple Anonymization Methods**: Replace, Redact, Mask, Hash, Encrypt
- **Advanced Encryption**: AES-256-GCM encryption with PBKDF2 key derivation
- **Robust File Handling**: UTF-8 → ISO-8859-1 → chardet encoding fallback
- **Drag and Drop Interface**: browse for local or just drop files onto the app

### Supported PII Types
- **Personal**: Names, email addresses, phone numbers
- **Financial**: Credit card numbers, IP addresses, URLs
- **Australian Entities**: ABN, ACN, TFN, Medicare card numbers, Medicare provider numbers, DVA file numbers, Centrelink CRN numbers, Passport numbers, Driver's License numbers
- **Enhanced Recognition**: Custom Australian phone number patterns (mobile/landline) and postal addresses

### Advanced Features
- **Interactive Preview System**: Real-time source and output previews with entity highlighting
- **Enhanced Findings Analysis**: Comprehensive findings table with 8-15 columns of entity data
- **Decision Process Analysis**: Toggle detailed analysis to see Presidio's detection reasoning
- **Export Functionality**: Export findings table data to CSV for further analysis
- **Advanced Filtering**: Filter findings by confidence, entity type, and text search
- **Multiple NER Framework Support**: Leverage Named Entity Recognition (NER) models for context-aware PII detection - spaCy, Transformers, Flair, and Stanza
- **Encryption Support**: Secure AES-256-GCM encryption with user-provided or generated keys
- **Custom Lists**: Allowlist/denylist functionality for fine-tuned PII detection
- **Output Preservation**: Maintains original file structure with timestamped output

## 🏗️ Architecture

```
src/
├── main.py                     # Application entry point with logging setup
├── core/                       # Core processing components
│   ├── presidio_manager.py     # Presidio abstraction with multiple NLP engine support
│   ├── model_manager.py        # Model registry and validation 
│   ├── file_processor.py       # CSV, JSON, TXT file handling with encoding detection
│   ├── custom_recognizers.py   # Australian PII pattern recognizers
│   ├── encryption_manager.py   # AES-256-GCM encryption with key management
│   ├── list_manager.py         # Allowlist/denylist management
│   ├── preview_manager.py      # Preview data sampling and processing
│   ├── findings_model.py       # Findings data model and statistics
│   └── nlp_engines/            # Multiple NLP framework support 
│       ├── engine_factory.py   # NLP engine factory pattern
│       ├── flair_engine.py     # Flair framework integration
│       └── stanza_engine.py    # Stanza framework integration
├── ui/                         # PyQt5 user interface
│   ├── main_window.py          # Main window with sidebar layout and model management
│   ├── styles.py               # Centralized styling system
│   ├── components/             # Advanced UI components
│   │   ├── preview_panel.py    # Source and output preview panels
│   │   └── findings_table.py   # Findings analysis table
│   └── widgets/                # Custom dialogs and components
│       ├── encryption_widget.py     # Encryption key management UI
│       ├── list_widget.py           # Custom list management UI
│       └── model_import_dialog.py   # Model import dialog 
└── utils/                      # Utility functions
    ├── logging_config.py       # Centralized logging configuration
    └── config_manager.py       # Application configuration persistence
```

## 🤖 NLP Model Management

### Supported Frameworks
The application supports multiple NLP frameworks for entity recognition:

- **spaCy**: Fast, production-ready models (bundled: sm, md), lg is optional
- **Transformers**: Hugging Face transformer models for advanced NER
- **Flair**: State-of-the-art sequence labeling models
- **Stanza**: Stanford NLP multilingual models

### Bundled Models
The application comes with these pre-installed models:
- **en_core_web_sm**: Small spaCy model (~13MB) - Fast processing
- **en_core_web_md**: Medium spaCy model (~43MB) - Balanced performance

#### Model Storage Location
All imported models are stored in:
```
~/Documents/PresidioDesktopRedactor/models/
├── spacy/          # spaCy models
├── transformers/   # Hugging Face models  
├── flair/          # Flair models
└── stanza/         # Stanza models
```

#### Where to Download Models

**spaCy Models:**
```bash
# Large model (recommended for best accuracy)
python -m spacy download en_core_web_lg

# Or download directly from GitHub releases:
# https://github.com/explosion/spacy-models/releases
```

**Hugging Face Transformers:**
- Visit: https://huggingface.co/models?pipeline_tag=token-classification
- Popular NER models:
  - `dbmdz/bert-large-cased-finetuned-conll03-english`
  - `dslim/bert-base-NER`
  - `microsoft/DialoGPT-medium`

**Flair Models:**
```bash
# Install Flair first
pip install flair

# Models download automatically, or visit:
# https://github.com/flairNLP/flair/blob/master/resources/docs/MODELS.md
```

**Stanza Models:**
```bash
# Install Stanza first
pip install stanza

# Download models
python -c "import stanza; stanza.download('en')"

# Or visit: https://stanfordnlp.github.io/stanza/models.html
```

#### How to Import Models

1. **Via Application UI:**
   - Open the application
   - In the sidebar, click "Import..." next to the NER Model dropdown
   - Select the framework and model directory
   - Click "Import" to validate and import

2. **Manual Import:**
   - Download model to any location
   - Copy to appropriate framework directory in `~/Documents/PresidioDesktopRedactor/models/`
   - Restart application or click refresh button

#### Framework Installation (Optional)
To use additional frameworks, install them separately:

```bash
# For Transformers support
pip install transformers torch

# For Flair support  
pip install flair torch

# For Stanza support
pip install stanza
```

### Model Validation
The application automatically validates imported models:
- **spaCy**: Checks for `meta.json` file
- **Transformers**: Checks for `config.json` file
- **Flair**: Checks for `.pt` model files
- **Stanza**: Checks for appropriate model structure

### Performance Considerations
- **Small models**: Faster processing, basic accuracy
- **Medium models**: Balanced performance (recommended)
- **Large models**: Best accuracy, slower processing
- **Transformer models**: Highest accuracy, requires more memory

## 🚀 Quick Start for Developers

### Prerequisites

- **macOS**: 10.14 (Mojave) or later
- **Python**: 3.8+ (3.13+ recommended)
- **Pip**: 3+
- **Homebrew**: For build dependencies

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd presidio-desktop-redactor

# Environment Setup
# Activate virtual environment (already configured)
source venv/bin/activate

# OR create new virtual environment if needed
python3 -m venv venv
source venv/bin/activate

# Install dependencies
# Assumes that PyQt5 was installed via Homebrew and commented out in requirements.txt file.
pip3 install -r requirements.txt

# Download required spaCy models (medium model listed, lg optional)
python3 -m spacy download en_core_web_md

## Run app in development mode
source venv/bin/activate && python3 src/main.py 

# Install build dependencies (macOS)
brew install create-dmg
```

### Development Workflow

```bash
# Run application in development mode
python3 src/main.py

# Run application with debug logging
python3 src/main.py --debug

# Run test suites
python3 test_core_processing.py
python3 test_ui_workflow.py
python3 test_complete_workflow.py
python3 test_processing_thread.py
python3 test_exception_handling.py
python3 test_phase3_components.py
python3 test_phase5_nlp_engines.py

# Build macOS application bundle and DMG
./build_mac.sh
```

## 🧪 Testing

### Test Structure
The project uses custom test scripts for integration-focused testing:

- **`test_core_processing.py`**: Core PresidioManager and FileProcessor functionality
- **`test_ui_workflow.py`**: UI components and dialog interactions
- **`test_complete_workflow.py`**: End-to-end file processing pipeline
- **`test_processing_thread.py`**: Background processing and threading
- **`test_exception_handling.py`**: Logging and error handling systems


### Test Data
Located in `tests/sample_files/`:
- **`test_simple.csv`**: Basic CSV with common PII patterns
- **`test_nested.json`**: Complex JSON with nested structures
- **`test_australian_data.csv`**: Australian-specific PII for custom recognizer testing

### Running Tests
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
python3 test_core_processing.py
python3 test_ui_workflow.py
python3 test_complete_workflow.py
python3 test_processing_thread.py
python3 test_exception_handling.py
python3 test_ui_extended_components.py
python3 test_nlp_engines.py
```

## 📦 Building & Distribution

### Build Process
The application uses PyInstaller for creating distributable packages:

```bash
# Build app bundle and DMG installer
./build_mac.sh

# Manual build (onedir mode recommended) - 
pyinstaller --clean --onedir --windowed \
    --name "Presidio Desktop Redactor" \
    --icon "src/resources/icons/app_icon.icns" \
    --add-data "venv/lib/python*/site-packages/spacy/lang:spacy/lang" \
    --add-data "venv/lib/python*/site-packages/en_core_web_sm:en_core_web_sm" \
    --add-data "venv/lib/python*/site-packages/en_core_web_md:en_core_web_md" \
    --hidden-import "spacy" \
    --hidden-import "presidio_analyzer" \
    --hidden-import "presidio_anonymizer" \
    --hidden-import "pandas" \
    --hidden-import "yaml" \
    src/main.py
```

### Deliverables
- **`dist/Presidio Desktop Redactor.app`**: macOS application bundle
- **`Presidio Desktop Redactor.dmg`**: Professional installer package (~250MB)
- **`Quick_Start_Guide.md`**: User documentation with model management guide

## 🔧 Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **PyQt5 5.15.11**: Cross-platform GUI framework
- **Microsoft Presidio**: PII detection and anonymization
  - presidio-analyzer 2.2.35
  - presidio-anonymizer 2.2.35
- **pandas 2.3.1**: CSV data processing
- **spaCy 3.8.7**: NLP processing with en_core_web_md model

### Development Tools
- **PyInstaller 6.3.0**: Application packaging
- **create-dmg**: macOS DMG installer creation
- **chardet 5.2.0**: Character encoding detection

## 📝 Configuration

### Logging Configuration
- **Default Level**: INFO
- **Debug Mode**: Use `--debug` flag for DEBUG level output
- **Log Location**: `~/Documents/PresidioDesktopRedactor/logs/app.log`
- **Log Rotation**: 10MB max size, 5 backup files
- **Exception Handling**: Global exception capture with user notifications

### File Processing Settings
- **File Size Limit**: 10MB (soft limit with warning)
- **Supported Formats**: CSV, JSON, TXT
- **Encoding Strategy**: UTF-8 → ISO-8859-1 → chardet detection
- **Output Naming**: `filename_redacted_YYYYMMDD_HHMMSS.ext`

### Model Management Settings
- **Model Storage**: `~/Documents/PresidioDesktopRedactor/models/`
- **Supported Frameworks**: spaCy, Transformers, Flair, Stanza
- **Bundled Models**: en_core_web_sm, en_core_web_md
- **Import Validation**: Automatic model structure validation
- **Configuration**: YAML-based model configuration templates

## 🎨 Custom Recognizers

The application includes custom recognizers for Australian PII patterns:

### Enhanced Phone Recognizer
- **Mobile**: 04XX XXX XXX patterns with validation
- **Landline**: State-based area codes (02, 03, 07, 08) with proper digit counts
- **Replaces**: Default Presidio phone recognizer for improved Australian support

### Medicare Provider Recognizer
- **Format**: 6-digit provider + 2-digit location + 1-digit check digit
- **Validation**: Location code validation and check digit algorithm
- **Coverage**: Australian healthcare provider identification

### DVA File Number Recognizer
- **Format**: State prefix + war service code + sequence number
- **Validation**: State code validation and war service code verification
- **Coverage**: Department of Veterans' Affairs file numbers

### Centrelink CRN Recognizer
- **Format**: State code (2-7) + 8 digits + check digit + optional dependant indicator
- **Validation**: State code validation, check digit algorithm verification
- **Coverage**: Australian Centrelink Customer Reference Numbers

### Australian Passport Numbers
- **Pattern**: 1-2 letters followed by exactly 7 digits
- **Validation**: Excludes confusing letters (O, S, Q, I)
- **Examples**: A1234567, PA1234567, N1234567
- **Score**: 0.9 confidence rating
- **Coverage**: Australian passport number identification

### Australian Driver's License Numbers
- **Patterns**: State-specific numeric and alphanumeric formats
- **Numeric**: 6-10 digits with optional delimiters (spaces/hyphens)
- **Alphanumeric**: 1-2 letters + 4-5 digits, or 4 digits + 2 letters
- **Examples**: 12345678, 123 456 789, A12345, AB1234, 1234AB, 1-234-567-890
- **Score**: 0.8 confidence rating
- **Coverage**: Australian state driver's license number identification

## 🔒 Security Considerations

### Data Handling
- **In-Memory Processing**: No temporary file creation
- **Original File Preservation**: Input files remain unchanged
- **Output Security**: Timestamped filenames prevent overwrites
- **Local Processing**: No data transmitted to external services
- **Encryption Security**: AES-256-GCM with secure key derivation (PBKDF2, 100k iterations)

### Encryption Features
- **Key Management**: Generate, import, export encryption keys securely
- **Key Validation**: Real-time strength assessment and security warnings
- **Secure Storage**: Optional encrypted key persistence for convenience
- **Algorithm**: AES-256-GCM (Galois/Counter Mode) for authenticated encryption
- **Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations, 256-bit salt

### Distribution Security
- **Code Signing**: Not implemented 
- **Notarization**: macOS requirement for broader distribution
- **Sandboxing**: Consider for App Store distribution

## 📊 Performance Characteristics

### Current Limitations
- **File Size**: 10MB soft limit (can process larger with warning)
- **Memory Usage**: Entire file loaded into memory
- **Processing**: Single-threaded analysis with UI separation

## 🛠️ Development Guidelines

### Code Organization
- **Separation of Concerns**: Clear UI, processing, and data layers
- **Testability**: Isolated components for integration testing
- **Error Handling**: Graceful degradation with user feedback
- **Documentation**: Comprehensive inline comments and docstrings

### PyQt5 Best Practices
- **Threading**: QThread for background operations
- **Memory Management**: Proper widget cleanup and lifecycle
- **Platform Integration**: Native look and feel
- **Signal/Slot Architecture**: Clean component communication

## 🔮 Future Enhancements

### Potential Enhancements
- **Per-Entity Rules**: Different anonymization methods per entity type
- **Batch Processing**: Multiple file handling
- **Profile Management**: Save/load configuration presets
- **Performance**: Support for files >10MB with chunking
- **Export Options**: Export findings and statistics to various formats

### Platform Expansion
- **Windows Support**: Adapt UI for Windows design language
- **Linux Support**: Potential future platform support

## 📚 Resources & References

### Documentation
- [Microsoft Presidio Documentation](https://microsoft.github.io/presidio/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [spaCy Documentation](https://spacy.io/api)

### Development Tools
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [create-dmg GitHub](https://github.com/sindresorhus/create-dmg)

## 🐛 Troubleshooting

### Common Issues

1. **spaCy Model Missing**
   ```bash
   python3 -m spacy download en_core_web_md
   ```

2. **PyQt5 Import Errors**
   ```bash
   source venv/bin/activate
   pip3 install PyQt5==5.15.11
   ```

3. **Build Failures**
   ```bash
   brew install create-dmg
   chmod +x build_mac.sh
   ```

4. **Application Won't Launch**
   - Check macOS version (10.14+ required)
   - Verify code signing permissions
   - Try running from Terminal for error messages

### Debug Mode
For detailed troubleshooting:
```bash
python3 src/main.py --debug
# Check logs at: ~/Documents/PresidioDesktopRedactor/logs/app.log
```

## 📄 License

The MIT License (MIT)

## 🤝 Contributing

This project is based directly on the [Microsoft Presidio project](https://github.com/microsoft/presidio/) and is not intended to be a commercial product.

---

**Version**: 1.7
**Last Updated**: July 2025  