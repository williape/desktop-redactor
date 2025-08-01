from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json

@dataclass
class Finding:
    """Data model for a PII finding"""
    entity_type: str
    text: str
    start: int
    end: int
    confidence: float
    recognizer: str
    pattern_name: Optional[str] = None
    pattern: Optional[str] = None
    # Decision process fields
    original_score: Optional[float] = None
    score: Optional[float] = None
    textual_explanation: Optional[str] = None
    score_context_improvement: Optional[float] = None
    supportive_context_word: Optional[str] = None
    validation_result: Optional[bool] = None
    regex_flags: Optional[str] = None
    decision_process: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            'entity_type': self.entity_type,
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'confidence': self.confidence,
            'recognizer': self.recognizer,
            'pattern_name': self.pattern_name,
            'pattern': self.pattern,
            'original_score': self.original_score,
            'score': self.score,
            'textual_explanation': self.textual_explanation,
            'score_context_improvement': self.score_context_improvement,
            'supportive_context_word': self.supportive_context_word,
            'validation_result': self.validation_result,
            'regex_flags': self.regex_flags,
            'decision_process': self.decision_process
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        """Create finding from dictionary"""
        return cls(
            entity_type=data.get('entity_type', ''),
            text=data.get('text', ''),
            start=int(data.get('start', 0)),
            end=int(data.get('end', 0)),
            confidence=float(data.get('confidence', 0.0)),
            recognizer=data.get('recognizer', ''),
            pattern_name=data.get('pattern_name'),
            pattern=data.get('pattern'),
            original_score=data.get('original_score'),
            score=data.get('score'),
            textual_explanation=data.get('textual_explanation'),
            score_context_improvement=data.get('score_context_improvement'),
            supportive_context_word=data.get('supportive_context_word'),
            validation_result=data.get('validation_result'),
            regex_flags=data.get('regex_flags'),
            decision_process=data.get('decision_process')
        )
    
    @classmethod
    def from_presidio_result(cls, result, recognizer_name: str = '') -> 'Finding':
        """Create finding from Presidio analyzer result"""
        return cls(
            entity_type=result.entity_type,
            text=result.text if hasattr(result, 'text') else '',
            start=result.start,
            end=result.end,
            confidence=result.score,
            recognizer=recognizer_name or (result.analysis_explanation.recognizer if hasattr(result, 'analysis_explanation') else ''),
            pattern_name=result.analysis_explanation.pattern_name if hasattr(result, 'analysis_explanation') and hasattr(result.analysis_explanation, 'pattern_name') else None,
            pattern=result.analysis_explanation.pattern if hasattr(result, 'analysis_explanation') and hasattr(result.analysis_explanation, 'pattern') else None
        )

@dataclass
class FindingsCollection:
    """Collection of findings with management methods"""
    findings: List[Finding] = field(default_factory=list)
    
    def add_finding(self, finding: Finding):
        """Add a finding to the collection"""
        self.findings.append(finding)
        
    def add_findings(self, findings: List[Finding]):
        """Add multiple findings to the collection"""
        self.findings.extend(findings)
        
    def clear(self):
        """Clear all findings"""
        self.findings.clear()
        
    def filter_by_confidence(self, min_confidence: float) -> List[Finding]:
        """Filter findings by minimum confidence threshold"""
        return [f for f in self.findings if f.confidence >= min_confidence]
        
    def filter_by_entity_types(self, entity_types: List[str]) -> List[Finding]:
        """Filter findings by entity types"""
        return [f for f in self.findings if f.entity_type in entity_types]
        
    def filter_by_text(self, search_term: str) -> List[Finding]:
        """Filter findings by text content"""
        search_term = search_term.lower()
        return [f for f in self.findings if search_term in f.text.lower()]
        
    def sort_by_confidence(self, descending: bool = True) -> List[Finding]:
        """Sort findings by confidence"""
        return sorted(self.findings, key=lambda f: f.confidence, reverse=descending)
        
    def sort_by_position(self) -> List[Finding]:
        """Sort findings by position in text"""
        return sorted(self.findings, key=lambda f: f.start)
        
    def sort_by_entity_type(self) -> List[Finding]:
        """Sort findings by entity type"""
        return sorted(self.findings, key=lambda f: f.entity_type)
        
    def get_entity_counts(self) -> Dict[str, int]:
        """Get count of findings by entity type"""
        counts = {}
        for finding in self.findings:
            counts[finding.entity_type] = counts.get(finding.entity_type, 0) + 1
        return counts
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the findings"""
        if not self.findings:
            return {
                'total_count': 0,
                'entity_counts': {},
                'average_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'recognizer_counts': {}
            }
            
        confidences = [f.confidence for f in self.findings]
        entity_counts = self.get_entity_counts()
        
        # Count by recognizer
        recognizer_counts = {}
        for finding in self.findings:
            recognizer_counts[finding.recognizer] = recognizer_counts.get(finding.recognizer, 0) + 1
            
        return {
            'total_count': len(self.findings),
            'entity_counts': entity_counts,
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'recognizer_counts': recognizer_counts
        }
        
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all findings to list of dictionaries"""
        return [finding.to_dict() for finding in self.findings]
        
    def to_json(self, indent: int = 2) -> str:
        """Export findings to JSON string"""
        return json.dumps(self.to_list(), indent=indent)
        
    def export_to_csv(self) -> str:
        """Export findings to CSV format"""
        if not self.findings:
            return ""
            
        headers = [
            'Entity Type', 'Text', 'Start', 'End', 'Confidence', 
            'Recognizer', 'Pattern Name', 'Pattern'
        ]
        
        lines = [','.join(headers)]
        
        for finding in self.findings:
            row = [
                finding.entity_type,
                f'"{finding.text}"',  # Quote text to handle commas
                str(finding.start),
                str(finding.end),
                f"{finding.confidence:.3f}",
                finding.recognizer,
                finding.pattern_name or '',
                finding.pattern or ''
            ]
            lines.append(','.join(row))
            
        return '\n'.join(lines)
        
    @classmethod
    def from_presidio_results(cls, results, text: str = '') -> 'FindingsCollection':
        """Create findings collection from Presidio analyzer results"""
        collection = cls()
        
        for result in results:
            # Extract text if available
            finding_text = text[result.start:result.end] if text else ''
            
            # Create finding with extracted text
            finding = Finding.from_presidio_result(result)
            if finding_text:
                finding.text = finding_text
                
            collection.add_finding(finding)
            
        return collection
        
    def get_findings_in_range(self, start: int, end: int) -> List[Finding]:
        """Get findings within a specific text range"""
        return [f for f in self.findings if f.start >= start and f.end <= end]
        
    def has_overlapping_findings(self) -> bool:
        """Check if there are any overlapping findings"""
        sorted_findings = self.sort_by_position()
        for i in range(len(sorted_findings) - 1):
            current = sorted_findings[i]
            next_finding = sorted_findings[i + 1]
            if current.end > next_finding.start:
                return True
        return False
        
    def remove_overlapping_findings(self, keep_highest_confidence: bool = True):
        """Remove overlapping findings, keeping highest confidence by default"""
        if not self.has_overlapping_findings():
            return
            
        sorted_findings = self.sort_by_position()
        filtered_findings = []
        
        i = 0
        while i < len(sorted_findings):
            current = sorted_findings[i]
            overlapping = [current]
            
            # Find all overlapping findings
            j = i + 1
            while j < len(sorted_findings) and sorted_findings[j].start < current.end:
                overlapping.append(sorted_findings[j])
                j += 1
                
            # Keep the best finding from overlapping group
            if keep_highest_confidence:
                best_finding = max(overlapping, key=lambda f: f.confidence)
            else:
                best_finding = overlapping[0]  # Keep first one
                
            filtered_findings.append(best_finding)
            i = j
            
        self.findings = filtered_findings