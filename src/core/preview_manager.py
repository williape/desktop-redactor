import pandas as pd
import json
import logging
from typing import Optional, Tuple, Dict, Any, List
from .presidio_manager import PresidioManager
from .findings_model import FindingsCollection
from .file_processor import FileProcessor
import chardet

class PreviewManager:
    """Manages preview data generation and processing"""
    
    def __init__(self, presidio_manager: PresidioManager):
        self.presidio_manager = presidio_manager
        self.file_processor = FileProcessor(presidio_manager)
        self.current_file_path: Optional[str] = None
        self.sample_data: Optional[str] = None
        self.processed_data: Optional[str] = None
        self.findings: Optional[FindingsCollection] = None
        self.file_format: Optional[str] = None
        self.sample_size = 15  # Number of rows to sample for preview
        
    def load_file_sample(self, file_path: str) -> Tuple[bool, str]:
        """
        Load a sample of the file for preview
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            Tuple of (success, sample_data_or_error_message)
        """
        try:
            self.current_file_path = file_path
            
            # Determine file format
            if file_path.lower().endswith('.csv'):
                self.file_format = 'csv'
                return self._load_csv_sample(file_path)
            elif file_path.lower().endswith('.json'):
                self.file_format = 'json'
                return self._load_json_sample(file_path)
            elif file_path.lower().endswith('.txt') or file_path.lower().endswith('.text'):
                self.file_format = 'txt'
                return self._load_txt_sample(file_path)
            else:
                return False, f"Unsupported file format: {file_path}"
                
        except Exception as e:
            logging.error(f"Error loading file sample: {e}")
            return False, f"Error loading file: {str(e)}"
    
    def _load_csv_sample(self, file_path: str) -> Tuple[bool, str]:
        """Load sample data from CSV file"""
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read the CSV file with sample size limit
            df = pd.read_csv(file_path, encoding=encoding, nrows=self.sample_size)
            
            # Convert to string representation
            self.sample_data = df.to_csv(index=False)
            
            return True, self.sample_data
            
        except Exception as e:
            logging.error(f"Error loading CSV sample: {e}")
            return False, f"Error reading CSV: {str(e)}"
    
    def _load_json_sample(self, file_path: str) -> Tuple[bool, str]:
        """Load sample data from JSON file"""
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read the JSON file
            with open(file_path, 'r', encoding=encoding) as file:
                data = json.load(file)
            
            # Sample the data if it's a list
            if isinstance(data, list) and len(data) > self.sample_size:
                sampled_data = data[:self.sample_size]
            elif isinstance(data, dict):
                # For dict data, sample nested lists if they exist
                sampled_data = self._sample_nested_dict(data, self.sample_size)
            else:
                sampled_data = data
            
            # Convert to formatted JSON string
            self.sample_data = json.dumps(sampled_data, indent=2, ensure_ascii=False)
            
            return True, self.sample_data
            
        except Exception as e:
            logging.error(f"Error loading JSON sample: {e}")
            return False, f"Error reading JSON: {str(e)}"
    
    def _load_txt_sample(self, file_path: str) -> Tuple[bool, str]:
        """Load sample data from TXT file"""
        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)
            
            # Read the TXT file
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            # For preview, limit to first portion of text (around 2000 characters)
            preview_limit = 2000
            if len(content) > preview_limit:
                preview_content = content[:preview_limit] + "\n\n... (content truncated for preview)"
            else:
                preview_content = content
            
            self.sample_data = preview_content
            
            return True, self.sample_data
            
        except Exception as e:
            logging.error(f"Error loading TXT sample: {e}")
            return False, f"Error reading TXT: {str(e)}"
    
    def _sample_nested_dict(self, data: Dict, sample_size: int) -> Dict:
        """Sample nested dictionary data"""
        sampled = {}
        for key, value in data.items():
            if isinstance(value, list) and len(value) > sample_size:
                sampled[key] = value[:sample_size]
            elif isinstance(value, dict):
                sampled[key] = self._sample_nested_dict(value, sample_size)
            else:
                sampled[key] = value
        return sampled
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                
                # Fallback to utf-8 if detection is uncertain
                if result.get('confidence', 0) < 0.7:
                    encoding = 'utf-8'
                    
                logging.debug(f"Detected encoding: {encoding} (confidence: {result.get('confidence', 0):.2f})")
                return encoding
                
        except Exception as e:
            logging.warning(f"Encoding detection failed: {e}, using utf-8")
            return 'utf-8'
    
    def process_preview(self, entities: List[str], confidence: float = 0.7, 
                       operation: str = "replace", detailed_analysis: bool = False) -> Tuple[bool, str, FindingsCollection]:
        """
        Process the current sample data with specified settings
        
        Args:
            entities: List of entity types to detect
            confidence: Minimum confidence threshold
            operation: Processing operation to apply
            detailed_analysis: Whether to enable decision process tracing
            
        Returns:
            Tuple of (success, processed_data_or_error, findings_collection)
        """
        if not self.sample_data:
            return False, "No sample data loaded", FindingsCollection()
        
        try:
            # Convert data to text for analysis
            if self.file_format == 'csv':
                analysis_text = self._csv_to_analysis_text(self.sample_data)
            elif self.file_format == 'json':
                analysis_text = self._json_to_analysis_text(self.sample_data)
            else:
                analysis_text = self.sample_data
            
            # Process with Presidio
            processed_text, findings = self.presidio_manager.process_text_with_findings(
                analysis_text, entities, confidence, operation, detailed_analysis
            )
            
            # Convert back to structured format if needed
            if self.file_format == 'csv':
                self.processed_data = self._analysis_text_to_csv(processed_text, self.sample_data)
            elif self.file_format == 'json':
                self.processed_data = self._analysis_text_to_json(processed_text, self.sample_data)
            else:
                self.processed_data = processed_text
            
            self.findings = findings
            
            return True, self.processed_data, findings
            
        except Exception as e:
            logging.error(f"Error processing preview: {e}")
            return False, f"Processing error: {str(e)}", FindingsCollection()
    
    def _csv_to_analysis_text(self, csv_data: str) -> str:
        """Convert CSV data to text for analysis"""
        try:
            # Parse CSV and extract text content
            lines = csv_data.strip().split('\n')
            if not lines:
                return ""
            
            # Join all lines with newlines for analysis
            return '\n'.join(lines)
            
        except Exception as e:
            logging.error(f"Error converting CSV to analysis text: {e}")
            return csv_data
    
    def _json_to_analysis_text(self, json_data: str) -> str:
        """Convert JSON data to text for analysis"""
        try:
            # Parse JSON and extract text values
            data = json.loads(json_data)
            text_values = []
            
            def extract_text_values(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        extract_text_values(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        extract_text_values(item, f"{path}[{i}]")
                elif isinstance(obj, str):
                    text_values.append(obj)
                elif obj is not None:
                    text_values.append(str(obj))
            
            extract_text_values(data)
            return '\n'.join(text_values)
            
        except Exception as e:
            logging.error(f"Error converting JSON to analysis text: {e}")
            return json_data
    
    def _analysis_text_to_csv(self, processed_text: str, original_csv: str) -> str:
        """Convert processed text back to CSV format"""
        try:
            # For CSV, we'll return the processed text as-is since it maintains structure
            return processed_text
            
        except Exception as e:
            logging.error(f"Error converting analysis text to CSV: {e}")
            return original_csv
    
    def _analysis_text_to_json(self, processed_text: str, original_json: str) -> str:
        """Convert processed text back to JSON format"""
        try:
            # For JSON, this is more complex - for now return formatted processed text
            # In a full implementation, we'd need to map changes back to JSON structure
            return processed_text
            
        except Exception as e:
            logging.error(f"Error converting analysis text to JSON: {e}")
            return original_json
    
    def get_sample_data(self) -> Optional[str]:
        """Get the current sample data"""
        return self.sample_data
    
    def get_processed_data(self) -> Optional[str]:
        """Get the current processed data"""
        return self.processed_data
    
    def get_findings(self) -> Optional[FindingsCollection]:
        """Get the current findings"""
        return self.findings
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the current file"""
        return {
            'file_path': self.current_file_path,
            'file_format': self.file_format,
            'has_sample': self.sample_data is not None,
            'has_processed': self.processed_data is not None,
            'has_findings': self.findings is not None and len(self.findings.findings) > 0,
            'sample_size': self.sample_size
        }
    
    def clear(self):
        """Clear all preview data"""
        self.current_file_path = None
        self.sample_data = None
        self.processed_data = None
        self.findings = None
        self.file_format = None
    
    def refresh_preview(self, entities: List[str], confidence: float = 0.7, 
                       operation: str = "replace") -> Tuple[bool, str]:
        """
        Refresh the preview with current settings
        
        Args:
            entities: List of entity types to detect
            confidence: Minimum confidence threshold
            operation: Processing operation to apply
            
        Returns:
            Tuple of (success, message)
        """
        if not self.current_file_path:
            return False, "No file loaded"
        
        # Reload sample data
        success, message = self.load_file_sample(self.current_file_path)
        if not success:
            return False, f"Failed to reload sample: {message}"
        
        # Process with new settings
        success, processed_data, findings = self.process_preview(entities, confidence, operation)
        if not success:
            return False, f"Failed to process preview: {processed_data}"
        
        return True, "Preview refreshed successfully"
    
    def get_sample_statistics(self) -> Dict[str, Any]:
        """Get statistics about the sample data"""
        if not self.sample_data:
            return {}
        
        stats = {
            'sample_size_bytes': len(self.sample_data),
            'file_format': self.file_format
        }
        
        if self.file_format == 'csv':
            try:
                lines = self.sample_data.strip().split('\n')
                stats.update({
                    'rows': len(lines) - 1 if lines else 0,  # Subtract header
                    'columns': len(lines[0].split(',')) if lines else 0
                })
            except:
                pass
        elif self.file_format == 'json':
            try:
                data = json.loads(self.sample_data)
                if isinstance(data, list):
                    stats['items'] = len(data)
                elif isinstance(data, dict):
                    stats['keys'] = len(data.keys())
            except:
                pass
        
        return stats