# Acknowledgements

The Desktop Redactor project is built upon the exceptional work of numerous open-source projects and their contributors. We extend our sincere gratitude to the following:

## Core Frameworks

### Microsoft Presidio
- **Project**: [Microsoft Presidio](https://github.com/microsoft/presidio)
- **License**: MIT License
- **Contribution**: The foundation of our PII detection and anonymization capabilities. Presidio's sophisticated analyzer and anonymizer engines enable accurate identification and secure redaction of personally identifiable information across multiple entity types.
- **Components Used**: presidio-analyzer, presidio-anonymizer
- **Special Thanks**: To the Microsoft team for creating and maintaining this robust privacy engineering framework that makes enterprise-grade PII protection accessible to developers worldwide.

### PyQt5
- **Project**: [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- **License**: GPL v3 / Commercial License
- **Contribution**: Powers our desktop user interface with native platform integration and responsive design. PyQt5's comprehensive widget library and threading capabilities enable our modern sidebar layout and real-time preview functionality.
- **Special Thanks**: To Riverbank Computing for maintaining this excellent Python binding for the Qt framework, enabling cross-platform desktop application development with professional-grade UI components.

### spaCy
- **Project**: [spaCy](https://github.com/explosion/spaCy)
- **License**: MIT License
- **Contribution**: Provides the natural language processing foundation for Presidio's entity recognition. The en_core_web_lg model enables sophisticated text analysis and pattern recognition crucial for accurate PII detection.
- **Special Thanks**: To Explosion AI for developing this industrial-strength NLP library that combines speed, accuracy, and ease of use for real-world applications.

## Essential Libraries

### pandas
- **Project**: [pandas](https://github.com/pandas-dev/pandas)
- **License**: BSD 3-Clause License
- **Contribution**: Handles CSV data processing with robust encoding detection and efficient data manipulation capabilities.

### chardet
- **Project**: [chardet](https://github.com/chardet/chardet)
- **License**: LGPL v2.1
- **Contribution**: Provides reliable character encoding detection for processing files with various encodings, ensuring data integrity across different file sources.

## Development and Build Tools

### PyInstaller
- **Project**: [PyInstaller](https://github.com/pyinstaller/pyinstaller)
- **License**: GPL v2 / PyInstaller Bootloader Exception
- **Contribution**: Enables creation of standalone executable applications, making distribution seamless for end users without requiring Python installation.

### create-dmg
- **Project**: [create-dmg](https://github.com/sindresorhus/create-dmg)
- **License**: MIT License
- **Contribution**: Provides professional macOS DMG installer creation with customizable layouts and user-friendly installation experience.

## Security and Cryptography

### cryptography
- **Project**: [cryptography](https://github.com/pyca/cryptography)
- **License**: Apache License 2.0 / BSD License
- **Contribution**: Powers our AES encryption capabilities for secure PII anonymization, with PBKDF2 key derivation and secure memory handling.

## Additional Dependencies

We also acknowledge the following libraries that contribute to the project's functionality:

- **Qt Framework**: The underlying GUI framework that PyQt5 wraps
- **Python Standard Library**: For core functionality including threading, logging, and file operations
- **setuptools**: For packaging and distribution support
- **wheel**: For efficient package installation

## Community and Inspiration

### Open Source Community
We are grateful to the broader open-source community whose collaborative spirit and shared knowledge make projects like this possible. The extensive documentation, examples, and community support surrounding these projects have been invaluable.

### Privacy Engineering Field
Thanks to researchers and practitioners in privacy engineering who continue to advance the field of automated PII detection and protection, making privacy-preserving data analysis more accessible.

## License Compliance

This project respects all licensing requirements of its dependencies. Users should ensure compliance with all relevant licenses when distributing or modifying this software.

---

*The Presidio Desktop Redactor project stands on the shoulders of giants. We are committed to contributing back to the open-source ecosystem that has made this work possible.*