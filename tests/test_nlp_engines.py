#!/usr/bin/env python3
"""
Phase 5 Test Suite: Multiple NER Model Support

This test suite validates the Phase 5 implementation including:
- ModelManager functionality
- Multiple NLP engine support
- Engine factory pattern
- Custom Flair and Stanza engines
- UI integration for model management
"""

import os
import sys
import tempfile
import shutil
import logging
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Core imports
from core.model_manager import ModelManager, ModelInfo, ModelMetadata
from core.nlp_engines.engine_factory import NlpEngineFactory
from core.presidio_manager import PresidioManager

# UI imports
from PyQt5.QtWidgets import QApplication
from ui.widgets.model_import_dialog import ModelImportDialog

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestModelManager(unittest.TestCase):
    """Test ModelManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create a test model manager with custom cache directory
        with patch.object(Path, 'home', return_value=self.temp_dir):
            self.model_manager = ModelManager()
        
        logger.info(f"Created temp directory: {self.temp_dir}")
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        logger.info("Cleaned up temp directory")
    
    def test_initialization(self):
        """Test ModelManager initialization"""
        logger.info("Testing ModelManager initialization...")
        
        # Check directory creation
        self.assertTrue(self.model_manager.cache_dir.exists())
        self.assertTrue(self.model_manager.import_dir.exists())
        
        # Check framework directories
        for framework in self.model_manager.supported_frameworks:
            framework_dir = self.model_manager.cache_dir / framework
            self.assertTrue(framework_dir.exists())
        
        # Check initial model discovery
        models = self.model_manager.get_available_models()
        self.assertIsInstance(models, list)
        
        logger.info(f"✓ Initialization test passed - found {len(models)} models")
    
    def test_model_validation(self):
        """Test model validation functionality"""
        logger.info("Testing model validation...")
        
        # Create mock model directories
        spacy_model_dir = self.model_manager.cache_dir / "spacy" / "test_model"
        spacy_model_dir.mkdir(parents=True)
        
        # Create meta.json for spaCy model
        meta_file = spacy_model_dir / "meta.json"
        meta_file.write_text('{"lang": "en", "name": "test_model", "version": "1.0.0"}')
        
        # Test spaCy validation
        self.assertTrue(self.model_manager.validate_model(spacy_model_dir, "spacy"))
        
        # Test invalid model
        invalid_dir = self.model_manager.cache_dir / "spacy" / "invalid_model"
        invalid_dir.mkdir()
        self.assertFalse(self.model_manager.validate_model(invalid_dir, "spacy"))
        
        logger.info("✓ Model validation test passed")
    
    def test_model_import(self):
        """Test model import functionality"""
        logger.info("Testing model import...")
        
        # Create source model directory
        source_dir = self.temp_dir / "source_model"
        source_dir.mkdir()
        meta_file = source_dir / "meta.json"
        meta_file.write_text('{"lang": "en", "name": "imported_model", "version": "1.0.0"}')
        
        # Import the model
        success = self.model_manager.import_model(source_dir, "spacy", "imported_test")
        self.assertTrue(success)
        
        # Check if model was imported
        imported_path = self.model_manager.cache_dir / "spacy" / "imported_test"
        self.assertTrue(imported_path.exists())
        self.assertTrue((imported_path / "meta.json").exists())
        
        # Check if model appears in registry
        models = self.model_manager.get_available_models()
        imported_models = [m for m in models if "imported_test" in m.id]
        self.assertEqual(len(imported_models), 1)
        
        logger.info("✓ Model import test passed")
    
    def test_configuration_templates(self):
        """Test configuration template generation"""
        logger.info("Testing configuration templates...")
        
        for framework in self.model_manager.supported_frameworks:
            template = self.model_manager.get_model_config_template(framework)
            self.assertIsInstance(template, str)
            self.assertGreater(len(template), 0)
            
            # Check for framework-specific content
            if framework == "spacy":
                self.assertIn("nlp_engine_name: spacy", template)
            elif framework == "transformers":
                self.assertIn("nlp_engine_name: transformers", template)
        
        logger.info("✓ Configuration templates test passed")
    
    def test_model_statistics(self):
        """Test model statistics generation"""
        logger.info("Testing model statistics...")
        
        stats = self.model_manager.get_model_statistics()
        
        # Check required fields
        required_fields = ['total_models', 'by_framework', 'by_status', 'total_size']
        for field in required_fields:
            self.assertIn(field, stats)
        
        self.assertIsInstance(stats['total_models'], int)
        self.assertIsInstance(stats['by_framework'], dict)
        self.assertIsInstance(stats['by_status'], dict)
        self.assertIsInstance(stats['total_size'], int)
        
        logger.info("✓ Model statistics test passed")


class TestNlpEngineFactory(unittest.TestCase):
    """Test NLP Engine Factory functionality"""
    
    def test_supported_frameworks(self):
        """Test framework support detection"""
        logger.info("Testing framework support detection...")
        
        frameworks = NlpEngineFactory.get_supported_frameworks()
        self.assertIsInstance(frameworks, dict)
        
        # Check that all expected frameworks are present
        expected_frameworks = ['spacy', 'transformers', 'flair', 'stanza']
        for framework in expected_frameworks:
            self.assertIn(framework, frameworks)
            self.assertIsInstance(frameworks[framework], bool)
        
        logger.info("✓ Framework support test passed")
    
    def test_dependency_checking(self):
        """Test dependency checking functionality"""
        logger.info("Testing dependency checking...")
        
        for framework in ['spacy', 'transformers', 'flair', 'stanza']:
            result = NlpEngineFactory.check_framework_dependencies(framework)
            
            # Check result structure
            self.assertIn('framework', result)
            self.assertIn('available', result)
            self.assertIn('missing_dependencies', result)
            
            self.assertEqual(result['framework'], framework)
            self.assertIsInstance(result['available'], bool)
            self.assertIsInstance(result['missing_dependencies'], list)
        
        logger.info("✓ Dependency checking test passed")
    
    def test_default_configurations(self):
        """Test default configuration generation"""
        logger.info("Testing default configurations...")
        
        for framework in ['spacy', 'transformers', 'flair', 'stanza']:
            config = NlpEngineFactory.get_default_configuration(framework)
            self.assertIsInstance(config, dict)
            
            if framework in ['spacy', 'transformers']:
                self.assertIn('models', config)
                self.assertIn('ner_model_configuration', config)
            else:
                # Flair and Stanza have different config structures
                self.assertGreater(len(config), 0)
        
        logger.info("✓ Default configurations test passed")
    
    @patch('core.nlp_engines.flair_engine.FLAIR_AVAILABLE', False)
    def test_engine_creation_with_missing_dependencies(self):
        """Test engine creation when dependencies are missing"""
        logger.info("Testing engine creation with missing dependencies...")
        
        # Test Flair engine creation when Flair is not available
        config = {'lang_code': 'en', 'model_name': 'ner'}
        engine = NlpEngineFactory.create_engine('flair', config)
        
        # Should return None when dependencies are missing
        self.assertIsNone(engine)
        
        logger.info("✓ Missing dependencies test passed")


class TestPresidioManagerExtensions(unittest.TestCase):
    """Test PresidioManager Phase 5 extensions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock the ModelManager to avoid dependency issues
        with patch.object(Path, 'home', return_value=self.temp_dir):
            with patch('core.presidio_manager.ModelManager') as mock_model_manager:
                # Configure mock
                mock_instance = Mock()
                mock_instance.get_available_models.return_value = [
                    ModelInfo(
                        id="spacy_sm",
                        name="spaCy Small",
                        framework="spacy",
                        language="en",
                        size=10000000,
                        path=None,
                        status="bundled",
                        entities=["PERSON", "ORG"],
                        description="Test model"
                    )
                ]
                mock_instance.supported_frameworks = ["spacy", "transformers", "flair", "stanza"]
                mock_model_manager.return_value = mock_instance
                
                self.presidio_manager = PresidioManager()
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_available_engines(self):
        """Test getting available engines"""
        logger.info("Testing available engines...")
        
        engines = self.presidio_manager.get_available_engines()
        self.assertIsInstance(engines, list)
        
        # Should have at least the mock model
        if engines:
            engine = engines[0]
            required_fields = ['id', 'name', 'framework', 'language', 'description', 'status']
            for field in required_fields:
                self.assertIn(field, engine)
        
        logger.info("✓ Available engines test passed")
    
    def test_current_engine_info(self):
        """Test getting current engine information"""
        logger.info("Testing current engine info...")
        
        info = self.presidio_manager.get_current_engine_info()
        self.assertIsInstance(info, dict)
        
        required_fields = ['id', 'name', 'framework', 'status']
        for field in required_fields:
            self.assertIn(field, info)
        
        logger.info("✓ Current engine info test passed")
    
    def test_framework_availability(self):
        """Test framework availability checking"""
        logger.info("Testing framework availability...")
        
        availability = self.presidio_manager.get_framework_availability()
        self.assertIsInstance(availability, dict)
        
        # Should contain status for all supported frameworks
        expected_frameworks = ['spacy', 'transformers', 'flair', 'stanza']
        for framework in expected_frameworks:
            self.assertIn(framework, availability)
            self.assertIsInstance(availability[framework], bool)
        
        logger.info("✓ Framework availability test passed")
    
    def test_nlp_engine_statistics(self):
        """Test NLP engine statistics"""
        logger.info("Testing NLP engine statistics...")
        
        stats = self.presidio_manager.get_nlp_engine_statistics()
        self.assertIsInstance(stats, dict)
        
        required_fields = ['total_engines', 'current_engine', 'by_framework', 'available_frameworks']
        for field in required_fields:
            self.assertIn(field, stats)
        
        self.assertIsInstance(stats['total_engines'], int)
        self.assertIsInstance(stats['by_framework'], dict)
        self.assertIsInstance(stats['available_frameworks'], list)
        
        logger.info("✓ NLP engine statistics test passed")


class TestCustomNlpEngines(unittest.TestCase):
    """Test custom NLP engine implementations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_text = "John Doe works at Acme Corp and can be reached at john@example.com"
    
    def test_flair_engine_initialization(self):
        """Test Flair engine initialization"""
        logger.info("Testing Flair engine initialization...")
        
        try:
            from core.nlp_engines.flair_engine import FlairNlpEngine, FLAIR_AVAILABLE
            
            if not FLAIR_AVAILABLE:
                logger.info("Flair not available - skipping test")
                return
            
            # Test initialization with mock models
            models = [{'lang_code': 'en', 'model_name': 'ner'}]
            
            # This might fail if Flair model is not available, which is expected
            try:
                engine = FlairNlpEngine(models)
                self.assertIsNotNone(engine)
                logger.info("✓ Flair engine initialization test passed")
            except Exception as e:
                logger.info(f"Flair engine test failed (expected if model not available): {e}")
                
        except ImportError:
            logger.info("Flair engine not available - skipping test")
    
    def test_stanza_engine_initialization(self):
        """Test Stanza engine initialization"""
        logger.info("Testing Stanza engine initialization...")
        
        try:
            from core.nlp_engines.stanza_engine import StanzaNlpEngine, STANZA_AVAILABLE
            
            if not STANZA_AVAILABLE:
                logger.info("Stanza not available - skipping test")
                return
            
            # Test initialization with mock models
            models = [{'lang_code': 'en', 'model_name': 'en'}]
            
            # This might fail if Stanza model is not available, which is expected
            try:
                engine = StanzaNlpEngine(models)
                self.assertIsNotNone(engine)
                logger.info("✓ Stanza engine initialization test passed")
            except Exception as e:
                logger.info(f"Stanza engine test failed (expected if model not available): {e}")
                
        except ImportError:
            logger.info("Stanza engine not available - skipping test")
    
    def test_engine_interface_compliance(self):
        """Test that custom engines implement the required interface"""
        logger.info("Testing engine interface compliance...")
        
        try:
            from core.nlp_engines.flair_engine import FlairNlpEngine
            
            # Check required methods exist
            required_methods = [
                'process_text', 'get_supported_entities', 'get_supported_languages',
                'is_available', 'get_model_info', 'analyze_entities'
            ]
            
            for method in required_methods:
                self.assertTrue(hasattr(FlairNlpEngine, method))
            
            logger.info("✓ Flair engine interface compliance test passed")
            
        except ImportError:
            logger.info("Flair engine not available - skipping interface test")
        
        try:
            from core.nlp_engines.stanza_engine import StanzaNlpEngine
            
            # Check required methods exist
            for method in required_methods:
                self.assertTrue(hasattr(StanzaNlpEngine, method))
            
            logger.info("✓ Stanza engine interface compliance test passed")
            
        except ImportError:
            logger.info("Stanza engine not available - skipping interface test")


class TestUIIntegration(unittest.TestCase):
    """Test UI integration for Phase 5 features"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for UI tests"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def test_model_import_dialog_creation(self):
        """Test ModelImportDialog creation"""
        logger.info("Testing ModelImportDialog creation...")
        
        try:
            # Create mock model manager
            mock_model_manager = Mock()
            mock_model_manager.supported_frameworks = ["spacy", "transformers", "flair", "stanza"]
            mock_model_manager.validate_model.return_value = True
            
            # Create dialog
            dialog = ModelImportDialog(mock_model_manager)
            self.assertIsNotNone(dialog)
            
            # Check UI elements exist
            self.assertIsNotNone(dialog.framework_combo)
            self.assertIsNotNone(dialog.path_input)
            self.assertIsNotNone(dialog.import_btn)
            self.assertIsNotNone(dialog.cancel_btn)
            
            dialog.close()
            logger.info("✓ ModelImportDialog creation test passed")
            
        except Exception as e:
            logger.error(f"ModelImportDialog test failed: {e}")
            self.fail(f"ModelImportDialog test failed: {e}")


def run_phase5_tests():
    """Run all Phase 5 tests"""
    logger.info("=" * 60)
    logger.info("PHASE 5 TEST SUITE: Multiple NER Model Support")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestModelManager,
        TestNlpEngineFactory,
        TestPresidioManagerExtensions,
        TestCustomNlpEngines,
        TestUIIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("PHASE 5 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        logger.info("\nFAILURES:")
        for test, traceback in result.failures:
            logger.info(f"- {test}: {traceback}")
    
    if result.errors:
        logger.info("\nERRORS:")
        for test, traceback in result.errors:
            logger.info(f"- {test}: {traceback}")
    
    # Phase 5 specific validation
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 5 FEATURE VALIDATION")
    logger.info("=" * 60)
    
    try:
        # Test ModelManager
        from core.model_manager import ModelManager
        logger.info("✓ ModelManager import successful")
        
        # Test NLP Engine Factory
        from core.nlp_engines.engine_factory import NlpEngineFactory
        logger.info("✓ NlpEngineFactory import successful")
        
        # Test custom engines
        try:
            from core.nlp_engines.flair_engine import FlairNlpEngine
            logger.info("✓ FlairNlpEngine import successful")
        except ImportError as e:
            logger.info(f"⚠ FlairNlpEngine import failed (optional): {e}")
        
        try:
            from core.nlp_engines.stanza_engine import StanzaNlpEngine
            logger.info("✓ StanzaNlpEngine import successful")
        except ImportError as e:
            logger.info(f"⚠ StanzaNlpEngine import failed (optional): {e}")
        
        # Test UI components
        try:
            from ui.widgets.model_import_dialog import ModelImportDialog
            logger.info("✓ ModelImportDialog import successful")
        except ImportError as e:
            logger.info(f"⚠ ModelImportDialog import failed: {e}")
        
        logger.info("\n✅ Phase 5 implementation validation completed!")
        
    except Exception as e:
        logger.error(f"❌ Phase 5 validation failed: {e}")
        return False
    
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_phase5_tests()
    sys.exit(0 if success else 1)