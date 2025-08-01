"""
NLP Engine Factory for creating different NLP engines.

This module provides a factory pattern for creating various NLP engines
that can be used with Microsoft Presidio.
"""

import logging
from typing import Dict, Any, Optional
from presidio_analyzer.nlp_engine import NlpEngine

# Import custom engines
from .flair_engine import FlairNlpEngine
from .stanza_engine import StanzaNlpEngine

# Try to import built-in engines
try:
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("SpacyNlpEngine not available")

try:
    from presidio_analyzer.nlp_engine import TransformersNlpEngine
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("TransformersNlpEngine not available")


class NlpEngineFactory:
    """Factory for creating NLP engines"""
    
    @staticmethod
    def create_engine(framework: str, model_config: Dict[str, Any], 
                     ner_model_configuration: Dict[str, Any] = None) -> Optional[NlpEngine]:
        """
        Create an NLP engine for the specified framework
        
        Args:
            framework: Framework name (spacy, transformers, flair, stanza)
            model_config: Configuration for the model
            ner_model_configuration: NER-specific configuration
            
        Returns:
            NlpEngine instance or None if creation fails
        """
        try:
            framework = framework.lower()
            
            if framework == "spacy":
                return NlpEngineFactory._create_spacy_engine(model_config, ner_model_configuration)
            elif framework == "transformers":
                return NlpEngineFactory._create_transformers_engine(model_config, ner_model_configuration)
            elif framework == "flair":
                return NlpEngineFactory._create_flair_engine(model_config, ner_model_configuration)
            elif framework == "stanza":
                return NlpEngineFactory._create_stanza_engine(model_config, ner_model_configuration)
            else:
                logging.error(f"Unsupported framework: {framework}")
                return None
                
        except Exception as e:
            logging.error(f"Failed to create NLP engine for {framework}: {e}")
            return None
    
    @staticmethod
    def _create_spacy_engine(model_config: Dict[str, Any], 
                           ner_model_configuration: Dict[str, Any] = None) -> Optional[NlpEngine]:
        """Create spaCy NLP engine"""
        if not SPACY_AVAILABLE:
            logging.error("SpacyNlpEngine not available")
            return None
        
        try:
            # Convert model_config to the format expected by SpacyNlpEngine
            models = []
            
            if isinstance(model_config, dict):
                # Single model configuration
                if 'models' in model_config:
                    models = model_config['models']
                else:
                    # Direct model specification
                    lang_code = model_config.get('lang_code', 'en')
                    model_name = model_config.get('model_name', model_config.get('name', 'en_core_web_sm'))
                    models = [{'lang_code': lang_code, 'model_name': model_name}]
            elif isinstance(model_config, list):
                models = model_config
            
            # Create the engine
            engine = SpacyNlpEngine(
                models=models,
                ner_model_configuration=ner_model_configuration
            )
            
            logging.info(f"Created SpacyNlpEngine with {len(models)} models")
            return engine
            
        except Exception as e:
            logging.error(f"Failed to create SpacyNlpEngine: {e}")
            return None
    
    @staticmethod
    def _create_transformers_engine(model_config: Dict[str, Any], 
                                  ner_model_configuration: Dict[str, Any] = None) -> Optional[NlpEngine]:
        """Create Transformers NLP engine"""
        if not TRANSFORMERS_AVAILABLE:
            logging.error("TransformersNlpEngine not available")
            return None
        
        try:
            # Convert model_config to the format expected by TransformersNlpEngine
            models = []
            
            if isinstance(model_config, dict):
                # Single model configuration
                if 'models' in model_config:
                    models = model_config['models']
                else:
                    # Direct model specification
                    lang_code = model_config.get('lang_code', 'en')
                    model_name = model_config.get('model_name', {})
                    
                    # Handle different model name formats
                    if isinstance(model_name, str):
                        # Simple model name
                        model_spec = {
                            'spacy': 'en_core_web_md',  # Required by TransformersNlpEngine
                            'transformers': model_name
                        }
                    elif isinstance(model_name, dict):
                        model_spec = model_name
                    else:
                        model_spec = {
                            'spacy': 'en_core_web_md',
                            'transformers': 'dbmdz/bert-large-cased-finetuned-conll03-english'
                        }
                    
                    models = [{'lang_code': lang_code, 'model_name': model_spec}]
            elif isinstance(model_config, list):
                models = model_config
            
            # Create the engine
            engine = TransformersNlpEngine(
                models=models,
                ner_model_configuration=ner_model_configuration
            )
            
            logging.info(f"Created TransformersNlpEngine with {len(models)} models")
            return engine
            
        except Exception as e:
            logging.error(f"Failed to create TransformersNlpEngine: {e}")
            return None
    
    @staticmethod
    def _create_flair_engine(model_config: Dict[str, Any], 
                           ner_model_configuration: Dict[str, Any] = None) -> Optional[NlpEngine]:
        """Create Flair NLP engine"""
        try:
            # Convert model_config to the format expected by FlairNlpEngine
            models = []
            
            if isinstance(model_config, dict):
                # Single model configuration
                if 'models' in model_config:
                    models = model_config['models']
                else:
                    # Direct model specification
                    lang_code = model_config.get('lang_code', 'en')
                    model_name = model_config.get('model_name', 'ner')
                    models = [{'lang_code': lang_code, 'model_name': model_name}]
            elif isinstance(model_config, list):
                models = model_config
            
            # Create the engine
            engine = FlairNlpEngine(
                models=models,
                ner_model_configuration=ner_model_configuration
            )
            
            logging.info(f"Created FlairNlpEngine with {len(models)} models")
            return engine
            
        except Exception as e:
            logging.error(f"Failed to create FlairNlpEngine: {e}")
            return None
    
    @staticmethod
    def _create_stanza_engine(model_config: Dict[str, Any], 
                            ner_model_configuration: Dict[str, Any] = None) -> Optional[NlpEngine]:
        """Create Stanza NLP engine"""
        try:
            # Convert model_config to the format expected by StanzaNlpEngine
            models = []
            
            if isinstance(model_config, dict):
                # Single model configuration
                if 'models' in model_config:
                    models = model_config['models']
                else:
                    # Direct model specification
                    lang_code = model_config.get('lang_code', 'en')
                    model_name = model_config.get('model_name', lang_code)
                    models = [{'lang_code': lang_code, 'model_name': model_name}]
            elif isinstance(model_config, list):
                models = model_config
            
            # Create the engine
            engine = StanzaNlpEngine(
                models=models,
                ner_model_configuration=ner_model_configuration
            )
            
            logging.info(f"Created StanzaNlpEngine with {len(models)} models")
            return engine
            
        except Exception as e:
            logging.error(f"Failed to create StanzaNlpEngine: {e}")
            return None
    
    @staticmethod
    def get_supported_frameworks() -> Dict[str, bool]:
        """Get list of supported frameworks and their availability"""
        return {
            'spacy': SPACY_AVAILABLE,
            'transformers': TRANSFORMERS_AVAILABLE,
            'flair': True,  # Our custom implementation is always available (if dependencies are installed)
            'stanza': True  # Our custom implementation is always available (if dependencies are installed)
        }
    
    @staticmethod
    def check_framework_dependencies(framework: str) -> Dict[str, Any]:
        """Check if dependencies for a framework are available"""
        framework = framework.lower()
        
        result = {
            'framework': framework,
            'available': False,
            'missing_dependencies': [],
            'error': None
        }
        
        try:
            if framework == 'spacy':
                import spacy
                result['available'] = True
                result['version'] = spacy.__version__
            elif framework == 'transformers':
                import transformers
                import torch
                result['available'] = True
                result['version'] = transformers.__version__
                result['torch_version'] = torch.__version__
            elif framework == 'flair':
                import flair
                import torch
                result['available'] = True
                result['version'] = flair.__version__
                result['torch_version'] = torch.__version__
            elif framework == 'stanza':
                import stanza
                result['available'] = True
                result['version'] = stanza.__version__
            else:
                result['error'] = f"Unknown framework: {framework}"
                
        except ImportError as e:
            result['error'] = str(e)
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            result['missing_dependencies'].append(missing)
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def get_default_configuration(framework: str) -> Dict[str, Any]:
        """Get default configuration for a framework"""
        framework = framework.lower()
        
        configurations = {
            'spacy': {
                'models': [{'lang_code': 'en', 'model_name': 'en_core_web_md'}],
                'ner_model_configuration': {
                    'model_to_presidio_entity_mapping': {
                        'PER': 'PERSON',
                        'LOC': 'LOCATION',
                        'ORG': 'ORGANIZATION',
                        'GPE': 'LOCATION'
                    },
                    'low_confidence_score_multiplier': 0.4,
                    'low_score_entity_names': ['ORG']
                }
            },
            'transformers': {
                'models': [{
                    'lang_code': 'en',
                    'model_name': {
                        'spacy': 'en_core_web_md',
                        'transformers': 'dbmdz/bert-large-cased-finetuned-conll03-english'
                    }
                }],
                'ner_model_configuration': {
                    'labels_to_ignore': ['O'],
                    'aggregation_strategy': 'max',
                    'alignment_mode': 'expand',
                    'model_to_presidio_entity_mapping': {
                        'PER': 'PERSON',
                        'PERSON': 'PERSON',
                        'LOC': 'LOCATION',
                        'LOCATION': 'LOCATION',
                        'ORG': 'ORGANIZATION',
                        'ORGANIZATION': 'ORGANIZATION'
                    }
                }
            },
            'flair': {
                'models': [{'lang_code': 'en', 'model_name': 'ner'}],
                'ner_model_configuration': {
                    'entity_mapping': {
                        'PER': 'PERSON',
                        'LOC': 'LOCATION',
                        'ORG': 'ORGANIZATION',
                        'MISC': 'MISC'
                    }
                }
            },
            'stanza': {
                'models': [{'lang_code': 'en', 'model_name': 'en'}],
                'ner_model_configuration': {
                    'entity_mapping': {
                        'PER': 'PERSON',
                        'LOC': 'LOCATION',
                        'ORG': 'ORGANIZATION',
                        'GPE': 'LOCATION'
                    }
                }
            }
        }
        
        return configurations.get(framework, {})