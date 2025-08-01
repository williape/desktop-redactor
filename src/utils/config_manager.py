"""
Configuration Manager for Presidio Desktop Redactor

Handles application configuration persistence including:
- User preferences and settings
- UI state (window geometry, collapsed sections)
- Detection settings (entities, confidence, lists)
- Processing options (anonymization methods, encryption)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class UIPreferences:
    """UI preferences and state"""
    theme: str = "auto"  # auto, light, dark
    sections_collapsed: Dict[str, bool] = None
    window_geometry: Dict[str, int] = None
    
    def __post_init__(self):
        if self.sections_collapsed is None:
            self.sections_collapsed = {
                "detection_settings": False,
                "processing_options": True,
                "output_settings": True
            }
        if self.window_geometry is None:
            self.window_geometry = {
                "width": 1400,
                "height": 900,
                "x": 100,
                "y": 100
            }


@dataclass 
class DetectionSettings:
    """Detection and analysis settings"""
    confidence_threshold: float = 0.7
    selected_entities: list = None
    enable_custom_lists: bool = False
    allowlist_enabled: bool = True
    denylist_enabled: bool = True
    
    def __post_init__(self):
        if self.selected_entities is None:
            self.selected_entities = [
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", 
                "CREDIT_CARD", "IBAN", "IP_ADDRESS", "URL"
            ]


@dataclass
class ProcessingOptions:
    """Processing and anonymization options"""
    default_anonymization: str = "redact"
    encryption_enabled: bool = False
    save_encryption_key: bool = False
    show_decryption_instructions: bool = True


@dataclass
class PreviewSettings:
    """Preview functionality settings"""
    sample_size: int = 1000
    auto_preview: bool = False
    show_confidence_scores: bool = True


class ConfigManager:
    """
    Manages application configuration and settings persistence
    
    Configuration is stored in ~/Documents/PresidioDesktopRedactor/config/
    """
    
    VERSION = "2.0"
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigManager
        
        Args:
            config_dir: Custom config directory path (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "PresidioDesktopRedactor" / "config"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Config file paths
        self.main_config_file = self.config_dir / "settings.json"
        self.lists_config_file = self.config_dir / "lists.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize default configuration
        self.ui_preferences = UIPreferences()
        self.detection_settings = DetectionSettings()
        self.processing_options = ProcessingOptions()
        self.preview_settings = PreviewSettings()
        
        # Load existing configuration
        self.load_config()
    
    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get complete configuration as dictionary
        
        Returns:
            Dictionary containing all configuration data
        """
        return {
            "version": self.VERSION,
            "profile_name": "Default",
            "ui_preferences": asdict(self.ui_preferences),
            "detection_settings": asdict(self.detection_settings),
            "processing_options": asdict(self.processing_options),
            "preview_settings": asdict(self.preview_settings),
            "last_updated": datetime.now().isoformat()
        }
    
    def save_config(self) -> bool:
        """
        Save current configuration to disk
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create backup before saving
            self._create_backup()
            
            config_data = self.get_config_dict()
            
            with open(self.main_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.main_config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self) -> bool:
        """
        Load configuration from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not self.main_config_file.exists():
                self.logger.info("No existing configuration found, using defaults")
                return self.save_config()  # Save defaults
            
            with open(self.main_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check for version compatibility and migration
            file_version = config_data.get("version", "1.0")
            if file_version != self.VERSION:
                self.logger.info(f"Migrating configuration from v{file_version} to v{self.VERSION}")
                config_data = self._migrate_config(config_data, file_version)
            
            # Load configuration sections
            if "ui_preferences" in config_data:
                self.ui_preferences = UIPreferences(**config_data["ui_preferences"])
            
            if "detection_settings" in config_data:
                self.detection_settings = DetectionSettings(**config_data["detection_settings"])
            
            if "processing_options" in config_data:
                self.processing_options = ProcessingOptions(**config_data["processing_options"])
            
            if "preview_settings" in config_data:
                self.preview_settings = PreviewSettings(**config_data["preview_settings"])
            
            self.logger.info(f"Configuration loaded from {self.main_config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.logger.info("Using default configuration")
            return False
    
    def save_lists(self, lists_data: Dict[str, Any]) -> bool:
        """
        Save lists configuration to separate file
        
        Args:
            lists_data: Dictionary containing allowlist and denylist data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Add metadata to lists data
            lists_with_metadata = {
                "version": self.VERSION,
                "lists": lists_data,
                "last_modified": datetime.now().isoformat()
            }
            
            with open(self.lists_config_file, 'w', encoding='utf-8') as f:
                json.dump(lists_with_metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Lists saved to {self.lists_config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save lists: {e}")
            return False
    
    def load_lists(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Load lists configuration from disk
        
        Returns:
            Tuple of (success, lists_data)
        """
        try:
            if not self.lists_config_file.exists():
                self.logger.info("No existing lists configuration found")
                return True, {"allowlist": {"words": []}, "denylist": {"entries": []}}
            
            with open(self.lists_config_file, 'r', encoding='utf-8') as f:
                lists_data = json.load(f)
            
            # Extract lists data from metadata wrapper
            if "lists" in lists_data:
                return True, lists_data["lists"]
            else:
                # Backward compatibility - assume the whole file is lists data
                return True, lists_data
                
        except Exception as e:
            self.logger.error(f"Failed to load lists: {e}")
            return False, {"allowlist": {"words": []}, "denylist": {"entries": []}}
    
    def export_config(self, export_path: str) -> bool:
        """
        Export configuration to specified file
        
        Args:
            export_path: Path to export configuration to
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_data = self.get_config_dict()
            
            # Include lists data in export
            success, lists_data = self.load_lists()
            if success:
                export_data["lists"] = lists_data
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Import configuration from specified file
        
        Args:
            import_path: Path to import configuration from
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if not self._validate_config_data(import_data):
                self.logger.error("Invalid configuration data in import file")
                return False
            
            # Create backup before importing
            self._create_backup()
            
            # Import configuration sections
            if "ui_preferences" in import_data:
                self.ui_preferences = UIPreferences(**import_data["ui_preferences"])
            
            if "detection_settings" in import_data:
                self.detection_settings = DetectionSettings(**import_data["detection_settings"])
            
            if "processing_options" in import_data:
                self.processing_options = ProcessingOptions(**import_data["processing_options"])
            
            if "preview_settings" in import_data:
                self.preview_settings = PreviewSettings(**import_data["preview_settings"])
            
            # Import lists if present
            if "lists" in import_data:
                self.save_lists(import_data["lists"])
            
            # Save imported configuration
            self.save_config()
            
            self.logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values
        
        Returns:
            True if reset successfully, False otherwise
        """
        try:
            # Create backup before reset
            self._create_backup()
            
            # Reset to defaults
            self.ui_preferences = UIPreferences()
            self.detection_settings = DetectionSettings()
            self.processing_options = ProcessingOptions()
            self.preview_settings = PreviewSettings()
            
            # Save defaults
            success = self.save_config()
            
            if success:
                self.logger.info("Configuration reset to defaults")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create backup of current configuration"""
        try:
            if self.main_config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"settings_backup_{timestamp}.json"
                
                # Copy current config to backup
                import shutil
                shutil.copy2(self.main_config_file, backup_file)
                
                # Keep only last 10 backups
                backups = sorted(self.backup_dir.glob("settings_backup_*.json"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                
                self.logger.debug(f"Configuration backup created: {backup_file}")
                
        except Exception as e:
            self.logger.warning(f"Failed to create configuration backup: {e}")
    
    def _migrate_config(self, config_data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """
        Migrate configuration from older version
        
        Args:
            config_data: Configuration data to migrate
            from_version: Version to migrate from
            
        Returns:
            Migrated configuration data
        """
        try:
            self.logger.info(f"Migrating configuration from version {from_version} to {self.VERSION}")
            
            # Update version
            config_data["version"] = self.VERSION
            
            # Add new fields with defaults if they don't exist
            if "ui_preferences" not in config_data:
                config_data["ui_preferences"] = asdict(UIPreferences())
            
            if "detection_settings" not in config_data:
                config_data["detection_settings"] = asdict(DetectionSettings())
            
            if "processing_options" not in config_data:
                config_data["processing_options"] = asdict(ProcessingOptions())
            
            if "preview_settings" not in config_data:
                config_data["preview_settings"] = asdict(PreviewSettings())
            
            # Handle specific migration logic for different versions
            if from_version == "1.0":
                # Migrate v1.0 settings to v2.0 structure
                self._migrate_from_v1(config_data)
            
            return config_data
            
        except Exception as e:
            self.logger.error(f"Configuration migration failed: {e}")
            return config_data
    
    def _migrate_from_v1(self, config_data: Dict[str, Any]) -> None:
        """Migrate from v1.0 configuration structure"""
        # Add any v1.0 specific migration logic here
        pass
    
    def _validate_config_data(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration data structure
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(config_data, dict):
                return False
            
            # Check required fields exist and have correct types
            if "version" in config_data and not isinstance(config_data["version"], str):
                return False
            
            # Validate sections if present
            for section in ["ui_preferences", "detection_settings", "processing_options", "preview_settings"]:
                if section in config_data and not isinstance(config_data[section], dict):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of current configuration
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "version": self.VERSION,
            "config_dir": str(self.config_dir),
            "main_config_exists": self.main_config_file.exists(),
            "lists_config_exists": self.lists_config_file.exists(),
            "theme": self.ui_preferences.theme,
            "selected_entities_count": len(self.detection_settings.selected_entities),
            "confidence_threshold": self.detection_settings.confidence_threshold,
            "custom_lists_enabled": self.detection_settings.enable_custom_lists,
            "encryption_enabled": self.processing_options.encryption_enabled,
            "last_config_file_modified": (
                datetime.fromtimestamp(self.main_config_file.stat().st_mtime).isoformat()
                if self.main_config_file.exists() else None
            )
        }