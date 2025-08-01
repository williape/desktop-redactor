"""
Model Manager for handling multiple NER models and frameworks.

This module provides the ModelManager class which handles:
- Model discovery and validation
- Model caching and import functionality
- Framework compatibility checking
- Model metadata management
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import importlib.util
import json

@dataclass
class ModelInfo:
    """Information about a NER model"""
    id: str
    name: str
    framework: str  # spacy, transformers, flair, stanza
    language: str
    size: int
    path: Optional[Path]
    status: str  # available, loading, error, bundled
    entities: List[str]
    description: str
    version: str = "unknown"
    created_date: Optional[datetime] = None

@dataclass
class ModelMetadata:
    """Extended metadata for a model"""
    version: str
    created_date: datetime
    entity_mappings: Dict[str, str]
    confidence_settings: Dict[str, float]
    framework_version: str = "unknown"
    model_type: str = "unknown"
    training_data: str = "unknown"
    performance_metrics: Dict[str, float] = None

class ModelManager:
    """Manages multiple NER models and frameworks"""
    
    def __init__(self):
        self.cache_dir = Path.home() / "Documents" / "PresidioDesktopRedactor" / "models"
        self.import_dir = self.cache_dir / "import"
        self.model_registry: Dict[str, ModelInfo] = {}
        self.supported_frameworks = ["spacy", "transformers", "flair", "stanza"]
        
        # Configuration templates for different frameworks
        self.config_templates = {
            "spacy": self._get_spacy_config_template(),
            "transformers": self._get_transformers_config_template(),
            "flair": self._get_flair_config_template(),
            "stanza": self._get_stanza_config_template()
        }
        
        # Initialize directories
        self._initialize_directories()
        
        # Discover available models
        self._discover_models()
        
        logging.info(f"ModelManager initialized with {len(self.model_registry)} models")
    
    def _initialize_directories(self):
        """Initialize the cache and import directories"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.import_dir.mkdir(parents=True, exist_ok=True)
            
            # Create framework-specific directories
            for framework in self.supported_frameworks:
                framework_dir = self.cache_dir / framework
                framework_dir.mkdir(exist_ok=True)
            
            logging.info(f"Model directories initialized at {self.cache_dir}")
        except Exception as e:
            logging.error(f"Failed to initialize model directories: {e}")
            raise
    
    def _discover_models(self):
        """Discover all available models"""
        self.model_registry.clear()
        
        # Add bundled models
        bundled_models = self._get_bundled_models()
        for model in bundled_models:
            self.model_registry[model.id] = model
        
        # Discover cached models
        cached_models = self._discover_cached_models()
        for model in cached_models:
            self.model_registry[model.id] = model
        
        # Discover imported models
        imported_models = self._discover_imported_models()
        for model in imported_models:
            self.model_registry[model.id] = model
        
        logging.info(f"Discovered {len(self.model_registry)} total models")
    
    def _get_bundled_models(self) -> List[ModelInfo]:
        """Get information about bundled spaCy models"""
        bundled_models = []
        
        # Check for bundled spaCy models
        try:
            import spacy
            
            # Check for small model
            if self._is_spacy_model_available("en_core_web_sm"):
                bundled_models.append(ModelInfo(
                    id="spacy_sm",
                    name="spaCy Small (en_core_web_sm)",
                    framework="spacy",
                    language="en",
                    size=10 * 1024 * 1024,  # 10MB approximate
                    path=None,  # Bundled - no specific path
                    status="bundled",
                    entities=["PERSON", "ORG", "GPE", "LOC"],
                    description="Fast, lightweight spaCy model",
                    version=spacy.__version__
                ))
            
            # Check for medium model
            if self._is_spacy_model_available("en_core_web_md"):
                bundled_models.append(ModelInfo(
                    id="spacy_md",
                    name="spaCy Medium (en_core_web_md)",
                    framework="spacy",
                    language="en",
                    size=43 * 1024 * 1024,  # 43MB approximate
                    path=None,  # Bundled - no specific path
                    status="bundled",
                    entities=["PERSON", "ORG", "GPE", "LOC"],
                    description="Balanced spaCy model with word vectors",
                    version=spacy.__version__
                ))
            
            # Check for large model (might be user-installed)
            if self._is_spacy_model_available("en_core_web_lg"):
                bundled_models.append(ModelInfo(
                    id="spacy_lg",
                    name="spaCy Large (en_core_web_lg)",
                    framework="spacy",
                    language="en",
                    size=560 * 1024 * 1024,  # 560MB approximate
                    path=None,  # Bundled - no specific path
                    status="bundled",
                    entities=["PERSON", "ORG", "GPE", "LOC"],
                    description="Large spaCy model with word vectors",
                    version=spacy.__version__
                ))
        
        except ImportError:
            logging.warning("spaCy not available - no bundled models")
        
        return bundled_models
    
    def _is_spacy_model_available(self, model_name: str) -> bool:
        """Check if a spaCy model is available"""
        try:
            import spacy
            spacy.load(model_name)
            return True
        except (ImportError, OSError):
            return False
    
    def _discover_cached_models(self) -> List[ModelInfo]:
        """Discover models in cache directories"""
        cached_models = []
        
        for framework in self.supported_frameworks:
            framework_dir = self.cache_dir / framework
            if framework_dir.exists():
                models = self._scan_framework_directory(framework_dir, framework)
                cached_models.extend(models)
        
        return cached_models
    
    def _discover_imported_models(self) -> List[ModelInfo]:
        """Discover models in import directory"""
        imported_models = []
        
        if self.import_dir.exists():
            for item in self.import_dir.iterdir():
                if item.is_dir():
                    # Try to detect framework from directory structure
                    framework = self._detect_framework_from_directory(item)
                    if framework:
                        model_info = self._create_model_info_from_directory(item, framework)
                        if model_info:
                            imported_models.append(model_info)
        
        return imported_models
    
    def _scan_framework_directory(self, framework_dir: Path, framework: str) -> List[ModelInfo]:
        """Scan a framework-specific directory for models"""
        models = []
        
        for model_dir in framework_dir.iterdir():
            if model_dir.is_dir():
                model_info = self._create_model_info_from_directory(model_dir, framework)
                if model_info:
                    models.append(model_info)
        
        return models
    
    def _detect_framework_from_directory(self, model_dir: Path) -> Optional[str]:
        """Detect framework from directory structure"""
        # Check for spaCy models
        if any(f.name == "meta.json" for f in model_dir.iterdir() if f.is_file()):
            return "spacy"
        
        # Check for Transformers models
        if any(f.name == "config.json" for f in model_dir.iterdir() if f.is_file()):
            return "transformers"
        
        # Check for Flair models
        if any(f.name.endswith(".pt") for f in model_dir.iterdir() if f.is_file()):
            return "flair"
        
        # Check for Stanza models
        if any(f.name.endswith(".conllu") for f in model_dir.iterdir() if f.is_file()):
            return "stanza"
        
        return None
    
    def _create_model_info_from_directory(self, model_dir: Path, framework: str) -> Optional[ModelInfo]:
        """Create ModelInfo from a model directory"""
        try:
            model_name = model_dir.name
            model_id = f"{framework}_{model_name}"
            
            # Try to load metadata
            metadata = self._load_model_metadata(model_dir, framework)
            
            # Get directory size
            size = self._get_directory_size(model_dir)
            
            # Default entities based on framework
            default_entities = ["PERSON", "ORG", "GPE", "LOC"]
            
            return ModelInfo(
                id=model_id,
                name=f"{framework.title()} - {model_name}",
                framework=framework,
                language=metadata.get("language", "en"),
                size=size,
                path=model_dir,
                status="available",
                entities=metadata.get("entities", default_entities),
                description=metadata.get("description", f"{framework.title()} model"),
                version=metadata.get("version", "unknown"),
                created_date=metadata.get("created_date")
            )
        
        except Exception as e:
            logging.error(f"Error creating model info for {model_dir}: {e}")
            return None
    
    def _load_model_metadata(self, model_dir: Path, framework: str) -> Dict:
        """Load metadata for a model"""
        metadata = {}
        
        try:
            if framework == "spacy":
                meta_file = model_dir / "meta.json"
                if meta_file.exists():
                    with open(meta_file, 'r') as f:
                        spacy_meta = json.load(f)
                        metadata.update({
                            "language": spacy_meta.get("lang", "en"),
                            "version": spacy_meta.get("version", "unknown"),
                            "description": spacy_meta.get("description", ""),
                            "entities": list(spacy_meta.get("labels", {}).get("ner", []))
                        })
            
            elif framework == "transformers":
                config_file = model_dir / "config.json"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        metadata.update({
                            "description": config.get("_name_or_path", ""),
                            "version": config.get("transformers_version", "unknown")
                        })
            
            # Try to load custom metadata file
            custom_meta_file = model_dir / "presidio_metadata.yaml"
            if custom_meta_file.exists():
                with open(custom_meta_file, 'r') as f:
                    custom_meta = yaml.safe_load(f)
                    metadata.update(custom_meta)
        
        except Exception as e:
            logging.debug(f"Could not load metadata for {model_dir}: {e}")
        
        return metadata
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of a directory"""
        total_size = 0
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logging.debug(f"Could not calculate size for {path}: {e}")
        
        return total_size
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of all available models"""
        return list(self.model_registry.values())
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get a specific model by ID"""
        return self.model_registry.get(model_id)
    
    def get_models_by_framework(self, framework: str) -> List[ModelInfo]:
        """Get all models for a specific framework"""
        return [model for model in self.model_registry.values() if model.framework == framework]
    
    def validate_model(self, model_path: Path, framework: str) -> bool:
        """Validate a model for compatibility"""
        try:
            if not model_path.exists():
                return False
            
            if framework == "spacy":
                return self._validate_spacy_model(model_path)
            elif framework == "transformers":
                return self._validate_transformers_model(model_path)
            elif framework == "flair":
                return self._validate_flair_model(model_path)
            elif framework == "stanza":
                return self._validate_stanza_model(model_path)
            
            return False
        
        except Exception as e:
            logging.error(f"Error validating model {model_path}: {e}")
            return False
    
    def _validate_spacy_model(self, model_path: Path) -> bool:
        """Validate a spaCy model"""
        meta_file = model_path / "meta.json"
        return meta_file.exists()
    
    def _validate_transformers_model(self, model_path: Path) -> bool:
        """Validate a Transformers model"""
        config_file = model_path / "config.json"
        return config_file.exists()
    
    def _validate_flair_model(self, model_path: Path) -> bool:
        """Validate a Flair model"""
        # Look for .pt files
        return any(f.suffix == ".pt" for f in model_path.iterdir() if f.is_file())
    
    def _validate_stanza_model(self, model_path: Path) -> bool:
        """Validate a Stanza model"""
        # Look for .conllu or .pt files
        extensions = {".conllu", ".pt"}
        return any(f.suffix in extensions for f in model_path.iterdir() if f.is_file())
    
    def import_model(self, source_path: Path, framework: str, model_name: str = None) -> bool:
        """Import a model from external source"""
        try:
            if not source_path.exists():
                logging.error(f"Source path does not exist: {source_path}")
                return False
            
            if framework not in self.supported_frameworks:
                logging.error(f"Unsupported framework: {framework}")
                return False
            
            # Validate the model
            if not self.validate_model(source_path, framework):
                logging.error(f"Model validation failed for {source_path}")
                return False
            
            # Determine target directory
            if not model_name:
                model_name = source_path.name
            
            target_dir = self.cache_dir / framework / model_name
            
            # Copy the model
            if source_path.is_dir():
                import shutil
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(source_path, target_dir)
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(source_path, target_dir)
            
            logging.info(f"Successfully imported {framework} model: {model_name}")
            
            # Refresh model registry
            self._discover_models()
            
            return True
        
        except Exception as e:
            logging.error(f"Error importing model: {e}")
            return False
    
    def get_model_config_template(self, framework: str) -> Optional[str]:
        """Get configuration template for a framework"""
        return self.config_templates.get(framework)
    
    def _get_spacy_config_template(self) -> str:
        """Get spaCy configuration template"""
        return """
nlp_engine_name: spacy
models:
  - lang_code: en
    model_name: ${model_name}
ner_model_configuration:
  model_to_presidio_entity_mapping:
    PER: PERSON
    LOC: LOCATION
    ORG: ORGANIZATION
    GPE: LOCATION
  low_confidence_score_multiplier: 0.4
  low_score_entity_names: [ORG]
"""
    
    def _get_transformers_config_template(self) -> str:
        """Get Transformers configuration template"""
        return """
nlp_engine_name: transformers
models:
  - lang_code: en
    model_name:
      spacy: en_core_web_md
      transformers: ${model_name}
ner_model_configuration:
  labels_to_ignore: [O]
  aggregation_strategy: max
  alignment_mode: expand
  model_to_presidio_entity_mapping:
    PER: PERSON
    PERSON: PERSON
    LOC: LOCATION
    LOCATION: LOCATION
    ORG: ORGANIZATION
    ORGANIZATION: ORGANIZATION
"""
    
    def _get_flair_config_template(self) -> str:
        """Get Flair configuration template"""
        return """
framework: flair
model_name: ${model_name}
entity_mapping:
  PER: PERSON
  LOC: LOCATION
  ORG: ORGANIZATION
  MISC: MISC
"""
    
    def _get_stanza_config_template(self) -> str:
        """Get Stanza configuration template"""
        return """
framework: stanza
model_name: ${model_name}
entity_mapping:
  PER: PERSON
  LOC: LOCATION
  ORG: ORGANIZATION
  GPE: LOCATION
"""
    
    def save_model_metadata(self, model_id: str, metadata: ModelMetadata) -> bool:
        """Save metadata for a model"""
        try:
            model = self.get_model_by_id(model_id)
            if not model or not model.path:
                return False
            
            metadata_file = model.path / "presidio_metadata.yaml"
            with open(metadata_file, 'w') as f:
                yaml.dump(asdict(metadata), f)
            
            logging.info(f"Saved metadata for model {model_id}")
            return True
        
        except Exception as e:
            logging.error(f"Error saving metadata for {model_id}: {e}")
            return False
    
    def load_model_metadata_obj(self, model_id: str) -> Optional[ModelMetadata]:
        """Load metadata object for a model"""
        try:
            model = self.get_model_by_id(model_id)
            if not model or not model.path:
                return None
            
            metadata_file = model.path / "presidio_metadata.yaml"
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                data = yaml.safe_load(f)
                return ModelMetadata(**data)
        
        except Exception as e:
            logging.debug(f"Could not load metadata for {model_id}: {e}")
            return None
    
    def get_framework_dependencies(self, framework: str) -> List[str]:
        """Get required dependencies for a framework"""
        dependencies = {
            "spacy": ["spacy>=3.4.0"],
            "transformers": ["transformers>=4.21.0", "torch>=1.12.0"],
            "flair": ["flair>=0.12.0", "torch>=1.12.0"],
            "stanza": ["stanza>=1.4.0", "torch>=1.12.0"]
        }
        
        return dependencies.get(framework, [])
    
    def check_framework_availability(self, framework: str) -> bool:
        """Check if a framework is available/installed"""
        try:
            if framework == "spacy":
                import spacy
                return True
            elif framework == "transformers":
                import transformers
                return True
            elif framework == "flair":
                import flair
                return True
            elif framework == "stanza":
                import stanza
                return True
        except ImportError:
            return False
        
        return False
    
    def get_model_statistics(self) -> Dict:
        """Get statistics about available models"""
        stats = {
            "total_models": len(self.model_registry),
            "by_framework": {},
            "by_status": {},
            "total_size": 0
        }
        
        for model in self.model_registry.values():
            # Framework stats
            if model.framework not in stats["by_framework"]:
                stats["by_framework"][model.framework] = 0
            stats["by_framework"][model.framework] += 1
            
            # Status stats
            if model.status not in stats["by_status"]:
                stats["by_status"][model.status] = 0
            stats["by_status"][model.status] += 1
            
            # Size stats
            stats["total_size"] += model.size
        
        return stats
    
    def cleanup_cache(self, framework: str = None) -> bool:
        """Clean up cached models"""
        try:
            if framework:
                # Clean specific framework
                framework_dir = self.cache_dir / framework
                if framework_dir.exists():
                    import shutil
                    shutil.rmtree(framework_dir)
                    framework_dir.mkdir()
            else:
                # Clean all cache
                for fw in self.supported_frameworks:
                    framework_dir = self.cache_dir / fw
                    if framework_dir.exists():
                        import shutil
                        shutil.rmtree(framework_dir)
                        framework_dir.mkdir()
            
            # Refresh model registry
            self._discover_models()
            
            logging.info(f"Cleaned up cache for {framework or 'all frameworks'}")
            return True
        
        except Exception as e:
            logging.error(f"Error cleaning up cache: {e}")
            return False
    
    def refresh_models(self):
        """Refresh the model registry"""
        self._discover_models()
        logging.info("Model registry refreshed")
    
    def get_model_info_dict(self, model_id: str) -> Optional[Dict]:
        """Get model information as dictionary"""
        model = self.get_model_by_id(model_id)
        if model:
            return asdict(model)
        return None
    
    def get_default_model_for_framework(self, framework: str) -> Optional[ModelInfo]:
        """Get the default/recommended model for a framework"""
        models = self.get_models_by_framework(framework)
        
        if not models:
            return None
        
        # For spaCy, prefer medium model, then large, then small
        if framework == "spacy":
            for model in models:
                if "md" in model.id:
                    return model
            for model in models:
                if "lg" in model.id:
                    return model
            for model in models:
                if "sm" in model.id:
                    return model
        
        # For other frameworks, return the first available
        return models[0]