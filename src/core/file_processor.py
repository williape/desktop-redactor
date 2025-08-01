import pandas as pd
import json
import chardet
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

class FileProcessor:
    """Handles CSV, JSON, and TXT file processing"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, presidio_manager):
        self.presidio_manager = presidio_manager
        
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate file size and format"""
        path = Path(file_path)
        
        if not path.exists():
            return False, "File does not exist"
            
        if path.stat().st_size > self.MAX_FILE_SIZE:
            # Don't block processing, just warn
            return True, f"File size ({path.stat().st_size / (1024*1024):.1f} MB) exceeds 10MB limit"
            
        if path.suffix.lower() not in ['.csv', '.json', '.txt', '.text']:
            return False, "File must be CSV, JSON, or TXT format"
            
        return True, "Valid"
        
    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding with fallback strategy"""
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Test read
            return 'utf-8'
        except UnicodeDecodeError:
            pass
            
        # Try ISO-8859-1 fallback
        try:
            with open(file_path, 'r', encoding='iso-8859-1') as f:
                f.read(1024)  # Test read
            return 'iso-8859-1'
        except UnicodeDecodeError:
            pass
            
        # Use chardet as last resort
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                if result['encoding'] and result['confidence'] > 0.7:
                    return result['encoding']
        except Exception as e:
            logging.warning(f"Chardet encoding detection failed: {e}")
            
        # Default fallback
        return 'utf-8'
        
    def process_csv(self, file_path: str, columns: Optional[List[str]], 
                   entities: List[str], confidence: float,
                   operator_config: Dict) -> pd.DataFrame:
        """Process CSV file with encoding fallback"""
        encoding = self._detect_encoding(file_path)
        logging.info(f"Processing CSV with encoding: {encoding}")
        
        try:
            df = pd.read_csv(file_path, encoding=encoding)
        except Exception as e:
            logging.error(f"Failed to read CSV with {encoding}: {e}")
            # Final fallback to utf-8 with error handling
            df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
            
        # Select columns to process
        if columns:
            cols_to_process = [col for col in columns if col in df.columns]
        else:
            # Process all string columns by default
            cols_to_process = df.select_dtypes(include=['object']).columns.tolist()
            
        # Process each selected column
        for col in cols_to_process:
            if col in df.columns:
                logging.info(f"Processing column: {col}")
                df[col] = df[col].apply(
                    lambda x: self._anonymize_value(
                        str(x), entities, confidence, operator_config
                    ) if pd.notna(x) and str(x).strip() else x
                )
                
        return df
        
    def process_json(self, file_path: str, paths: Optional[List[str]],
                    entities: List[str], confidence: float,
                    operator_config: Dict) -> Dict:
        """Process JSON file with encoding fallback"""
        encoding = self._detect_encoding(file_path)
        logging.info(f"Processing JSON with encoding: {encoding}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to read JSON with {encoding}: {e}")
            # Final fallback
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
            
        # If no paths specified, process all string values recursively
        if not paths:
            return self._process_json_recursive(
                data, entities, confidence, operator_config
            )
        else:
            # Process only specified paths
            for path in paths:
                self._process_json_path(
                    data, path, entities, confidence, operator_config
                )
            return data
    
    def process_txt(self, file_path: str, entities: List[str], 
                   confidence: float, operator_config: Dict) -> str:
        """Process TXT file with encoding fallback"""
        encoding = self._detect_encoding(file_path)
        logging.info(f"Processing TXT with encoding: {encoding}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Failed to read TXT with {encoding}: {e}")
            # Final fallback to utf-8 with error handling
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        
        # Process the entire text content
        return self._anonymize_value(content, entities, confidence, operator_config)
            
    def _anonymize_value(self, text: str, entities: List[str],
                        confidence: float, operator_config: Dict) -> str:
        """Anonymize a single text value"""
        if not text or not isinstance(text, str) or not text.strip():
            return text
            
        results = self.presidio_manager.analyze_text(
            text, entities, confidence
        )
        
        if results:
            return self.presidio_manager.anonymize_text(
                text, results, operator_config
            )
        return text
        
    def _process_json_recursive(self, obj: Any, entities: List[str],
                               confidence: float, operator_config: Dict) -> Any:
        """Recursively process JSON object"""
        if isinstance(obj, dict):
            return {
                key: self._process_json_recursive(value, entities, confidence, operator_config)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [
                self._process_json_recursive(item, entities, confidence, operator_config)
                for item in obj
            ]
        elif isinstance(obj, str):
            return self._anonymize_value(obj, entities, confidence, operator_config)
        else:
            return obj
            
    def _process_json_path(self, data: Dict, path: str, entities: List[str],
                          confidence: float, operator_config: Dict):
        """Process specific JSON path"""
        # Simple path processing - can be enhanced for complex paths
        keys = path.split('.')
        current = data
        
        try:
            # Navigate to parent of target
            for key in keys[:-1]:
                if key.startswith('[') and key.endswith(']'):
                    # Array index
                    index = int(key[1:-1])
                    current = current[index]
                else:
                    current = current[key]
                    
            # Process the final key
            final_key = keys[-1]
            if final_key.startswith('[') and final_key.endswith(']'):
                # Array index
                index = int(final_key[1:-1])
                if isinstance(current[index], str):
                    current[index] = self._anonymize_value(
                        current[index], entities, confidence, operator_config
                    )
            else:
                if isinstance(current[final_key], str):
                    current[final_key] = self._anonymize_value(
                        current[final_key], entities, confidence, operator_config
                    )
        except (KeyError, IndexError, ValueError) as e:
            logging.warning(f"Could not process JSON path '{path}': {e}")
            
    def save_csv(self, df: pd.DataFrame, output_path: str):
        """Save DataFrame to CSV file"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        
    def save_json(self, data: Dict, output_path: str):
        """Save data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_txt(self, content: str, output_path: str):
        """Save content to TXT file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def get_csv_columns(self, file_path: str) -> List[str]:
        """Get column names from CSV file"""
        encoding = self._detect_encoding(file_path)
        try:
            df = pd.read_csv(file_path, encoding=encoding, nrows=0)  # Read only headers
            return df.columns.tolist()
        except Exception as e:
            logging.error(f"Failed to get CSV columns: {e}")
            return []
            
    def get_json_structure(self, file_path: str) -> Dict:
        """Get JSON structure for path selection"""
        encoding = self._detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            return data
        except Exception as e:
            logging.error(f"Failed to get JSON structure: {e}")
            return {}