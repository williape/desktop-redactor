"""
Stanza NLP Engine for Presidio integration.

This module provides a custom NLP engine that integrates Stanza models
with Microsoft Presidio for PII detection.
"""

import logging
from typing import List, Dict, Optional, Any
from presidio_analyzer.nlp_engine import NlpEngine, NlpArtifacts
from presidio_analyzer.nlp_engine.nlp_artifacts import NlpArtifacts as NlpArtifactsBase

try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False
    logging.warning("Stanza not available - StanzaNlpEngine will not function")
    # Create dummy stanza module to prevent import errors
    class stanza:
        class Pipeline:
            pass


class StanzaNlpArtifacts(NlpArtifactsBase):
    """Custom NLP artifacts for Stanza"""
    
    def __init__(self, doc: Any, language: str):
        self.doc = doc
        self.language = language
        super().__init__()
    
    @property
    def tokens(self) -> List[str]:
        """Get list of tokens"""
        if self.doc and hasattr(self.doc, 'sentences'):
            tokens = []
            for sentence in self.doc.sentences:
                for token in sentence.tokens:
                    tokens.append(token.text)
            return tokens
        return []
    
    @property
    def tokens_indices(self) -> List[tuple]:
        """Get list of token indices (start, end)"""
        if self.doc and hasattr(self.doc, 'sentences'):
            indices = []
            for sentence in self.doc.sentences:
                for token in sentence.tokens:
                    # Stanza tokens have start_char and end_char
                    start = getattr(token, 'start_char', 0)
                    end = getattr(token, 'end_char', len(token.text))
                    indices.append((start, end))
            return indices
        return []
    
    @property
    def lemmas(self) -> List[str]:
        """Get list of lemmas"""
        if self.doc and hasattr(self.doc, 'sentences'):
            lemmas = []
            for sentence in self.doc.sentences:
                for word in sentence.words:
                    lemmas.append(word.lemma or word.text)
            return lemmas
        return self.tokens  # Fallback to tokens
    
    @property
    def entities(self) -> List[Dict[str, Any]]:
        """Get list of entities"""
        entities = []
        if self.doc and hasattr(self.doc, 'entities'):
            for entity in self.doc.entities:
                entities.append({
                    'start': entity.start_char,
                    'end': entity.end_char,
                    'text': entity.text,
                    'label': entity.type,
                    'confidence': 1.0  # Stanza doesn't provide confidence scores by default
                })
        return entities


class StanzaNlpEngine(NlpEngine):
    """Custom NLP Engine using Stanza models"""
    
    def __init__(self, models: List[Dict], ner_model_configuration: Dict = None):
        """
        Initialize Stanza NLP Engine
        
        Args:
            models: List of model configurations
            ner_model_configuration: NER model configuration
        """
        super().__init__()
        
        if not STANZA_AVAILABLE:
            raise ImportError("Stanza is not available. Please install with: pip install stanza")
        
        self.models = {}
        self.ner_model_configuration = ner_model_configuration or {}
        self.entity_mapping = self._get_entity_mapping()
        
        # Load models
        self._load_models(models)
        
        logging.info(f"StanzaNlpEngine initialized with {len(self.models)} models")
    
    def _load_models(self, models: List[Dict]):
        """Load Stanza models"""
        for model_config in models:
            lang_code = model_config.get('lang_code', 'en')
            model_name = model_config.get('model_name', lang_code)
            
            try:
                # Configure processors - enable NER
                processors = 'tokenize,ner'
                
                # Create pipeline
                pipeline = stanza.Pipeline(
                    lang=lang_code,
                    processors=processors,
                    use_gpu=False,  # Use CPU by default for compatibility
                    verbose=False,
                    download_method=None  # Don't auto-download
                )
                
                self.models[lang_code] = pipeline
                logging.info(f"Loaded Stanza model for {lang_code}")
                
            except Exception as e:
                logging.error(f"Failed to load Stanza model for {lang_code}: {e}")
                # Try with basic configuration
                try:
                    pipeline = stanza.Pipeline(
                        lang=lang_code,
                        processors='tokenize,ner',
                        use_gpu=False,
                        verbose=False,
                        package=None,  # Use default package
                        download_method=None
                    )
                    self.models[lang_code] = pipeline
                    logging.info(f"Loaded Stanza model for {lang_code} with basic configuration")
                except Exception as e2:
                    logging.error(f"Failed to load Stanza model for {lang_code} with basic config: {e2}")
    
    def _get_entity_mapping(self) -> Dict[str, str]:
        """Get entity mapping from Stanza to Presidio entities"""
        default_mapping = {
            'PER': 'PERSON',
            'PERSON': 'PERSON',
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'GPE': 'LOCATION',
            'MISC': 'MISC',
            'MONEY': 'MONEY',
            'DATE': 'DATE_TIME',
            'TIME': 'DATE_TIME'
        }
        
        # Use configuration mapping if available
        if self.ner_model_configuration and 'entity_mapping' in self.ner_model_configuration:
            mapping = self.ner_model_configuration['entity_mapping']
            default_mapping.update(mapping)
        
        return default_mapping
    
    def process_text(self, text: str, language: str) -> NlpArtifacts:
        """
        Process text using Stanza models
        
        Args:
            text: Text to process
            language: Language code
            
        Returns:
            NlpArtifacts object with processing results
        """
        if not text or not isinstance(text, str):
            # Return empty artifacts for invalid input
            return StanzaNlpArtifacts(None, language)
        
        # Get model for language (fallback to 'en' if not available)
        model = self.models.get(language, self.models.get('en'))
        if not model:
            logging.warning(f"No Stanza model available for language: {language}")
            return StanzaNlpArtifacts(None, language)
        
        try:
            # Process text with Stanza
            doc = model(text)
            
            # Create artifacts
            artifacts = StanzaNlpArtifacts(doc, language)
            
            return artifacts
            
        except Exception as e:
            logging.error(f"Error processing text with Stanza: {e}")
            return StanzaNlpArtifacts(None, language)
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        # Return Presidio-mapped entity types
        return list(set(self.entity_mapping.values()))
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.models.keys())
    
    def is_available(self) -> bool:
        """Check if Stanza is available and models are loaded"""
        return STANZA_AVAILABLE and len(self.models) > 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        info = {
            'framework': 'stanza',
            'available': self.is_available(),
            'languages': self.get_supported_languages(),
            'entities': self.get_supported_entities(),
            'models': {}
        }
        
        for lang, model in self.models.items():
            model_info = {
                'language': lang,
                'type': type(model).__name__,
                'available': True,
                'processors': getattr(model, 'processors', [])
            }
            
            # Try to get model details
            try:
                if hasattr(model, 'config'):
                    model_info['config'] = model.config
            except Exception as e:
                logging.debug(f"Could not get config for Stanza model {lang}: {e}")
            
            info['models'][lang] = model_info
        
        return info
    
    def analyze_entities(self, text: str, language: str = 'en') -> List[Dict[str, Any]]:
        """
        Analyze text and return entities in Presidio format
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of entity dictionaries
        """
        artifacts = self.process_text(text, language)
        entities = []
        
        for entity_info in artifacts.entities:
            # Map Stanza entity type to Presidio entity type
            stanza_label = entity_info['label']
            presidio_label = self.entity_mapping.get(stanza_label, stanza_label)
            
            entities.append({
                'start': entity_info['start'],
                'end': entity_info['end'],
                'text': entity_info['text'],
                'entity_type': presidio_label,
                'confidence': entity_info['confidence'],
                'recognition_metadata': {
                    'recognizer_name': 'StanzaNlpEngine',
                    'original_label': stanza_label
                }
            })
        
        return entities
    
    def download_model(self, language: str) -> bool:
        """
        Download a Stanza model for a specific language
        
        Args:
            language: Language code to download
            
        Returns:
            True if successful, False otherwise
        """
        if not STANZA_AVAILABLE:
            return False
        
        try:
            stanza.download(language, verbose=False)
            logging.info(f"Downloaded Stanza model for {language}")
            
            # Try to load the downloaded model
            pipeline = stanza.Pipeline(
                lang=language,
                processors='tokenize,ner',
                use_gpu=False,
                verbose=False
            )
            
            self.models[language] = pipeline
            logging.info(f"Successfully loaded downloaded Stanza model for {language}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to download/load Stanza model for {language}: {e}")
            return False
    
    def get_available_languages(self) -> List[str]:
        """Get list of languages available for download"""
        if not STANZA_AVAILABLE:
            return []
        
        try:
            # Common Stanza languages
            return [
                'en', 'zh', 'zh-hans', 'zh-hant', 'es', 'fr', 'de', 'it', 'pt', 'ru',
                'ar', 'ja', 'ko', 'hi', 'th', 'vi', 'tr', 'pl', 'nl', 'sv', 'da',
                'no', 'fi', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr', 'sl', 'et', 'lv',
                'lt', 'uk', 'be', 'ca', 'eu', 'gl', 'cy', 'ga', 'mt', 'sq', 'mk',
                'sr', 'bs', 'me', 'is', 'fo', 'af', 'am', 'hy', 'az', 'bn', 'my',
                'ka', 'gu', 'he', 'id', 'kk', 'km', 'ky', 'lo', 'ml', 'mr', 'mn',
                'ne', 'or', 'pa', 'ps', 'fa', 'si', 'ta', 'te', 'bo', 'ug', 'ur',
                'uz', 'wo', 'yo'
            ]
        except Exception:
            return ['en']  # Fallback to English only