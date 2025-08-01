# Presidio Desktop Redactor - User Guide

## Installation

1. **Download**: Download the `Presidio Desktop Redactor.dmg` file
2. **Mount**: Double-click the DMG file to mount it
3. **Install**: Drag the "Presidio Desktop Redactor.app" to the Applications folder link
4. **Launch**: Open Applications and double-click "Presidio Desktop Redactor"

> **Note**: On first launch, macOS may show a security warning. Click "Open" to allow the application to run.

## Using the Application

The application features a modern sidebar interface with real-time previews and comprehensive findings analysis.

### Step 1: Load a File
- **Drag & Drop**: Drag a CSV, JSON, or TXT file onto the main content area
- **Browse**: Click "Browse Files..." to select a file
- **Supported Formats**: CSV, JSON, and TXT files up to 10MB
  - **CSV**: Comma-separated value files (.csv)
  - **JSON**: JavaScript Object Notation files (.json)
  - **TXT**: Plain text files (.txt, .text)
- **Live Preview**: Source data preview appears automatically after loading

### Step 2: Configure Detection (Sidebar)
- **Select Entities**: Choose which types of personal information to detect:
  - **Personal**: Names, emails, phone numbers
  - **Australian**: ABN, ACN, TFN, Medicare numbers, DVA numbers, CRN numbers, Passport numbers, Driver's License numbers
  - **Financial**: Credit cards
  - **Technical**: IP addresses, URLs
  - Use "Select All" button for convenience
  - **Collapsible Interface**: Click "Show & Select Entities" to expand/collapse the entity list for better space management

- **Acceptance Threshold**: Adjust the confidence slider (0.0-1.0)
  - Higher values = more precise detection, may miss some items
  - Lower values = broader detection, may include false positives
  - Default: 0.70 (recommended)

- **NER Model**: Choose the Natural Language Recognition model
  - **Bundled Models** (included with application):
    - spaCy/en_core_web_md (default, balanced performance)
    - spaCy/en_core_web_sm (fastest, basic accuracy)
  - **Import Additional Models** using the "Import..." button:
    - spaCy/en_core_web_lg (most accurate, requires manual import)
    - Transformers models (BERT, RoBERTa, etc.)
    - Flair models (state-of-the-art sequence labeling)
    - Stanza models (Stanford NLP multilingual)

### Step 3: Choose De-identification Method (Sidebar)
- **Replace**: Replaces detected PII with `<REDACTED>` (default)
  - Example: "John Doe → <REDACTED>"
- **Redact**: Removes detected PII completely
  - Example: "John Doe → ████████"
- **Mask**: Replaces detected PII with asterisks
  - Example: "John Doe → J*** D**"
- **Hash**: Replaces detected PII with cryptographic hash values
  - Example: "John Doe → a1b2c3d4"
- **Encrypt**: Encrypts detected PII with AES-256-GCM
  - Example: "John Doe → U2FsdGVk..."
  - Requires encryption key setup when selected

## How the Application Works

The Presidio Desktop Redactor uses Microsoft's Presidio framework to automatically detect and redact personally identifiable information (PII) from your files. Here's what happens:

1. **File Analysis**: The application scans your file content using advanced natural language processing
2. **Entity Detection**: It identifies various types of PII using pattern matching and machine learning models
3. **Confidence Scoring**: Each detection receives a confidence score (0.0-1.0) indicating certainty
4. **Data Processing**: Detected PII is replaced, redacted, masked, hashed, or encrypted based on your settings
5. **Output Generation**: A new file is created with the processed data, preserving the original format

## Importing Additional NER Models

The application supports multiple NLP frameworks for enhanced entity detection:

### Quick Import Process
1. **Click "Import..."** next to the NER Model dropdown
2. **Select Framework**: Choose spaCy, Transformers, Flair, or Stanza
3. **Browse Model Path**: Select the downloaded model directory
4. **Import**: The application validates and adds the model to your collection

### Where to Get Models

**spaCy Models (Recommended):**
- Download via command line: `python -m spacy download en_core_web_lg`
- Visit: https://spacy.io/models/en for all English models
- Most accurate for general PII detection

**Hugging Face Transformers:**
- Visit: https://huggingface.co/models?pipeline_tag=token-classification
- Popular models: `dbmdz/bert-large-cased-finetuned-conll03-english`, `dslim/bert-base-NER`
- Best for specialized domain detection

**Flair Models:**
- Visit: https://github.com/flairNLP/flair/blob/master/resources/docs/MODELS.md
- State-of-the-art sequence labeling performance
- Requires more processing time but higher accuracy

**Stanza Models:**
- Visit: https://stanfordnlp.github.io/stanza/models.html
- Multilingual support with robust NER capabilities
- Good for non-English content

### Model Storage
Models are stored in: `~/Documents/PresidioDesktopRedactor/models/`

## Step 4: Review and Process
- **Output Preview**: See processed data in real-time as you adjust settings
- **Findings Table**: Review all detected entities with comprehensive details:
  - **Basic View**: Entity Type, Text, Position, Confidence, Recognizer, Pattern Name, Pattern
  - **Detailed Analysis**: Toggle "Show detailed analysis" for additional decision process information:
    - Original Score, Score, Textual Explanation, Score Context Improvement
    - Supportive Context Word, Validation Result, Regex Flags
  - **Enhanced Row Selection**: Improved highlighting when clicking on table rows
  - **Pattern Visibility**: View actual regex patterns used for PII detection
  - **Export Functionality**: Export findings table data to CSV for further analysis
  - Use confidence filter to focus on high-confidence findings
  - Sort by any column or search for specific text
- **Process File**: Click "Start Processing" in the action bar
- **Progress Tracking**: Watch the progress bar for processing status
- **Output**: Processed file saved to your Desktop with timestamp
- **Format**: `filename_redacted_YYYYMMDD_HHMMSS.[csv|json|txt]` (preserves original format)

## Key Features

### What Can Be Detected
The application recognizes these types of personally identifiable information:

**Standard PII:**
- **Person Names**: Full names and name components
- **Email Addresses**: All standard email formats
- **Phone Numbers**: International and local formats
- **Credit Cards**: Major card number formats
- **IP Addresses**: IPv4 and IPv6 addresses
- **URLs**: Web addresses and links

**Australian-Specific PII:**
- **Australian Business Numbers (ABN)**: 11-digit format with validation
- **Australian Company Numbers (ACN)**: 9-digit format
- **Tax File Numbers (TFN)**: Australian tax identification
- **Medicare Numbers**: Australian Medicare card numbers
- **Medicare Provider Numbers**: Healthcare provider identification
- **DVA File Numbers**: Department of Veterans' Affairs numbers
- **Centrelink Customer Reference Numbers (CRN)**: Centrelink reference numbers
- **Passport Numbers**: Australian format (1-2 letters + 7 digits)
- **Driver's License Numbers**: State-specific formats (6-10 digits or alphanumeric)

### Custom Australian Entity Recognition
Enhanced patterns specifically designed for Australian data:
- **Mobile Numbers**: 04XX XXX XXX format with validation
- **Landline Numbers**: State-based area codes (02, 03, 07, 08)
- **Medicare Providers**: 6-digit provider + location + check digit validation
- **DVA Numbers**: State codes + war service codes + sequence validation
- **CRN Numbers**: State codes + 8 digits + check digit + optional dependent

### Core Processing Features
- **Multiple File Formats**: CSV, JSON, and TXT files up to 10MB
- **Real-Time Preview**: See changes instantly as you adjust settings
- **Background Processing**: Interface remains responsive during processing
- **Format Preservation**: Original file structure maintained in output
- **Secure Processing**: All processing happens locally, no data sent externally
- **Timestamped Output**: Prevents accidental file overwrites

### Analysis and Insights
- **Findings Table**: Comprehensive view of all detected entities
- **Confidence Scoring**: Each detection includes certainty percentage
- **Pattern Visibility**: View actual regex patterns used for detection
- **Decision Process**: Toggle detailed analysis to see detection reasoning
- **Export Capabilities**: Save findings analysis to CSV for further review
- **Interactive Filtering**: Filter by confidence, entity type, or text search

## Troubleshooting

### File Size Warning
- Files larger than 10MB will show a warning but processing will continue
- Very large files may take longer to process

### Supported File Formats
- **CSV**: Comma-separated values with UTF-8 or ISO-8859-1 encoding
- **JSON**: JavaScript Object Notation with nested structures supported
- **TXT**: Plain text files (.txt, .text) with automatic encoding detection

### Common Issues
1. **File Won't Load**
   - Ensure file is CSV, JSON, or TXT format
   - Check file isn't corrupted or password-protected

2. **No PII Detected**
   - Lower the acceptance threshold
   - Verify the entity types are selected
   - Check if the data format matches expected patterns

3. **Application Won't Start**
   - Check macOS version compatibility (10.14+)
   - Try running from Applications folder, not the DMG

4. **Preview Not Updating**
   - Ensure file is loaded successfully
   - Check that entities are selected in the sidebar
   - Try adjusting confidence threshold

5. **Findings Table Empty**
   - Lower the confidence threshold
   - Verify entity types are selected
   - Check if the loaded file contains expected PII patterns
   - Try toggling "Show detailed analysis" for additional detection information

6. **Export Not Working**
   - Ensure findings table has data
   - Check file write permissions in selected directory
   - Try exporting in both basic and detailed modes

7. **Pattern Column Shows "None"**
   - Some entities use statistical NLP models rather than regex patterns
   - Toggle detailed analysis mode for more pattern information
   - Built-in recognizers may not expose pattern details

8. **Model Import Failed**
   - Ensure the selected directory contains a valid model structure
   - Check framework-specific requirements (meta.json for spaCy, config.json for Transformers)
   - Verify framework dependencies are installed (pip install transformers torch)
   - Try importing a different model format

9. **Framework Not Available**
   - Install required dependencies: `pip install [framework] torch`
   - Restart the application after installing new frameworks
   - Check if the framework appears in the Import dialog

10. **Model Loading Error**
    - Verify model compatibility with your system architecture
    - Check available memory (some models require 4GB+ RAM)
    - Try switching to a smaller bundled model
    - Check application logs for detailed error messages

11. **Poor Detection Quality**
    - Try a larger, more accurate model (en_core_web_lg vs en_core_web_sm)
    - Adjust confidence threshold to capture more entities
    - Consider using Transformer models for better accuracy
    - Check if your text format matches the model's training data

### Debug Mode
For detailed logging and troubleshooting:
1. Open Terminal
2. Navigate to Applications
3. Run: `./Presidio\ Desktop\ Redactor.app/Contents/MacOS/Presidio\ Desktop\ Redactor --debug`
4. Check logs at: `~/Documents/PresidioDesktopRedactor/logs/app.log`

## Privacy & Security

- **No Data Retention**: Files are processed locally, no data sent to external servers
- **Original Files Protected**: Input files are never modified
- **Secure Processing**: All processing happens in memory
- **Timestamped Output**: Prevents accidental overwrites

## Technical Requirements

- **macOS**: 10.14 (Mojave) or later
- **Architecture**: Intel or Apple Silicon (Universal)
- **Memory**: 4GB RAM recommended (8GB+ for Transformer models)
- **Storage**: 2GB free space for application and model storage
- **Python Dependencies** (for model management):
  - Optional: `pip install transformers torch` for Transformer models
  - Optional: `pip install flair torch` for Flair models
  - Optional: `pip install stanza` for Stanza models

## External Resources & References

### Official Documentation
- **Microsoft Presidio**: https://microsoft.github.io/presidio/
  - Core PII detection and anonymization engine
  - Entity recognizer documentation
  - Anonymization methods reference

### NLP Model Resources
- **spaCy Models**: https://spacy.io/models/en
  - Pre-trained language models for entity recognition
  - Installation guides and model comparisons
  
- **Hugging Face Transformers**: https://huggingface.co/models?pipeline_tag=token-classification
  - State-of-the-art transformer models for NER
  - Model cards with performance metrics
  
- **Flair NLP**: https://github.com/flairNLP/flair/blob/master/resources/docs/MODELS.md
  - Contextual string embeddings for sequence labeling
  - Pre-trained models and training guides
  
- **Stanford Stanza**: https://stanfordnlp.github.io/stanza/models.html
  - Multilingual NLP pipeline with robust NER
  - Language-specific model downloads

### Privacy and Security Standards
- **Australian Privacy Principles**: https://www.oaic.gov.au/privacy/australian-privacy-principles
- **GDPR Compliance**: https://gdpr-info.eu/
- **Data Classification Guidelines**: https://www.cyber.gov.au/acsc/view-all-content/publications/protective-security-policy-framework-data-classification

## Support

For issues or questions:
- Check application logs: `~/Documents/PresidioDesktopRedactor/logs/app.log`
- Review the troubleshooting section above
- Ensure you're using supported file formats and sizes

---

**Version**: 1.5
**Last Updated**: July 2025