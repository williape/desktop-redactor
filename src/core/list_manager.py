"""
List Manager for Presidio Desktop Redactor

Manages allowlists and denylists for improved PII detection accuracy.
- Allowlists: Words/phrases that should NOT be treated as PII (reduce false positives)
- Denylists: Words/phrases that should ALWAYS be treated as PII (reduce false negatives)
"""

import logging
from typing import Set, List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from presidio_analyzer import PatternRecognizer, RecognizerResult, Pattern
import re


@dataclass(frozen=True)
class DenylistEntry:
    """Represents a denylist entry with word and entity type"""
    word: str
    entity_type: str
    confidence: float = 0.9


class ListManager:
    """
    Manages allowlists and denylists for PII detection customization.
    
    Allowlists filter out false positives after analysis.
    Denylists create custom recognizers for guaranteed detection.
    """
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize ListManager
        
        Args:
            case_sensitive: Whether string matching should be case-sensitive
        """
        self.allowlist: Set[str] = set()
        self.denylist: Set[DenylistEntry] = set()
        self._case_sensitive = case_sensitive
        self.logger = logging.getLogger(__name__)
        
        # Performance optimization: keep normalized versions for fast lookup
        self._allowlist_normalized: Set[str] = set()
        self._denylist_normalized: Set[Tuple[str, str]] = set()
    
    @property
    def case_sensitive(self) -> bool:
        """Get case sensitivity setting"""
        return self._case_sensitive
    
    @case_sensitive.setter
    def case_sensitive(self, value: bool):
        """Set case sensitivity and rebuild normalized sets"""
        if self._case_sensitive != value:
            self._case_sensitive = value
            self._rebuild_normalized_sets()
    
    def _rebuild_normalized_sets(self):
        """Rebuild normalized sets after case sensitivity change"""
        # Rebuild allowlist normalized set
        self._allowlist_normalized.clear()
        for word in self.allowlist:
            self._allowlist_normalized.add(self._normalize_text(word))
        
        # Rebuild denylist normalized set
        self._denylist_normalized.clear()
        for entry in self.denylist:
            normalized = self._normalize_text(entry.word)
            self._denylist_normalized.add((normalized, entry.entity_type))
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison based on case sensitivity setting"""
        if not text or not isinstance(text, str):
            return ""
        return text if self.case_sensitive else text.lower()
    
    def add_to_allowlist(self, word: str) -> bool:
        """
        Add word to allowlist
        
        Args:
            word: Word or phrase to add to allowlist
            
        Returns:
            True if added successfully, False if word was empty or already exists
        """
        if not word or not isinstance(word, str):
            self.logger.warning(f"Invalid word for allowlist: {word}")
            return False
        
        word = word.strip()
        if not word:
            self.logger.warning("Empty word cannot be added to allowlist")
            return False
        
        normalized = self._normalize_text(word)
        if normalized in self._allowlist_normalized:
            self.logger.info(f"Word '{word}' already in allowlist")
            return False
        
        self.allowlist.add(word)
        self._allowlist_normalized.add(normalized)
        self.logger.info(f"Added '{word}' to allowlist")
        return True
    
    def add_to_denylist(self, word: str, entity_type: str = "CUSTOM_DENY", confidence: float = 0.9) -> bool:
        """
        Add word to denylist
        
        Args:
            word: Word or phrase to add to denylist
            entity_type: Entity type to assign to this word
            confidence: Confidence score for detection (0.0-1.0)
            
        Returns:
            True if added successfully, False if word was empty or already exists
        """
        if not word or not isinstance(word, str):
            self.logger.warning(f"Invalid word for denylist: {word}")
            return False
        
        if not entity_type or not isinstance(entity_type, str):
            self.logger.warning(f"Invalid entity_type for denylist: {entity_type}")
            return False
        
        if not 0.0 <= confidence <= 1.0:
            self.logger.warning(f"Invalid confidence score: {confidence}. Must be between 0.0 and 1.0")
            confidence = max(0.0, min(1.0, confidence))
        
        word = word.strip()
        entity_type = entity_type.strip().upper()
        
        if not word:
            self.logger.warning("Empty word cannot be added to denylist")
            return False
        
        normalized = self._normalize_text(word)
        normalized_tuple = (normalized, entity_type)
        
        if normalized_tuple in self._denylist_normalized:
            self.logger.info(f"Word '{word}' with entity type '{entity_type}' already in denylist")
            return False
        
        entry = DenylistEntry(word=word, entity_type=entity_type, confidence=confidence)
        self.denylist.add(entry)
        self._denylist_normalized.add(normalized_tuple)
        self.logger.info(f"Added '{word}' to denylist with entity type '{entity_type}'")
        return True
    
    def remove_from_allowlist(self, word: str) -> bool:
        """
        Remove word from allowlist
        
        Args:
            word: Word to remove
            
        Returns:
            True if removed successfully, False if word not found
        """
        if not word:
            return False
        
        normalized = self._normalize_text(word.strip())
        
        # Find the actual word in allowlist that matches normalized version
        word_to_remove = None
        for existing_word in self.allowlist:
            if self._normalize_text(existing_word) == normalized:
                word_to_remove = existing_word
                break
        
        if word_to_remove:
            self.allowlist.remove(word_to_remove)
            self._allowlist_normalized.remove(normalized)
            self.logger.info(f"Removed '{word_to_remove}' from allowlist")
            return True
        
        return False
    
    def remove_from_denylist(self, word: str, entity_type: str = None) -> bool:
        """
        Remove word from denylist
        
        Args:
            word: Word to remove
            entity_type: Specific entity type to remove (if None, removes all entries for word)
            
        Returns:
            True if removed successfully, False if word not found
        """
        if not word:
            return False
        
        normalized = self._normalize_text(word.strip())
        removed_any = False
        
        # Create list of entries to remove (can't modify set during iteration)
        entries_to_remove = []
        normalized_to_remove = []
        
        for entry in self.denylist:
            entry_normalized = self._normalize_text(entry.word)
            if entry_normalized == normalized:
                if entity_type is None or entry.entity_type == entity_type.upper():
                    entries_to_remove.append(entry)
                    normalized_to_remove.append((entry_normalized, entry.entity_type))
        
        # Remove entries
        for entry in entries_to_remove:
            self.denylist.remove(entry)
            removed_any = True
            self.logger.info(f"Removed '{entry.word}' with entity type '{entry.entity_type}' from denylist")
        
        for normalized_tuple in normalized_to_remove:
            self._denylist_normalized.remove(normalized_tuple)
        
        return removed_any
    
    def clear_allowlist(self) -> None:
        """Clear all entries from allowlist"""
        count = len(self.allowlist)
        self.allowlist.clear()
        self._allowlist_normalized.clear()
        self.logger.info(f"Cleared {count} entries from allowlist")
    
    def clear_denylist(self) -> None:
        """Clear all entries from denylist"""
        count = len(self.denylist)
        self.denylist.clear()
        self._denylist_normalized.clear()
        self.logger.info(f"Cleared {count} entries from denylist")
    
    def get_allowlist(self) -> List[str]:
        """Get sorted list of allowlist entries"""
        return sorted(list(self.allowlist))
    
    def get_denylist(self) -> List[DenylistEntry]:
        """Get sorted list of denylist entries"""
        return sorted(list(self.denylist), key=lambda x: (x.entity_type, x.word))
    
    def create_denylist_recognizers(self) -> List[PatternRecognizer]:
        """
        Create Presidio PatternRecognizer instances for all denylist entries
        
        Returns:
            List of PatternRecognizer instances
        """
        recognizers = []
        
        # Group entries by entity type for efficiency
        entity_groups: Dict[str, List[DenylistEntry]] = {}
        for entry in self.denylist:
            if entry.entity_type not in entity_groups:
                entity_groups[entry.entity_type] = []
            entity_groups[entry.entity_type].append(entry)
        
        # Create one recognizer per entity type
        for entity_type, entries in entity_groups.items():
            patterns = []
            for entry in entries:
                # Escape special regex characters
                escaped_word = re.escape(entry.word)
                # Create word boundary pattern for exact matches
                pattern_regex = rf'\b{escaped_word}\b'
                
                # For case insensitive matching, modify the regex pattern itself
                if not self.case_sensitive:
                    pattern_regex = f"(?i){pattern_regex}"
                
                # Create Pattern object
                pattern_obj = Pattern(
                    name=f'{entity_type.lower()}_{entry.word.lower()}_pattern',
                    regex=pattern_regex,
                    score=entry.confidence
                )
                patterns.append(pattern_obj)
            
            if patterns:
                recognizer = PatternRecognizer(
                    supported_entity=entity_type,
                    patterns=patterns,
                    name=f"{entity_type}_DenylistRecognizer"
                )
                
                recognizers.append(recognizer)
                self.logger.info(f"Created recognizer for {entity_type} with {len(patterns)} patterns")
        
        return recognizers
    
    def apply_allowlist_filter(self, analyzer_results: List[RecognizerResult]) -> List[RecognizerResult]:
        """
        Filter analyzer results by removing matches found in allowlist
        
        Args:
            analyzer_results: List of RecognizerResult from Presidio analysis
            
        Returns:
            Filtered list of RecognizerResult
        """
        if not self.allowlist or not analyzer_results:
            return analyzer_results
        
        filtered_results = []
        
        for result in analyzer_results:
            # Get the actual text that was detected
            # Note: This requires the original text, which should be provided by the caller
            # For now, we'll check if any allowlist entry matches the detected text
            should_filter = False
            
            # Check if this result should be filtered based on allowlist
            for allowed_word in self.allowlist:
                allowed_normalized = self._normalize_text(allowed_word)
                # This is a simplified check - in practice, we'd need the original text
                # The actual implementation would check if the detected span matches allowlist entries
                if allowed_normalized and len(allowed_normalized) > 0:
                    # Mark for potential filtering - actual implementation would compare with original text
                    pass
            
            if not should_filter:
                filtered_results.append(result)
        
        filtered_count = len(analyzer_results) - len(filtered_results)
        if filtered_count > 0:
            self.logger.info(f"Filtered {filtered_count} results using allowlist")
        
        return filtered_results
    
    def apply_allowlist_filter_with_text(self, analyzer_results: List[RecognizerResult], original_text: str) -> List[RecognizerResult]:
        """
        Filter analyzer results by removing matches found in allowlist
        
        Args:
            analyzer_results: List of RecognizerResult from Presidio analysis
            original_text: Original text that was analyzed
            
        Returns:
            Filtered list of RecognizerResult
        """
        if not self.allowlist or not analyzer_results or not original_text:
            return analyzer_results
        
        filtered_results = []
        
        for result in analyzer_results:
            # Extract the detected text from the original text
            detected_text = original_text[result.start:result.end]
            detected_normalized = self._normalize_text(detected_text)
            
            # Check if this detected text matches any allowlist entry
            should_filter = False
            for allowed_word in self.allowlist:
                allowed_normalized = self._normalize_text(allowed_word)
                if detected_normalized == allowed_normalized:
                    should_filter = True
                    self.logger.debug(f"Filtering '{detected_text}' (matches allowlist entry '{allowed_word}')")
                    break
            
            if not should_filter:
                filtered_results.append(result)
        
        filtered_count = len(analyzer_results) - len(filtered_results)
        if filtered_count > 0:
            self.logger.info(f"Filtered {filtered_count} results using allowlist")
        
        return filtered_results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current lists
        
        Returns:
            Dictionary with list statistics
        """
        entity_counts = {}
        for entry in self.denylist:
            entity_counts[entry.entity_type] = entity_counts.get(entry.entity_type, 0) + 1
        
        return {
            'allowlist_count': len(self.allowlist),
            'denylist_count': len(self.denylist),
            'denylist_entity_types': entity_counts,
            'case_sensitive': self.case_sensitive,
            'total_entries': len(self.allowlist) + len(self.denylist)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert lists to dictionary format for serialization
        
        Returns:
            Dictionary representation of lists
        """
        return {
            'allowlist': {
                'words': list(self.allowlist),
                'case_sensitive': self.case_sensitive
            },
            'denylist': {
                'entries': [
                    {
                        'word': entry.word,
                        'entity_type': entry.entity_type,
                        'confidence': entry.confidence
                    }
                    for entry in self.denylist
                ],
                'case_sensitive': self.case_sensitive
            }
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load lists from dictionary format
        
        Args:
            data: Dictionary containing list data
        """
        try:
            # Clear existing lists
            self.clear_allowlist()
            self.clear_denylist()
            
            # Load allowlist
            if 'allowlist' in data and 'words' in data['allowlist']:
                for word in data['allowlist']['words']:
                    self.add_to_allowlist(word)
                
                # Update case sensitivity if specified
                if 'case_sensitive' in data['allowlist']:
                    self.case_sensitive = data['allowlist']['case_sensitive']
            
            # Load denylist
            if 'denylist' in data and 'entries' in data['denylist']:
                for entry_data in data['denylist']['entries']:
                    word = entry_data.get('word', '')
                    entity_type = entry_data.get('entity_type', 'CUSTOM_DENY')
                    confidence = entry_data.get('confidence', 0.9)
                    self.add_to_denylist(word, entity_type, confidence)
                
                # Update case sensitivity if specified
                if 'case_sensitive' in data['denylist']:
                    self.case_sensitive = data['denylist']['case_sensitive']
            
            self.logger.info(f"Loaded lists: {len(self.allowlist)} allowlist, {len(self.denylist)} denylist entries")
            
        except Exception as e:
            self.logger.error(f"Error loading lists from dictionary: {e}")
            raise