"""
Flair NLP Engine for Presidio integration.

This module provides a custom NLP engine that integrates Flair models
with Microsoft Presidio for PII detection.
"""

import logging
from typing import List, Dict, Optional, Any
from presidio_analyzer.nlp_engine import NlpEngine, NlpArtifacts
from presidio_analyzer.nlp_engine.nlp_artifacts import NlpArtifacts as NlpArtifactsBase

try:
    from flair.data import Sentence
    from flair.nn import Classifier
    from flair.models import SequenceTagger
    FLAIR_AVAILABLE = True
except ImportError:
    FLAIR_AVAILABLE = False
    logging.warning("Flair not available - FlairNlpEngine will not function")
    # Create dummy classes to prevent import errors
    class Sentence:
        pass
    class Classifier:
        pass
    class SequenceTagger:
        pass


class FlairNlpArtifacts(NlpArtifactsBase):
    """Custom NLP artifacts for Flair"""
    
    def __init__(self, sentence: Sentence, language: str):
        self.sentence = sentence
        self.language = language
        super().__init__()
    
    @property
    def tokens(self) -> List[str]:
        """Get list of tokens"""
        if hasattr(self.sentence, 'tokens'):
            return [token.text for token in self.sentence.tokens]
        return []
    
    @property
    def tokens_indices(self) -> List[tuple]:
        """Get list of token indices (start, end)"""
        if hasattr(self.sentence, 'tokens'):
            return [(token.start_pos, token.end_pos) for token in self.sentence.tokens]
        return []
    
    @property
    def lemmas(self) -> List[str]:
        """Get list of lemmas (Flair doesn't provide lemmas by default)"""
        return self.tokens  # Fallback to tokens
    
    @property
    def entities(self) -> List[Dict[str, Any]]:
        """Get list of entities"""
        entities = []
        if hasattr(self.sentence, 'get_spans'):
            spans = self.sentence.get_spans('ner')
            for span in spans:
                entities.append({
                    'start': span.start_pos,
                    'end': span.end_pos,
                    'text': span.text,
                    'label': span.tag,
                    'confidence': span.score
                })
        return entities


class FlairNlpEngine(NlpEngine):
    """Custom NLP Engine using Flair models"""
    
    def __init__(self, models: List[Dict], ner_model_configuration: Dict = None):
        """
        Initialize Flair NLP Engine
        
        Args:
            models: List of model configurations
            ner_model_configuration: NER model configuration
        """
        super().__init__()
        
        if not FLAIR_AVAILABLE:
            raise ImportError("Flair is not available. Please install with: pip install flair")
        
        self.models = {}
        self.ner_model_configuration = ner_model_configuration or {}
        self.entity_mapping = self._get_entity_mapping()
        
        # Load models
        self._load_models(models)
        
        logging.info(f"FlairNlpEngine initialized with {len(self.models)} models")
    
    def _load_models(self, models: List[Dict]):
        """Load Flair models"""
        for model_config in models:
            lang_code = model_config.get('lang_code', 'en')
            model_path = model_config.get('model_name', model_config.get('model_path'))
            
            if not model_path:
                logging.error(f"No model path specified for language {lang_code}")
                continue
            
            try:
                # Load the NER model
                if isinstance(model_path, str):
                    # Load from path or model name
                    if model_path.startswith('ner') or '/' in model_path:
                        # Standard Flair model name or path
                        model = SequenceTagger.load(model_path)
                    else:
                        # Try as a file path
                        model = SequenceTagger.load(model_path)
                else:
                    logging.error(f"Invalid model path type for {lang_code}: {type(model_path)}")
                    continue
                
                self.models[lang_code] = model
                logging.info(f"Loaded Flair model for {lang_code}: {model_path}")
                
            except Exception as e:
                logging.error(f"Failed to load Flair model for {lang_code}: {e}")
    
    def _get_entity_mapping(self) -> Dict[str, str]:
        """Get entity mapping from Flair to Presidio entities"""
        default_mapping = {
            'PER': 'PERSON',
            'PERSON': 'PERSON',
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'MISC': 'MISC',
            'GPE': 'LOCATION'
        }
        
        # Use configuration mapping if available
        if self.ner_model_configuration and 'entity_mapping' in self.ner_model_configuration:
            mapping = self.ner_model_configuration['entity_mapping']
            default_mapping.update(mapping)
        
        return default_mapping
    
    def process_text(self, text: str, language: str) -> NlpArtifacts:
        """
        Process text using Flair models
        
        Args:
            text: Text to process
            language: Language code
            
        Returns:
            NlpArtifacts object with processing results
        """
        if not text or not isinstance(text, str):
            # Return empty artifacts for invalid input
            return FlairNlpArtifacts(Sentence(""), language)
        
        # Get model for language (fallback to 'en' if not available)
        model = self.models.get(language, self.models.get('en'))
        if not model:
            logging.warning(f"No Flair model available for language: {language}")
            return FlairNlpArtifacts(Sentence(""), language)
        
        try:
            # Create Flair sentence
            sentence = Sentence(text)
            
            # Predict entities
            model.predict(sentence)
            
            # Create artifacts
            artifacts = FlairNlpArtifacts(sentence, language)
            
            return artifacts
            
        except Exception as e:
            logging.error(f"Error processing text with Flair: {e}")
            return FlairNlpArtifacts(Sentence(""), language)
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        # Return Presidio-mapped entity types
        return list(set(self.entity_mapping.values()))
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.models.keys())
    
    def is_available(self) -> bool:
        """Check if Flair is available and models are loaded"""
        return FLAIR_AVAILABLE and len(self.models) > 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        info = {
            'framework': 'flair',
            'available': self.is_available(),
            'languages': self.get_supported_languages(),
            'entities': self.get_supported_entities(),
            'models': {}
        }
        
        for lang, model in self.models.items():
            model_info = {
                'language': lang,
                'type': type(model).__name__,
                'available': True
            }
            
            # Try to get model details
            try:
                if hasattr(model, 'tag_dictionary'):
                    model_info['tags'] = [tag for tag in model.tag_dictionary.get_items()]
                elif hasattr(model, 'label_dictionary'):
                    model_info['tags'] = [tag for tag in model.label_dictionary.get_items()]
            except Exception as e:
                logging.debug(f"Could not get tags for Flair model {lang}: {e}")
            
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
            # Map Flair entity type to Presidio entity type
            flair_label = entity_info['label']
            presidio_label = self.entity_mapping.get(flair_label, flair_label)
            
            entities.append({
                'start': entity_info['start'],
                'end': entity_info['end'],
                'text': entity_info['text'],
                'entity_type': presidio_label,
                'confidence': entity_info['confidence'],
                'recognition_metadata': {
                    'recognizer_name': 'FlairNlpEngine',
                    'original_label': flair_label
                }
            })
        
        return entities