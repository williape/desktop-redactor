from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Optional, Tuple, Any
import logging
from .custom_recognizers import EnhancedPhoneRecognizer, AuDvaRecognizer, AuMedicareProviderRecognizer, AuCrnRecognizer, AuPassportRecognizer, AuDriversLicenseRecognizer
from .list_manager import ListManager
from .encryption_manager import EncryptionManager
from .findings_model import Finding, FindingsCollection
from .model_manager import ModelManager, ModelInfo
from .nlp_engines.engine_factory import NlpEngineFactory

class PresidioManager:
    """Abstraction layer for Presidio operations"""
    
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        self.list_manager: Optional[ListManager] = None
        self.encryption_manager: Optional[EncryptionManager] = None
        
        # Phase 5 additions - Multiple NLP Engine support
        self.model_manager = ModelManager()
        self.nlp_engines = {}
        self.current_engine_id = "spacy_lg"  # Default fallback
        self.current_nlp_engine = None
        
        self.initialize_engines()
        
    def initialize_engines(self):
        """Initialize Presidio engines with custom recognizers and NLP engines"""
        try:
            # Initialize the default analyzer (will be replaced with custom NLP engine)
            self._initialize_default_analyzer()
            
            # Initialize available NLP engines
            self._initialize_nlp_engines()
            
            # Set the default engine
            self._set_default_engine()
            
            # Initialize anonymizer
            self.anonymizer = AnonymizerEngine()
            
            logging.info("Presidio engines initialized successfully with multiple NLP engine support")
        except Exception as e:
            logging.error(f"Failed to initialize Presidio: {e}")
            raise
    
    def _get_best_available_spacy_model(self):
        """Get the best available spaCy model with fallback logic"""
        import sys
        import os
        
        # Priority order: medium -> small -> large (if available)
        model_priority = ["en_core_web_md", "en_core_web_sm", "en_core_web_lg"]
        
        # In PyInstaller, models may be in different locations
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle - models are in Resources
            if hasattr(sys, '_MEIPASS'):
                bundle_dir = sys._MEIPASS
                logging.debug(f"Using sys._MEIPASS: {bundle_dir}")
                
                # For macOS app bundles, also check Resources directory for complete models
                if 'Contents' in sys.executable:
                    # We're in a macOS app bundle, try Resources directory first
                    executable_dir = os.path.dirname(sys.executable)
                    contents_dir = executable_dir
                    while contents_dir and not contents_dir.endswith('Contents'):
                        contents_dir = os.path.dirname(contents_dir)
                    resources_dir = os.path.join(contents_dir, 'Resources')
                    
                    if os.path.exists(resources_dir):
                        models_in_resources = [d for d in os.listdir(resources_dir) if d.startswith('en_core_web')]
                        if models_in_resources:
                            logging.debug(f"Found models in Resources: {models_in_resources}, using Resources instead of _MEIPASS")
                            bundle_dir = resources_dir
            else:
                # For macOS app bundles, resources are in Contents/Resources
                executable_dir = os.path.dirname(sys.executable)
                logging.debug(f"Executable: {sys.executable}")
                logging.debug(f"Executable directory: {executable_dir}")
                
                if 'MacOS' in executable_dir:
                    # Find the Contents directory by going up from MacOS
                    contents_dir = executable_dir
                    while contents_dir and not contents_dir.endswith('Contents'):
                        contents_dir = os.path.dirname(contents_dir)
                    bundle_dir = os.path.join(contents_dir, 'Resources')
                else:
                    # Fallback - look for Resources relative to executable
                    bundle_dir = os.path.join(executable_dir, '..', 'Resources')
                    bundle_dir = os.path.abspath(bundle_dir)
            logging.debug(f"Running in PyInstaller bundle, bundle_dir: {bundle_dir}")
            
            # Double-check the path exists and contains models
            if os.path.exists(bundle_dir):
                models_in_bundle = [d for d in os.listdir(bundle_dir) if d.startswith('en_core_web')]
                logging.debug(f"Models found in bundle: {models_in_bundle}")
            else:
                logging.debug(f"Bundle directory does not exist: {bundle_dir}")
        
        for model_name in model_priority:
            try:
                import spacy
                
                # For PyInstaller bundles, check if model directory exists first
                if getattr(sys, 'frozen', False):
                    # Check in the bundle resources - try different nested structures
                    model_paths_to_try = [
                        # Three-level nesting: en_core_web_md/en_core_web_md/en_core_web_md-3.8.0/
                        os.path.join(bundle_dir, model_name, model_name, f"{model_name}-3.8.0"),
                        # Two-level nesting: en_core_web_md/en_core_web_md/
                        os.path.join(bundle_dir, model_name, model_name),
                        # Single-level: en_core_web_md/
                        os.path.join(bundle_dir, model_name)
                    ]
                    
                    for model_path in model_paths_to_try:
                        if os.path.exists(model_path):
                            logging.info(f"Found bundled model at: {model_path}")
                            try:
                                nlp = spacy.load(model_path)
                                logging.info(f"Successfully loaded model from path: {model_name}")
                                return model_path
                            except Exception as e:
                                logging.debug(f"Failed to load model from path {model_path}: {e}")
                                continue
                
                # Try standard spaCy loading
                spacy.load(model_name)
                logging.info(f"Selected spaCy model: {model_name}")
                return model_name
                
            except OSError:
                logging.debug(f"Model {model_name} not available")
                continue
            except Exception as e:
                logging.debug(f"Error checking model {model_name}: {e}")
                continue
        
        # If no models are available, this will cause an error which is what we want
        # so the user knows something is wrong with the installation
        raise RuntimeError("No spaCy models available. Please ensure at least one English model is installed.")
    
    def _ensure_presidio_config_available(self):
        """Ensure Presidio configuration files are accessible in PyInstaller bundles"""
        import sys
        import os
        import shutil
        
        if not getattr(sys, 'frozen', False):
            return  # Not in PyInstaller bundle
            
        # Presidio looks for config in sys._MEIPASS/presidio_analyzer/conf/
        # But we bundled it to Resources, so copy it if needed
        if hasattr(sys, '_MEIPASS'):
            meipass_config_dir = os.path.join(sys._MEIPASS, 'presidio_analyzer', 'conf')
            
            # Check if config already exists in MEIPASS location
            if not os.path.exists(os.path.join(meipass_config_dir, 'default_recognizers.yaml')):
                # Find config in Resources
                if 'Contents' in sys.executable:
                    executable_dir = os.path.dirname(sys.executable)
                    contents_dir = executable_dir
                    while contents_dir and not contents_dir.endswith('Contents'):
                        contents_dir = os.path.dirname(contents_dir)
                    resources_config_dir = os.path.join(contents_dir, 'Resources', 'presidio_analyzer', 'conf')
                    
                    if os.path.exists(resources_config_dir):
                        # Create the target directory
                        os.makedirs(meipass_config_dir, exist_ok=True)
                        
                        # Copy config files
                        for config_file in os.listdir(resources_config_dir):
                            src = os.path.join(resources_config_dir, config_file)
                            dst = os.path.join(meipass_config_dir, config_file)
                            if os.path.isfile(src):
                                shutil.copy2(src, dst)
                                logging.debug(f"Copied Presidio config: {config_file}")
                        
                        logging.info(f"Presidio configuration files made available at: {meipass_config_dir}")
                    else:
                        logging.warning(f"Could not find Presidio config files in Resources: {resources_config_dir}")
    
    def _initialize_default_analyzer(self):
        """Initialize the default analyzer with custom recognizers"""
        # For PyInstaller bundles, ensure Presidio config files are accessible
        self._ensure_presidio_config_available()
        
        # Get the best available spaCy model instead of letting Presidio default to en_core_web_lg
        available_model = self._get_best_available_spacy_model()
        
        # Import necessary classes for NLP engine configuration
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        
        # Create NLP engine provider with specific model
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": available_model}]
        }
        
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()
        
        # Initialize analyzer with specific NLP engine
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        
        # Remove the default phone recognizer
        phone_recognizers_to_remove = []
        for recognizer in self.analyzer.registry.recognizers:
            if hasattr(recognizer, 'name') and recognizer.name == "PhoneRecognizer":
                phone_recognizers_to_remove.append(recognizer)
        
        for recognizer in phone_recognizers_to_remove:
            self.analyzer.registry.recognizers.remove(recognizer)
            logging.info("Removed default PhoneRecognizer")
        
        # Add enhanced phone recognizer for Australian support
        enhanced_phone_recognizer = EnhancedPhoneRecognizer()
        self.analyzer.registry.add_recognizer(enhanced_phone_recognizer)
        logging.info("Added EnhancedPhoneRecognizer with Australian support")
        
        # Add AU DVA recognizer for Australian DVA file numbers
        au_dva_recognizer = AuDvaRecognizer()
        self.analyzer.registry.add_recognizer(au_dva_recognizer)
        logging.info("Added AuDvaRecognizer for Australian DVA file numbers")
        
        # Add AU Medicare Provider recognizer for Australian Medicare Provider Numbers
        au_medicare_provider_recognizer = AuMedicareProviderRecognizer()
        self.analyzer.registry.add_recognizer(au_medicare_provider_recognizer)
        logging.info("Added AuMedicareProviderRecognizer for Australian Medicare Provider Numbers")
        
        # Add AU CRN recognizer for Australian Centrelink Customer Reference Numbers
        au_crn_recognizer = AuCrnRecognizer()
        self.analyzer.registry.add_recognizer(au_crn_recognizer)
        logging.info("Added AuCrnRecognizer for Australian Centrelink Customer Reference Numbers")
        
        # Add AU Passport recognizer for Australian passport numbers
        au_passport_recognizer = AuPassportRecognizer()
        self.analyzer.registry.add_recognizer(au_passport_recognizer)
        logging.info("Added AuPassportRecognizer for Australian passport numbers")
        
        # Add AU Driver's License recognizer for Australian driver's license numbers
        au_drivers_license_recognizer = AuDriversLicenseRecognizer()
        self.analyzer.registry.add_recognizer(au_drivers_license_recognizer)
        logging.info("Added AuDriversLicenseRecognizer for Australian driver's license numbers")
    
    def _initialize_nlp_engines(self):
        """Initialize available NLP engines based on discovered models"""
        available_models = self.model_manager.get_available_models()
        
        for model in available_models:
            try:
                engine_id = model.id
                
                # Create engine configuration
                if model.framework == "spacy":
                    config = {
                        'lang_code': model.language,
                        'model_name': self._get_spacy_model_name(model)
                    }
                    ner_config = NlpEngineFactory.get_default_configuration("spacy")['ner_model_configuration']
                elif model.framework == "transformers":
                    config = {
                        'lang_code': model.language,
                        'model_name': {
                            'spacy': 'en_core_web_md',  # Required fallback
                            'transformers': model.name
                        }
                    }
                    ner_config = NlpEngineFactory.get_default_configuration("transformers")['ner_model_configuration']
                elif model.framework == "flair":
                    config = {
                        'lang_code': model.language,
                        'model_name': str(model.path) if model.path else model.name
                    }
                    ner_config = NlpEngineFactory.get_default_configuration("flair")['ner_model_configuration']
                elif model.framework == "stanza":
                    config = {
                        'lang_code': model.language,
                        'model_name': model.language
                    }
                    ner_config = NlpEngineFactory.get_default_configuration("stanza")['ner_model_configuration']
                else:
                    continue
                
                # Try to create the engine
                engine = NlpEngineFactory.create_engine(
                    framework=model.framework,
                    model_config=config,
                    ner_model_configuration=ner_config
                )
                
                if engine:
                    self.nlp_engines[engine_id] = {
                        'engine': engine,
                        'model_info': model,
                        'config': config
                    }
                    logging.info(f"Initialized NLP engine: {engine_id}")
                
            except Exception as e:
                logging.warning(f"Could not initialize NLP engine for {model.id}: {e}")
        
        logging.info(f"Initialized {len(self.nlp_engines)} NLP engines")
    
    def _get_spacy_model_name(self, model: ModelInfo) -> str:
        """Get the appropriate spaCy model name"""
        import sys
        
        if model.status == "bundled" and getattr(sys, 'frozen', False):
            # For bundled models in PyInstaller, return the actual path
            import os
            
            model_name = None
            if "sm" in model.id:
                model_name = "en_core_web_sm"
            elif "md" in model.id:
                model_name = "en_core_web_md"
            elif "lg" in model.id:
                model_name = "en_core_web_lg"
            
            if model_name:
                # Use the same path resolution logic as _get_best_available_spacy_model
                if hasattr(sys, '_MEIPASS'):
                    bundle_dir = sys._MEIPASS
                    
                    # For macOS app bundles, check Resources directory
                    if 'Contents' in sys.executable:
                        executable_dir = os.path.dirname(sys.executable)
                        contents_dir = executable_dir
                        while contents_dir and not contents_dir.endswith('Contents'):
                            contents_dir = os.path.dirname(contents_dir)
                        resources_dir = os.path.join(contents_dir, 'Resources')
                        
                        if os.path.exists(resources_dir):
                            models_in_resources = [d for d in os.listdir(resources_dir) if d.startswith('en_core_web')]
                            if models_in_resources:
                                bundle_dir = resources_dir
                    
                    # Try different nested structures
                    model_paths_to_try = [
                        os.path.join(bundle_dir, model_name, model_name, f"{model_name}-3.8.0"),
                        os.path.join(bundle_dir, model_name, model_name),
                        os.path.join(bundle_dir, model_name)
                    ]
                    
                    for model_path in model_paths_to_try:
                        if os.path.exists(model_path):
                            return model_path
            
            # Fallback to standard name
            return model_name or "en_core_web_md"
        
        elif model.status == "bundled":
            # Not in PyInstaller, use standard names
            if "sm" in model.id:
                return "en_core_web_sm"
            elif "md" in model.id:
                return "en_core_web_md"
            elif "lg" in model.id:
                return "en_core_web_lg"
        
        # For custom models, use the path or name
        return str(model.path) if model.path else model.name
    
    def _set_default_engine(self):
        """Set the default NLP engine"""
        # Priority order for default engine selection
        preferred_engines = ["spacy_md", "spacy_lg", "spacy_sm"]
        
        for engine_id in preferred_engines:
            if engine_id in self.nlp_engines:
                self.current_engine_id = engine_id
                self.current_nlp_engine = self.nlp_engines[engine_id]['engine']
                
                # Update analyzer with custom NLP engine
                self._update_analyzer_with_engine(engine_id)
                
                logging.info(f"Set default NLP engine: {engine_id}")
                return
        
        # If no preferred engines, use the first available
        if self.nlp_engines:
            engine_id = list(self.nlp_engines.keys())[0]
            self.current_engine_id = engine_id
            self.current_nlp_engine = self.nlp_engines[engine_id]['engine']
            self._update_analyzer_with_engine(engine_id)
            logging.info(f"Set default NLP engine (fallback): {engine_id}")
        else:
            logging.warning("No NLP engines available - using default spaCy engine")
            # Keep the default analyzer as-is
            
    def get_supported_entities(self) -> List[str]:
        """Get list of built-in supported entities"""
        return [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "CREDIT_CARD", "IP_ADDRESS", "URL",
            "AU_ABN", "AU_ACN", "AU_TFN", "AU_MEDICARE", "AU_MEDICAREPROVIDER", "AU_DVA", "AU_CRN", "AU_PASSPORT", "AU_DRIVERSLICENSE"
        ]
        
    def analyze_text_with_findings(self, text: str, entities: List[str], 
                                   confidence: float = 0.7, detailed_analysis: bool = False) -> Tuple[List, FindingsCollection]:
        """Analyze text for PII entities and return both results and findings collection"""
        results = self.analyze_text(text, entities, confidence, detailed_analysis)
        findings_collection = self.create_findings_from_results(results, text, detailed_analysis)
        return results, findings_collection
        
    def create_findings_from_results(self, analyzer_results: List, text: str, detailed_analysis: bool = False) -> FindingsCollection:
        """Create a findings collection from Presidio analyzer results"""
        findings_collection = FindingsCollection()
        
        for result in analyzer_results:
            # Extract the actual text
            finding_text = text[result.start:result.end] if text else ''
            
            # Get recognizer name from recognition_metadata
            recognizer_name = 'Unknown'
            if hasattr(result, 'recognition_metadata') and result.recognition_metadata:
                recognizer_name = result.recognition_metadata.get('recognizer_name', 'Unknown')
            
            # Get pattern information from recognizers
            pattern_name = None
            pattern = None
            
            # Try to get pattern info from recognition metadata first
            if hasattr(result, 'recognition_metadata') and result.recognition_metadata:
                metadata = result.recognition_metadata
                
                # Check for pattern information in metadata
                if 'pattern_name' in metadata:
                    pattern_name = metadata['pattern_name']
                if 'pattern' in metadata:
                    pattern = metadata['pattern']
                elif 'regex_pattern' in metadata:
                    pattern = metadata['regex_pattern']
            
            # If no pattern found in metadata, try to extract from recognizers
            if not pattern:
                # Try custom recognizers first
                if recognizer_name in ['AuDvaRecognizer', 'AuMedicareProviderRecognizer', 'EnhancedPhoneRecognizer', 'AuCrnRecognizer', 'AuDriversLicenseRecognizer']:
                    pattern_info = self._get_pattern_info_for_custom_recognizer(recognizer_name, finding_text, result)
                    if pattern_info:
                        pattern_name = pattern_info.get('pattern_name')
                        pattern = pattern_info.get('pattern')
                
                # Try built-in recognizers
                if not pattern:
                    pattern_info = self._get_pattern_info_from_analyzer(recognizer_name, result.entity_type, finding_text)
                    if pattern_info:
                        pattern_name = pattern_info.get('pattern_name')
                        pattern = pattern_info.get('pattern')
            
            # Extract decision process data if available
            original_score = None
            score = None
            textual_explanation = None
            score_context_improvement = None
            supportive_context_word = None
            validation_result = None
            regex_flags = None
            decision_process = None
            
            if detailed_analysis and hasattr(result, 'analysis_explanation'):
                # Extract decision process information
                explanation = result.analysis_explanation
                if explanation:
                    decision_process = explanation.__dict__ if hasattr(explanation, '__dict__') else str(explanation)
                    
                    # Extract specific fields if available
                    if hasattr(explanation, 'original_score'):
                        original_score = explanation.original_score
                    if hasattr(explanation, 'score'):
                        score = explanation.score
                    if hasattr(explanation, 'textual_explanation'):
                        textual_explanation = explanation.textual_explanation
                    if hasattr(explanation, 'score_context_improvement'):
                        score_context_improvement = explanation.score_context_improvement
                    if hasattr(explanation, 'supportive_context_word'):
                        supportive_context_word = explanation.supportive_context_word
                    if hasattr(explanation, 'validation_result'):
                        validation_result = explanation.validation_result
                    if hasattr(explanation, 'regex_flags'):
                        regex_flags = str(explanation.regex_flags)
                    
                    # Extract pattern information from decision process if not already found
                    if not pattern and hasattr(explanation, 'pattern'):
                        pattern = explanation.pattern
                    if not pattern_name and hasattr(explanation, 'pattern_name'):
                        pattern_name = explanation.pattern_name
                    
                    # Try to extract from recognizer results within explanation
                    if hasattr(explanation, 'recognizer_results'):
                        for recognizer_result in explanation.recognizer_results:
                            if hasattr(recognizer_result, 'pattern') and not pattern:
                                pattern = recognizer_result.pattern
                            if hasattr(recognizer_result, 'pattern_name') and not pattern_name:
                                pattern_name = recognizer_result.pattern_name
            
            # Create finding
            finding = Finding(
                entity_type=result.entity_type,
                text=finding_text,
                start=result.start,
                end=result.end,
                confidence=result.score,
                recognizer=recognizer_name,
                pattern_name=pattern_name,
                pattern=pattern,
                original_score=original_score,
                score=score,
                textual_explanation=textual_explanation,
                score_context_improvement=score_context_improvement,
                supportive_context_word=supportive_context_word,
                validation_result=validation_result,
                regex_flags=regex_flags,
                decision_process=decision_process
            )
            
            findings_collection.add_finding(finding)
            
        return findings_collection
    
    def _get_pattern_info_for_custom_recognizer(self, recognizer_name: str, text: str, result) -> Dict:
        """Get pattern information for custom recognizers"""
        try:
            # Find the recognizer instance
            for recognizer in self.analyzer.registry.recognizers:
                if hasattr(recognizer, 'name') and recognizer.name == recognizer_name:
                    # For pattern-based recognizers, try to match against patterns
                    if hasattr(recognizer, 'patterns'):
                        for i, pattern in enumerate(recognizer.patterns):
                            if hasattr(pattern, 'pattern') and hasattr(pattern, 'name'):
                                # Try to match the pattern against the text
                                import re
                                if re.search(pattern.pattern, text):
                                    return {
                                        'pattern_name': pattern.name,
                                        'pattern': pattern.pattern
                                    }
                            elif hasattr(pattern, 'regex') and hasattr(pattern, 'name'):
                                # Some patterns might use 'regex' instead of 'pattern'
                                import re
                                if re.search(pattern.regex, text):
                                    return {
                                        'pattern_name': pattern.name,
                                        'pattern': pattern.regex
                                    }
                    
                    # For Enhanced Phone Recognizer, provide specific pattern info
                    if recognizer_name == 'EnhancedPhoneRecognizer':
                        if '+61' in text or text.startswith('04'):
                            return {
                                'pattern_name': 'Australian Phone',
                                'pattern': 'Australian mobile/landline pattern'
                            }
                    
                    # For DVA recognizer
                    if recognizer_name == 'AuDvaRecognizer':
                        return {
                            'pattern_name': 'Australian DVA File Number',
                            'pattern': 'State code + War service + Number'
                        }
                    
                    # For Medicare Provider recognizer
                    if recognizer_name == 'AuMedicareProviderRecognizer':
                        return {
                            'pattern_name': 'Australian Medicare Provider Number',
                            'pattern': '6-digit stem + location + check digit'
                        }
                    
                    # For CRN recognizer
                    if recognizer_name == 'AuCrnRecognizer':
                        return {
                            'pattern_name': 'Australian Centrelink CRN',
                            'pattern': 'State code + sequence + check digit'
                        }
                    
                    # For Driver's License recognizer
                    if recognizer_name == 'AuDriversLicenseRecognizer':
                        return {
                            'pattern_name': 'Australian Driver\'s License Number',
                            'pattern': 'State-specific numeric/alphanumeric format'
                        }
                    
                    break
                    
        except Exception as e:
            logging.debug(f"Error getting pattern info for {recognizer_name}: {e}")
            
        return {}
    
    def _get_pattern_info_from_analyzer(self, recognizer_name: str, entity_type: str, text: str) -> Dict:
        """Get pattern information from built-in analyzer recognizers"""
        try:
            # Find the recognizer in the analyzer registry
            for recognizer in self.analyzer.registry.recognizers:
                # Check if this is the right recognizer
                if (hasattr(recognizer, 'name') and recognizer.name == recognizer_name) or \
                   (hasattr(recognizer, '__class__') and recognizer.__class__.__name__ == recognizer_name):
                    
                    # Check if recognizer supports the entity type
                    if hasattr(recognizer, 'supported_entities') and entity_type in recognizer.supported_entities:
                        
                        # Try to get patterns from pattern-based recognizers
                        if hasattr(recognizer, 'patterns'):
                            import re
                            for pattern in recognizer.patterns:
                                pattern_regex = None
                                pattern_name_attr = None
                                
                                # Different recognizers store patterns differently
                                if hasattr(pattern, 'regex'):
                                    pattern_regex = pattern.regex
                                elif hasattr(pattern, 'pattern'):
                                    pattern_regex = pattern.pattern
                                
                                if hasattr(pattern, 'name'):
                                    pattern_name_attr = pattern.name
                                elif hasattr(pattern, 'pattern_name'):
                                    pattern_name_attr = pattern.pattern_name
                                
                                # Test if pattern matches the text
                                if pattern_regex:
                                    try:
                                        if re.search(pattern_regex, text, re.IGNORECASE):
                                            return {
                                                'pattern_name': pattern_name_attr or f"{entity_type} Pattern",
                                                'pattern': pattern_regex
                                            }
                                    except re.error:
                                        # Skip invalid regex patterns
                                        continue
                        
                        # For non-pattern recognizers, return generic info
                        return {
                            'pattern_name': f"{entity_type} ({recognizer_name})",
                            'pattern': f"Built-in {entity_type} recognition"
                        }
            
            return {}
        except Exception as e:
            logging.debug(f"Error getting pattern info from analyzer for {recognizer_name}: {e}")
            return {}
    
    def analyze_text(self, text: str, entities: List[str], 
                     confidence: float = 0.7, detailed_analysis: bool = False) -> List:
        """Analyze text for PII entities with list management support"""
        if not text or not isinstance(text, str):
            return []
            
        try:
            # Create custom recognizers from denylist
            custom_recognizers = self._create_custom_recognizers()
            
            # If we have custom recognizers, add their entity types to the entities list
            analysis_entities = entities.copy() if entities else []
            if custom_recognizers and self.list_manager:
                denylist_entity_types = set()
                for entry in self.list_manager.denylist:
                    denylist_entity_types.add(entry.entity_type)
                
                # Add denylist entity types to analysis entities
                for entity_type in denylist_entity_types:
                    if entity_type not in analysis_entities:
                        analysis_entities.append(entity_type)
                        logging.debug(f"Added denylist entity type '{entity_type}' to analysis")
            
            # Analyze with custom recognizers
            results = self.analyzer.analyze(
                text=text,
                entities=analysis_entities,
                language='en',
                score_threshold=confidence,
                ad_hoc_recognizers=custom_recognizers,
                return_decision_process=detailed_analysis
            )
            
            # Apply allowlist filtering
            if self.list_manager:
                results = self.list_manager.apply_allowlist_filter_with_text(results, text)
                if custom_recognizers:
                    logging.debug(f"Applied {len(custom_recognizers)} custom recognizers from denylist")
            
            return results
        except Exception as e:
            logging.error(f"Error analyzing text: {e}")
            return []
        
    def anonymize_text(self, text: str, analyzer_results: List,
                       operator_config: Dict[str, OperatorConfig]) -> str:
        """Anonymize text based on analysis results"""
        if not text or not isinstance(text, str):
            return text
            
        if not analyzer_results:
            return text
            
        try:
            result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operator_config
            )
            return result.text
        except Exception as e:
            logging.error(f"Error anonymizing text: {e}")
            return text
            
    def get_default_operator_config(self, operation: str = "replace") -> Dict[str, OperatorConfig]:
        """Get default operator configuration for anonymization"""
        if operation.lower() == "encrypt":
            # Use encryption if available and configured
            if self.encryption_manager and self.encryption_manager.encryption_enabled:
                return {"DEFAULT": self.encryption_manager.get_operator_config()}
            else:
                # Fall back to redact if encryption not available
                logging.warning("Encryption requested but not available, falling back to redact")
                return {"DEFAULT": OperatorConfig("redact")}
        elif operation.lower() == "redact":
            return {"DEFAULT": OperatorConfig("redact")}
        elif operation.lower() == "mask":
            return {"DEFAULT": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 4, "from_end": False})}
        elif operation.lower() == "hash":
            return {"DEFAULT": OperatorConfig("hash")}
        else:  # replace (default)
            # Create entity-specific replace operators
            return self._get_entity_specific_replace_config()
            
    def _get_entity_specific_replace_config(self) -> Dict[str, OperatorConfig]:
        """Create entity-specific replace configuration"""
        entity_configs = {}
        
        # Define all supported entity types with their replacement values
        entity_types = [
            'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'CREDIT_CARD', 
            'IP_ADDRESS', 'URL', 'AU_ABN', 'AU_ACN', 'AU_TFN', 
            'AU_MEDICARE', 'AU_MEDICAREPROVIDER', 'AU_DVA', 'AU_CRN', 'AU_PASSPORT', 'AU_DRIVERSLICENSE'
        ]
        
        # Create specific operator config for each entity type
        for entity_type in entity_types:
            entity_configs[entity_type] = OperatorConfig("replace", {"new_value": f"<{entity_type}>"})
        
        # Add default for any other entity types
        entity_configs["DEFAULT"] = OperatorConfig("replace", {"new_value": "<ENTITY>"})
        
        return entity_configs
            
    def set_list_manager(self, list_manager: ListManager) -> None:
        """
        Set the list manager for allowlist/denylist functionality
        
        Args:
            list_manager: ListManager instance to use for list operations
        """
        self.list_manager = list_manager
        logging.info("List manager set for Presidio operations")
    
    def set_encryption_manager(self, encryption_manager: EncryptionManager) -> None:
        """
        Set the encryption manager for encryption functionality
        
        Args:
            encryption_manager: EncryptionManager instance to use for encryption operations
        """
        self.encryption_manager = encryption_manager
        logging.info("Encryption manager set for Presidio operations")
    
    def _create_custom_recognizers(self) -> List:
        """
        Create Presidio PatternRecognizer instances from denylist entries
        
        Returns:
            List of PatternRecognizer instances
        """
        if not self.list_manager:
            return []
        
        try:
            recognizers = self.list_manager.create_denylist_recognizers()
            if recognizers:
                logging.info(f"Created {len(recognizers)} custom recognizers from denylist")
            return recognizers
        except Exception as e:
            logging.error(f"Error creating custom recognizers: {e}")
            return []
    
    def get_list_stats(self) -> Dict:
        """
        Get statistics about list manager
        
        Returns:
            Dictionary with list statistics
        """
        if not self.list_manager:
            return {"error": "No list manager configured"}
        
        return self.list_manager.get_stats()
    
    def has_custom_lists(self) -> bool:
        """
        Check if list manager has any custom lists configured
        
        Returns:
            True if allowlist or denylist has entries, False otherwise
        """
        if not self.list_manager:
            return False
        
        stats = self.list_manager.get_stats()
        return stats.get('total_entries', 0) > 0
    
    def is_initialized(self) -> bool:
        """Check if engines are properly initialized"""
        return self.analyzer is not None and self.anonymizer is not None
    
    def get_supported_operations(self) -> List[str]:
        """
        Get list of supported anonymization operations
        
        Returns:
            List of supported operation names
        """
        operations = ["replace", "redact", "mask", "hash"]
        
        # Add encryption if available
        if self.encryption_manager and self.encryption_manager.encryption_enabled:
            operations.append("encrypt")
        
        return operations
    
    def has_encryption_available(self) -> bool:
        """
        Check if encryption is available and properly configured
        
        Returns:
            True if encryption is ready to use
        """
        return (self.encryption_manager is not None and 
                self.encryption_manager.encryption_enabled)
    
    def get_encryption_info(self) -> Dict:
        """
        Get information about encryption status
        
        Returns:
            Dictionary with encryption information
        """
        if not self.encryption_manager:
            return {
                "available": False,
                "enabled": False,
                "error": "No encryption manager configured"
            }
        
        try:
            key_info = self.encryption_manager.get_key_info()
            return {
                "available": True,
                "enabled": self.encryption_manager.encryption_enabled,
                "has_key": key_info.get("has_key", False),
                "key_strength": key_info.get("key_strength", 0.0),
                "algorithm": key_info.get("algorithm", "AES-256-GCM")
            }
        except Exception as e:
            return {
                "available": False,
                "enabled": False,
                "error": str(e)
            }
    
    def test_encryption_functionality(self) -> bool:
        """
        Test encryption functionality
        
        Returns:
            True if encryption is working correctly
        """
        if not self.encryption_manager:
            logging.error("No encryption manager available for testing")
            return False
        
        try:
            return self.encryption_manager.test_encryption_round_trip()
        except Exception as e:
            logging.error(f"Encryption test failed: {e}")
            return False
    
    def get_anonymizer_config_with_encryption(self, operation: str = "replace") -> Dict[str, OperatorConfig]:
        """
        Get anonymizer configuration including encryption support
        
        Args:
            operation: Type of anonymization operation
            
        Returns:
            Dictionary with operator configuration
        """
        try:
            if operation.lower() == "encrypt" and self.has_encryption_available():
                # Use encryption operator
                config = {"DEFAULT": self.encryption_manager.get_operator_config()}
                logging.info("Using encryption operator for anonymization")
                return config
            else:
                # Use standard operators
                return self.get_default_operator_config(operation)
                
        except Exception as e:
            logging.error(f"Error creating anonymizer config: {e}")
            # Fall back to replace operation
            return self._get_entity_specific_replace_config()
    
    def analyze_sample_text(self, text: str, entities: List[str], 
                           confidence: float = 0.7) -> Tuple[str, FindingsCollection]:
        """
        Analyze sample text and return both anonymized result and findings
        
        Args:
            text: Text to analyze
            entities: List of entity types to detect
            confidence: Minimum confidence threshold
            
        Returns:
            Tuple of (anonymized_text, findings_collection)
        """
        try:
            # Analyze text and get findings
            results, findings_collection = self.analyze_text_with_findings(text, entities, confidence)
            
            # Get default anonymization config
            operator_config = self.get_default_operator_config("replace")
            
            # Anonymize the text
            anonymized_text = self.anonymize_text(text, results, operator_config)
            
            return anonymized_text, findings_collection
            
        except Exception as e:
            logging.error(f"Error analyzing sample text: {e}")
            return text, FindingsCollection()
    
    def process_text_with_findings(self, text: str, entities: List[str], 
                                  confidence: float = 0.7, operation: str = "replace", detailed_analysis: bool = False) -> Tuple[str, FindingsCollection]:
        """
        Process text with specified operation and return findings
        
        Args:
            text: Text to process
            entities: List of entity types to detect
            confidence: Minimum confidence threshold
            operation: Type of anonymization operation
            detailed_analysis: Whether to enable decision process tracing
            
        Returns:
            Tuple of (processed_text, findings_collection)
        """
        try:
            # Analyze text and get findings
            results, findings_collection = self.analyze_text_with_findings(text, entities, confidence, detailed_analysis)
            
            if not results:
                return text, findings_collection
            
            # Get operator config for the specified operation
            operator_config = self.get_anonymizer_config_with_encryption(operation)
            
            # Process the text
            processed_text = self.anonymize_text(text, results, operator_config)
            
            return processed_text, findings_collection
            
        except Exception as e:
            logging.error(f"Error processing text with findings: {e}")
            return text, FindingsCollection()
    
    def get_findings_statistics(self, findings_collection: FindingsCollection) -> Dict:
        """
        Get comprehensive statistics about findings
        
        Args:
            findings_collection: Collection of findings to analyze
            
        Returns:
            Dictionary with detailed statistics
        """
        try:
            stats = findings_collection.get_statistics()
            
            # Add additional analysis
            supported_entities = self.get_supported_entities()
            
            # Entity coverage
            detected_entities = set(stats.get('entity_counts', {}).keys())
            coverage = {
                'detected_entities': list(detected_entities),
                'total_entity_types': len(detected_entities),
                'available_entity_types': len(supported_entities),
                'coverage_percentage': (len(detected_entities) / len(supported_entities)) * 100 if supported_entities else 0
            }
            
            # Add coverage info to stats
            stats['coverage'] = coverage
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting findings statistics: {e}")
            return {}
    
    def cleanup_encryption(self) -> None:
        """
        Clean up encryption resources securely
        """
        if self.encryption_manager:
            try:
                self.encryption_manager.secure_cleanup()
                logging.info("Encryption resources cleaned up")
            except Exception as e:
                logging.error(f"Error cleaning up encryption: {e}")
    
    def __del__(self):
        """Destructor - ensure encryption cleanup"""
        try:
            self.cleanup_encryption()
        except:
            pass  # Don't raise exceptions in destructor
    
    # Phase 5 Methods - Multiple NLP Engine Support
    
    def get_available_engines(self) -> List[Dict[str, str]]:
        """Get list of available NLP engines"""
        engines = []
        for engine_id, engine_data in self.nlp_engines.items():
            model_info = engine_data['model_info']
            engines.append({
                'id': engine_id,
                'name': model_info.name,
                'framework': model_info.framework,
                'language': model_info.language,
                'description': model_info.description,
                'status': model_info.status
            })
        return engines
    
    def set_nlp_engine(self, engine_id: str) -> bool:
        """
        Set the current NLP engine
        
        Args:
            engine_id: ID of the engine to set as current
            
        Returns:
            True if successful, False otherwise
        """
        if engine_id not in self.nlp_engines:
            logging.error(f"NLP engine not found: {engine_id}")
            return False
        
        try:
            self.current_engine_id = engine_id
            self.current_nlp_engine = self.nlp_engines[engine_id]['engine']
            
            # Update analyzer with the new engine
            self._update_analyzer_with_engine(engine_id)
            
            logging.info(f"Switched to NLP engine: {engine_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to set NLP engine {engine_id}: {e}")
            return False
    
    def _update_analyzer_with_engine(self, engine_id: str):
        """Update the analyzer to use a specific NLP engine"""
        if engine_id not in self.nlp_engines:
            return
        
        engine_data = self.nlp_engines[engine_id]
        nlp_engine = engine_data['engine']
        
        # Create a new analyzer with the custom NLP engine
        try:
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            
            # Re-add all our custom recognizers
            self._add_custom_recognizers_to_analyzer()
            
            logging.info(f"Updated analyzer with NLP engine: {engine_id}")
            
        except Exception as e:
            logging.error(f"Failed to update analyzer with engine {engine_id}: {e}")
            # Fall back to default analyzer
            self._initialize_default_analyzer()
    
    def _add_custom_recognizers_to_analyzer(self):
        """Add custom recognizers to the analyzer"""
        # Remove default phone recognizer
        phone_recognizers_to_remove = []
        for recognizer in self.analyzer.registry.recognizers:
            if hasattr(recognizer, 'name') and recognizer.name == "PhoneRecognizer":
                phone_recognizers_to_remove.append(recognizer)
        
        for recognizer in phone_recognizers_to_remove:
            self.analyzer.registry.recognizers.remove(recognizer)
        
        # Add our custom recognizers
        custom_recognizers = [
            EnhancedPhoneRecognizer(),
            AuDvaRecognizer(),
            AuMedicareProviderRecognizer(),
            AuCrnRecognizer(),
            AuPassportRecognizer(),
            AuDriversLicenseRecognizer()
        ]
        
        for recognizer in custom_recognizers:
            self.analyzer.registry.add_recognizer(recognizer)
    
    def get_current_engine_info(self) -> Dict[str, str]:
        """Get information about the current NLP engine"""
        if not self.current_engine_id or self.current_engine_id not in self.nlp_engines:
            return {
                'id': 'default',
                'name': 'Default spaCy Engine',
                'framework': 'spacy',
                'status': 'active'
            }
        
        engine_data = self.nlp_engines[self.current_engine_id]
        model_info = engine_data['model_info']
        
        return {
            'id': self.current_engine_id,
            'name': model_info.name,
            'framework': model_info.framework,
            'language': model_info.language,
            'description': model_info.description,
            'status': 'active'
        }
    
    def refresh_nlp_engines(self) -> bool:
        """Refresh available NLP engines by re-scanning models"""
        try:
            # Refresh model manager
            self.model_manager.refresh_models()
            
            # Store current engine for restoration
            current_engine = self.current_engine_id
            
            # Clear and reinitialize engines
            self.nlp_engines.clear()
            self._initialize_nlp_engines()
            
            # Try to restore previous engine
            if current_engine in self.nlp_engines:
                self.set_nlp_engine(current_engine)
            else:
                self._set_default_engine()
            
            logging.info("NLP engines refreshed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to refresh NLP engines: {e}")
            return False
    
    def get_model_manager(self) -> ModelManager:
        """Get the model manager instance"""
        return self.model_manager
    
    def import_model(self, source_path: str, framework: str, model_name: str = None) -> bool:
        """
        Import a new model and refresh engines
        
        Args:
            source_path: Path to the model to import
            framework: Framework type (spacy, transformers, flair, stanza)
            model_name: Optional custom name for the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from pathlib import Path
            
            # Import the model
            success = self.model_manager.import_model(
                source_path=Path(source_path),
                framework=framework,
                model_name=model_name
            )
            
            if success:
                # Refresh engines to include the new model
                self.refresh_nlp_engines()
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to import model: {e}")
            return False
    
    def get_framework_availability(self) -> Dict[str, bool]:
        """Get availability status of different frameworks"""
        return NlpEngineFactory.get_supported_frameworks()
    
    def check_framework_dependencies(self, framework: str) -> Dict[str, Any]:
        """Check dependencies for a specific framework"""
        return NlpEngineFactory.check_framework_dependencies(framework)
    
    def get_nlp_engine_statistics(self) -> Dict[str, Any]:
        """Get statistics about NLP engines"""
        stats = {
            'total_engines': len(self.nlp_engines),
            'current_engine': self.current_engine_id,
            'by_framework': {},
            'available_frameworks': list(self.model_manager.supported_frameworks)
        }
        
        for engine_id, engine_data in self.nlp_engines.items():
            framework = engine_data['model_info'].framework
            if framework not in stats['by_framework']:
                stats['by_framework'][framework] = 0
            stats['by_framework'][framework] += 1
        
        # Add model manager statistics
        stats['model_statistics'] = self.model_manager.get_model_statistics()
        
        return stats