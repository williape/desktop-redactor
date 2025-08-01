from typing import List, Optional
import re

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

from presidio_analyzer import (
    AnalysisExplanation,
    EntityRecognizer,
    LocalRecognizer,
    RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpArtifacts


class EnhancedPhoneRecognizer(LocalRecognizer):
    """Enhanced phone recognizer with Australian support.

    Using python-phonenumbers, along with fixed and regional context words.
    Extends the default PhoneRecognizer to include Australian phone numbers.
    
    :param context: Base context words for enhancing the assurance scores.
    :param supported_language: Language this recognizer supports
    :param supported_regions: The regions for phone number matching and validation
    :param leniency: The strictness level of phone number formats.
    Accepts values from 0 to 3, where 0 is the lenient and 3 is the most strictest.
    """

    SCORE = 0.7
    CONTEXT = ["phone", "number", "telephone", "cell", "cellphone", "mobile", "call"]
    # Enhanced to include Australian region
    DEFAULT_SUPPORTED_REGIONS = ("US", "UK", "DE", "FE", "IL", "IN", "CA", "BR", "AU")

    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        # For all regions, use phonenumbers.SUPPORTED_REGIONS
        supported_regions=DEFAULT_SUPPORTED_REGIONS,
        leniency: Optional[int] = 1,
    ):
        context = context if context else self.CONTEXT
        self.supported_regions = supported_regions
        self.leniency = leniency
        super().__init__(
            supported_entities=self.get_supported_entities(),
            supported_language=supported_language,
            context=context,
        )

    def load(self) -> None:  # noqa D102
        pass

    def get_supported_entities(self):  # noqa D102
        return ["PHONE_NUMBER"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect phone numbers using python-phonenumbers.

        Iterates over entities, fetching regions, then matching regional
        phone numbers patterns against the text.
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of phone numbers RecognizerResults
        """
        results = []
        for region in self.supported_regions:
            for match in phonenumbers.PhoneNumberMatcher(
                text, region, leniency=self.leniency
            ):
                try:
                    parsed_number = phonenumbers.parse(text[match.start:match.end])
                    region_code = phonenumbers.region_code_for_number(parsed_number)
                    results += [
                        self._get_recognizer_result(match, text, region_code, nlp_artifacts)
                    ]
                except NumberParseException:
                    results += [
                        self._get_recognizer_result(match, text, region, nlp_artifacts)
                    ]

        return EntityRecognizer.remove_duplicates(results)

    def _get_recognizer_result(self, match, text, region, nlp_artifacts):
        result = RecognizerResult(
            entity_type="PHONE_NUMBER",
            start=match.start,
            end=match.end,
            score=self.SCORE,
            analysis_explanation=self._get_analysis_explanation(region),
            recognition_metadata={
                RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
            },
        )

        return result

    def _get_analysis_explanation(self, region):
        return AnalysisExplanation(
            recognizer=EnhancedPhoneRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation=f"Recognized as {region} region phone number, "
            f"using EnhancedPhoneRecognizer",
        )

class AuMedicareProviderRecognizer(LocalRecognizer):
    """Australian Medicare Provider Number recognizer.
    
    Detects and validates Australian Medicare Provider Numbers according to the format:
    - 6-digit Provider Stem
    - 1 Practice Location Character (0-9, A-F, G-H, J-Y excluding I, O, S, Z)
    - 1 Check Digit (Y, X, W, T, L, K, J, H, F, B, A)
    
    Includes validation using the Medicare Provider check digit algorithm.
    """
    
    SCORE = 0.9
    CONTEXT = ["provider", "medicare", "number", "practitioner", "doctor", "GP", "medical"]
    
    # Practice Location Characters - all valid characters except I, O, S, Z
    PRACTICE_LOCATION_CHARS = set("0123456789ABCDEFGHJKLMNPQRTUVWXY")
    
    # Check digits mapping remainder to check digit
    CHECK_DIGITS = {0: 'Y', 1: 'X', 2: 'W', 3: 'T', 4: 'L', 5: 'K', 
                   6: 'J', 7: 'H', 8: 'F', 9: 'B', 10: 'A'}
    
    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entities=["AU_MEDICAREPROVIDER"],
            supported_language=supported_language,
            context=context,
        )
        
        # Regex pattern: 6 digits + 1 alphanumeric + 1 alpha
        self.pattern = re.compile(r'\b\d{6}[0-9A-Z][A-Z]\b', re.IGNORECASE)

    def load(self) -> None:
        pass

    def get_supported_entities(self):
        return ["AU_MEDICAREPROVIDER"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect Australian Medicare Provider Numbers.
        
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of Medicare Provider Number RecognizerResults
        """
        results = []
        
        if "AU_MEDICAREPROVIDER" not in entities:
            return results
            
        for match in self.pattern.finditer(text):
            provider_number = match.group().upper()
            
            if self._is_valid_provider_number(provider_number):
                result = RecognizerResult(
                    entity_type="AU_MEDICAREPROVIDER",
                    start=match.start(),
                    end=match.end(),
                    score=self.SCORE,
                    analysis_explanation=self._get_analysis_explanation(),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                    },
                )
                results.append(result)
        
        return results

    def _is_valid_provider_number(self, provider_number: str) -> bool:
        """Validates Australian Medicare Provider Number format and check digit.
        
        :param provider_number: The provider number to validate (8 characters)
        :return: True if valid, False otherwise
        """
        if len(provider_number) != 8:
            return False
            
        # Extract components
        provider_stem = provider_number[:6]
        practice_location_char = provider_number[6]
        check_digit = provider_number[7]
        
        # Validate provider stem is all digits
        if not provider_stem.isdigit():
            return False
            
        # Validate practice location character
        if practice_location_char not in self.PRACTICE_LOCATION_CHARS:
            return False
            
        # Validate check digit using the algorithm
        calculated_check_digit = self._calculate_check_digit(provider_stem, practice_location_char)
        
        return calculated_check_digit == check_digit

    def _calculate_check_digit(self, provider_stem: str, practice_location_char: str) -> str:
        """Calculates the check digit for a Medicare Provider Number.
        
        Algorithm:
        • (digit 1 * 3) +
        • (digit 2 * 5) +
        • (digit 3 * 8) +
        • (digit 4 * 4) +
        • (digit 5 * 2) +
        • (digit 6) +
        • (PLV * 6)
        • Divide the result by 11
        The remainder maps to check digit: Y X W T L K J H F B A
        
        :param provider_stem: 6-digit provider stem
        :param practice_location_char: Practice location character
        :return: Calculated check digit
        """
        # Convert practice location character to numeric value
        if practice_location_char.isdigit():
            plv = int(practice_location_char)
        else:
            # Map A-Z to 10-35, excluding I(18), O(24), S(28), Z(35)
            # Create mapping for valid characters
            char_to_num = {}
            num = 10
            for char in "ABCDEFGHJKLMNPQRTUVWXY":
                char_to_num[char] = num
                num += 1
            plv = char_to_num.get(practice_location_char, 0)
        
        # Calculate weighted sum
        digits = [int(d) for d in provider_stem]
        total = (
            digits[0] * 3 +
            digits[1] * 5 +
            digits[2] * 8 +
            digits[3] * 4 +
            digits[4] * 2 +
            digits[5] * 1 +
            plv * 6
        )
        
        # Get remainder when divided by 11
        remainder = total % 11
        
        # Return corresponding check digit
        return self.CHECK_DIGITS.get(remainder, '')

    def _get_analysis_explanation(self):
        """Returns analysis explanation for Medicare Provider Number detection."""
        return AnalysisExplanation(
            recognizer=AuMedicareProviderRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation="Detected as Australian Medicare Provider Number with valid format and check digit",
        )

class AuDvaRecognizer(LocalRecognizer):
    """Australian DVA File Number recognizer.
    
    Detects and validates Australian DVA (Department of Veterans' Affairs) File Numbers.
    
    Format specifications:
    - Minimum 3, maximum 9 characters total
    - First character: State code (N, V, Q, W, S, or T)
    - Following characters: War code (1-3 alpha chars or space) + numeric digits
    - Optional last character: Dependent code (alpha) for dependents of veterans
    
    Pattern rules:
    - 1st character: Must be alpha (state code)
    - 2nd character: May be alpha or space (war code start)
    - 3rd-8th characters: May be alpha or numeric
    - 9th character: If present, must be alpha (dependent code)
    
    Examples: W 1, NX5, NX5A, SCGW1234, SCGW1234B, N 026027K
    """
    
    SCORE = 0.9
    CONTEXT = ["dva", "veterans", "affairs", "file", "number", "veteran", "dependent"]
    
    # Valid state codes for Australian states and territories
    STATE_CODES = set("NVQWST")
    
    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entities=["AU_DVA"],
            supported_language=supported_language,
            context=context,
        )
        
        # Complex regex pattern to match DVA file number format
        # Pattern: [NVQWST][A-Z ]?[A-Z0-9]{1,6}[A-Z]?
        # With length constraints and validation logic in _is_valid_dva_number
        self.pattern = re.compile(r'\b[NVQWST][A-Z ]?[A-Z0-9]{1,6}[A-Z]?\b', re.IGNORECASE)

    def load(self) -> None:
        pass

    def get_supported_entities(self):
        return ["AU_DVA"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect Australian DVA File Numbers.
        
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of DVA File Number RecognizerResults
        """
        results = []
        
        if "AU_DVA" not in entities:
            return results
            
        for match in self.pattern.finditer(text):
            dva_number = match.group().upper()
            
            if self._is_valid_dva_number(dva_number):
                result = RecognizerResult(
                    entity_type="AU_DVA",
                    start=match.start(),
                    end=match.end(),
                    score=self.SCORE,
                    analysis_explanation=self._get_analysis_explanation(),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                    },
                )
                results.append(result)
        
        return results

    def _is_valid_dva_number(self, dva_number: str) -> bool:
        """Validates Australian DVA File Number format.
        
        :param dva_number: The DVA file number to validate (3-9 characters)
        :return: True if valid, False otherwise
        """
        # Length check: 3-9 characters
        if len(dva_number) < 3 or len(dva_number) > 9:
            return False
            
        # First character must be a valid state code
        if dva_number[0] not in self.STATE_CODES:
            return False
            
        # If 9 characters, last character must be alpha (dependent code)
        if len(dva_number) == 9 and not dva_number[8].isalpha():
            return False
            
        # Second character can be alpha or space
        if len(dva_number) > 1:
            second_char = dva_number[1]
            if not (second_char.isalpha() or second_char == ' '):
                return False
        
        # Must contain at least one numeric digit after the state code
        # to distinguish from random letter sequences
        numeric_found = False
        for i in range(1, len(dva_number)):
            if dva_number[i].isdigit():
                numeric_found = True
                break
                
        if not numeric_found:
            return False
            
        # Additional validation based on war code patterns
        return self._validate_war_code_pattern(dva_number)
    
    def _validate_war_code_pattern(self, dva_number: str) -> bool:
        """Validates the war code pattern within the DVA file number.
        
        War code rules:
        - 1 alpha char or space + up to 6 numeric chars
        - 2 alpha chars + up to 5 numeric chars  
        - 3 alpha chars + up to 4 numeric chars
        
        :param dva_number: The DVA file number to validate
        :return: True if war code pattern is valid, False otherwise
        """
        # Remove state code (first char) and optional dependent code (last char if alpha)
        work_string = dva_number[1:]  # Remove state code
        
        # Check if last character is dependent code (alpha)
        has_dependent = len(work_string) > 0 and work_string[-1].isalpha() and len(dva_number) > 3
        if has_dependent:
            # Remove dependent code for pattern analysis
            # But only if there are digits before it
            digits_before_last = any(c.isdigit() for c in work_string[:-1])
            if digits_before_last:
                work_string = work_string[:-1]
        
        if len(work_string) == 0:
            return False
            
        # Count leading alpha characters (war code)
        alpha_count = 0
        for char in work_string:
            if char.isalpha():
                alpha_count += 1
            elif char == ' ' and alpha_count == 0:
                # Space can be the first character of war code
                alpha_count = 1
                break
            else:
                break
                
        # Get remaining characters after war code
        remaining = work_string[alpha_count:]
        
        # Remaining characters should be numeric
        if not remaining.isdigit():
            return False
            
        numeric_count = len(remaining)
        
        # Validate based on war code length
        if alpha_count == 1:  # 1 alpha char or space
            return numeric_count >= 1 and numeric_count <= 6
        elif alpha_count == 2:  # 2 alpha chars
            return numeric_count >= 1 and numeric_count <= 5
        elif alpha_count == 3:  # 3 alpha chars
            return numeric_count >= 1 and numeric_count <= 4
        else:
            return False

    def _get_analysis_explanation(self):
        """Returns analysis explanation for DVA File Number detection."""
        return AnalysisExplanation(
            recognizer=AuDvaRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation="Detected as Australian DVA File Number with valid format",
        )

class AuCrnRecognizer(LocalRecognizer):
    """Australian Centrelink Customer Reference Number (CRN) recognizer.
    
    Detects and validates Australian CRNs according to the format:
    - State character code (2=NSW/ACT, 3=VIC, 4=QLD, 5=SA/NT, 6=WA, 7=TAS)
    - 8 numeric digits
    - Check digit (ABCHJKLSTVX)  
    - Optional dependant indicator (A-Z or space)
    
    Format: snnnnnnnncd where s=state, n=digits, c=check digit, d=dependant
    May include spaces or hyphens between groupings.
    
    Examples: 123 456 789A, 307111942H
    """
    
    SCORE = 0.9
    CONTEXT = ["crn", "centrelink", "customer", "reference", "number"]
    
    # Valid state codes
    STATE_CODES = set("234567")
    
    # Valid check digits
    CHECK_DIGITS = set("ABCHJKLSTVX")
    
    # Check digit mapping from remainder to character
    REMAINDER_TO_CHECK_DIGIT = {
        10: 'A', 9: 'B', 8: 'C', 7: 'H', 6: 'J', 5: 'K',
        4: 'L', 3: 'S', 2: 'T', 1: 'V', 0: 'X'
    }
    
    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entities=["AU_CRN"],
            supported_language=supported_language,
            context=context,
        )
        
        # Regex pattern to match CRN format with optional spaces/hyphens
        # [234567] - state code
        # [\s-]? - optional space or hyphen
        # \d{3} - first 3 digits
        # [\s-]? - optional space or hyphen  
        # \d{3} - next 3 digits
        # [\s-]? - optional space or hyphen
        # \d{3} - last 3 digits (total 8 digits after state)
        # [ABCHJKLSTVX] - check digit
        # [A-Z ]? - optional dependant indicator
        self.pattern = re.compile(
            r'\b[234567][\s-]?(?:\d{3}[\s-]?\d{3}[\s-]?\d{2}|\d{8})[ABCHJKLSTVX][A-Z ]?\b',
            re.IGNORECASE
        )

    def load(self) -> None:
        pass

    def get_supported_entities(self):
        return ["AU_CRN"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect Australian CRNs.
        
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of CRN RecognizerResults
        """
        results = []
        
        if "AU_CRN" not in entities:
            return results
            
        for match in self.pattern.finditer(text):
            crn = match.group().upper()
            
            if self._is_valid_crn(crn):
                result = RecognizerResult(
                    entity_type="AU_CRN",
                    start=match.start(),
                    end=match.end(),
                    score=self.SCORE,
                    analysis_explanation=self._get_analysis_explanation(),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                    },
                )
                results.append(result)
        
        return results

    def _is_valid_crn(self, crn: str) -> bool:
        """Validates Australian CRN format and check digit.
        
        :param crn: The CRN to validate
        :return: True if valid, False otherwise
        """
        # Clean the CRN by removing spaces and hyphens
        clean_crn = re.sub(r'[\s-]', '', crn)
        
        # Length should be 10-11 characters (state + 8 digits + check + optional dependant)
        if len(clean_crn) < 10 or len(clean_crn) > 11:
            return False
            
        # Extract components
        state_code = clean_crn[0]
        digits = clean_crn[1:9]  # 8 digits
        check_digit = clean_crn[9]
        dependant = clean_crn[10] if len(clean_crn) == 11 else None
        
        # Validate state code
        if state_code not in self.STATE_CODES:
            return False
            
        # Validate digits are numeric
        if not digits.isdigit():
            return False
            
        # Validate check digit
        if check_digit not in self.CHECK_DIGITS:
            return False
            
        # Validate dependant indicator if present
        if dependant and not (dependant.isalpha() or dependant == ' '):
            return False
            
        # Validate check digit using algorithm
        calculated_check_digit = self._calculate_check_digit(state_code + digits)
        
        return calculated_check_digit == check_digit

    def _calculate_check_digit(self, number_part: str) -> str:
        """Calculates the check digit for a CRN.
        
        Algorithm:
        - Use first 9 characters (state code + 8 digits)
        - Sum of (each digit * 2^(10-n)) where n is digit position (1-based)
        - Remainder when divided by 11 maps to check digit
        
        :param number_part: State code + 8 digits (9 characters total)
        :return: Calculated check digit
        """
        if len(number_part) != 9:
            return ''
            
        total = 0
        for i, digit_char in enumerate(number_part):
            if digit_char.isdigit():
                digit = int(digit_char)
                position = i + 1  # 1-based position
                weight = 2 ** (10 - position)
                total += digit * weight
        
        remainder = total % 11
        
        return self.REMAINDER_TO_CHECK_DIGIT.get(remainder, '')

    def _get_analysis_explanation(self):
        """Returns analysis explanation for CRN detection."""
        return AnalysisExplanation(
            recognizer=AuCrnRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation="Detected as Australian Centrelink Customer Reference Number with valid format and check digit",
        )

class AuPassportRecognizer(LocalRecognizer):
    """Australian Passport Number recognizer.
    
    Detects and validates Australian passport numbers according to the format:
    - One or two letters (A-Z, excluding O, S, Q, and I)
    - Exactly seven digits (0-9)
    
    Format: ^[A-Za-z]{1,2}[0-9]{7}$
    Examples: A1234567, PA1234567, PB1234567, N1234567, L5678901
    
    The letters used exclude O, S, Q, and I to avoid confusion with numbers.
    """
    
    SCORE = 0.9
    CONTEXT = ["passport", "number", "travel", "document", "identification", "ID"]
    
    # Valid passport letters - excluding O, S, Q, I
    VALID_LETTERS = set("ABCDEFGHJKLMNPRTUVWXYZ")
    
    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entities=["AU_PASSPORT"],
            supported_language=supported_language,
            context=context,
        )
        
        # Regex pattern: 1-2 letters + exactly 7 digits
        # Using word boundaries to ensure complete match
        self.pattern = re.compile(r'\b[A-Za-z]{1,2}\d{7}\b', re.IGNORECASE)

    def load(self) -> None:
        pass

    def get_supported_entities(self):
        return ["AU_PASSPORT"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect Australian passport numbers.
        
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of passport number RecognizerResults
        """
        results = []
        
        if "AU_PASSPORT" not in entities:
            return results
            
        for match in self.pattern.finditer(text):
            passport_number = match.group().upper()
            
            if self._is_valid_passport_number(passport_number):
                result = RecognizerResult(
                    entity_type="AU_PASSPORT",
                    start=match.start(),
                    end=match.end(),
                    score=self.SCORE,
                    analysis_explanation=self._get_analysis_explanation(),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        "pattern_name": "Australian Passport Format",
                        "pattern": r"^[A-Za-z]{1,2}[0-9]{7}$"
                    },
                )
                results.append(result)
        
        return results

    def _is_valid_passport_number(self, passport_number: str) -> bool:
        """Validates Australian passport number format.
        
        :param passport_number: The passport number to validate (8-9 characters)
        :return: True if valid, False otherwise
        """
        # Length check: 8-9 characters (1-2 letters + 7 digits)
        if len(passport_number) < 8 or len(passport_number) > 9:
            return False
            
        # Extract letter and digit parts
        if len(passport_number) == 8:
            letters = passport_number[:1]
            digits = passport_number[1:]
        else:  # len == 9
            letters = passport_number[:2]
            digits = passport_number[2:]
        
        # Validate letters are from valid set (excluding O, S, Q, I)
        for letter in letters:
            if letter not in self.VALID_LETTERS:
                return False
        
        # Validate exactly 7 digits
        if len(digits) != 7 or not digits.isdigit():
            return False
        
        return True

    def _get_analysis_explanation(self):
        """Returns analysis explanation for passport number detection."""
        return AnalysisExplanation(
            recognizer=AuPassportRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation="Detected as Australian passport number with valid format (1-2 letters + 7 digits, excluding O/S/Q/I)",
        )

class AuDriversLicenseRecognizer(LocalRecognizer):
    """Australian Driver's License Number recognizer.
    
    Detects and validates Australian driver's license numbers according to state-specific formats:
    - **Numeric formats**: 6-10 digits (with optional spaces/hyphens)
    - **Alphanumeric formats**: Various combinations of letters and digits
      - 1 letter + 5 digits (e.g., A12345)
      - 2 letters + 4 digits (e.g., AB1234)
      - 4 digits + 2 letters (e.g., 1234AB)
    
    State examples:
    - Victoria: 8-10 digits, sometimes formatted with spaces or hyphens
    - NSW: Typically 8 digits
    - Other states: Various alphanumeric combinations
    
    Examples: 12345678, 123 456 789, A12345, AB1234, 1234AB, 1-234-567-890
    """
    
    SCORE = 0.8  # Slightly lower than other recognizers due to format variations
    CONTEXT = ["license", "licence", "driving", "driver", "drivers", "dl", "permit"]
    
    def __init__(
        self,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
    ):
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entities=["AU_DRIVERSLICENSE"],
            supported_language=supported_language,
            context=context,
        )
        
        # Combined regex pattern to match various Australian driver's license formats
        # Pattern components:
        # 1. Alphanumeric: Letter(s) + digits or digits + letters (more specific first)
        # 2. Numeric with delimiters: specific patterns to avoid phone numbers
        # 3. Numeric: 6-10 digits without delimiters
        self.pattern = re.compile(
            r'\b(?:'
            r'[A-Z]\d{5}|'                                      # 1 letter + 5 digits
            r'[A-Z]{2}\d{4}|'                                   # 2 letters + 4 digits
            r'\d{4}[A-Z]{2}|'                                   # 4 digits + 2 letters
            r'\d{3}[\s-]\d{3}[\s-]\d{3}|'                      # 9 digits: 3-3-3 format
            r'\d{1}[\s-]\d{3}[\s-]\d{3}[\s-]\d{3}|'            # 10 digits: 1-3-3-3 format
            r'\d{6,10}'                                         # 6-10 digits no delimiters
            r')\b',
            re.IGNORECASE
        )

    def load(self) -> None:
        pass

    def get_supported_entities(self):
        return ["AU_DRIVERSLICENSE"]

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """Analyzes text to detect Australian driver's license numbers.
        
        :param text: Text to be analyzed
        :param entities: Entities this recognizer can detect
        :param nlp_artifacts: Additional metadata from the NLP engine
        :return: List of driver's license number RecognizerResults
        """
        results = []
        
        if "AU_DRIVERSLICENSE" not in entities:
            return results
            
        for match in self.pattern.finditer(text):
            license_number = match.group().upper()
            
            if self._is_valid_license_number(license_number):
                result = RecognizerResult(
                    entity_type="AU_DRIVERSLICENSE",
                    start=match.start(),
                    end=match.end(),
                    score=self.SCORE,
                    analysis_explanation=self._get_analysis_explanation(),
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        "pattern_name": "Australian Driver's License Format",
                        "pattern": r"^(?:\d{6,10}|[A-Z]{1,2}\d{4,5}|\d{4}[A-Z]{2})$"
                    },
                )
                results.append(result)
        
        return results

    def _is_valid_license_number(self, license_number: str) -> bool:
        """Validates Australian driver's license number format.
        
        :param license_number: The license number to validate
        :return: True if valid, False otherwise
        """
        # Remove spaces and hyphens for validation
        clean_number = re.sub(r'[\s-]', '', license_number)
        
        # Length check: must be between 6-10 characters total
        if len(clean_number) < 6 or len(clean_number) > 10:
            return False
        
        # Check different format patterns
        if self._is_numeric_format(clean_number):
            return True
        elif self._is_alphanumeric_format(clean_number):
            return True
        else:
            return False

    def _is_numeric_format(self, clean_number: str) -> bool:
        """Validates numeric driver's license formats (6-10 digits).
        
        :param clean_number: Cleaned license number without spaces/hyphens
        :return: True if valid numeric format, False otherwise
        """
        # Must be all digits and 6-10 characters
        if not clean_number.isdigit():
            return False
        
        length = len(clean_number)
        if length < 6 or length > 10:
            return False
        
        # For shorter numbers (6-7 digits), be more strict about patterns
        if length <= 7:
            # Reject if too uniform for shorter numbers
            if self._is_too_uniform(clean_number):
                return False
            # Also reject very simple patterns for short numbers
            if length == 6 and (clean_number == "123456" or clean_number == "654321"):
                return False
        else:
            # For longer numbers (8-10 digits), use normal uniform check
            if self._is_too_uniform(clean_number):
                return False
        
        return True

    def _is_alphanumeric_format(self, clean_number: str) -> bool:
        """Validates alphanumeric driver's license formats.
        
        :param clean_number: Cleaned license number without spaces/hyphens
        :return: True if valid alphanumeric format, False otherwise
        """
        length = len(clean_number)
        
        # Pattern: 1 letter + 5 digits
        if length == 6:
            if clean_number[0].isalpha() and clean_number[1:].isdigit():
                return True
        
        # Pattern: 2 letters + 4 digits
        if length == 6:
            if clean_number[:2].isalpha() and clean_number[2:].isdigit():
                return True
        
        # Pattern: 4 digits + 2 letters
        if length == 6:
            if clean_number[:4].isdigit() and clean_number[4:].isalpha():
                return True
        
        return False

    def _is_too_uniform(self, number: str) -> bool:
        """Checks if a number is too uniform to be a valid license number.
        
        :param number: The numeric string to check
        :return: True if too uniform, False otherwise
        """
        # Check for all same digits (e.g., 1111111, 0000000)
        if len(set(number)) == 1:
            return True
        
        # For shorter numbers (6-7 digits), be more strict about sequential patterns
        if len(number) <= 7:
            # Check for perfect ascending/descending sequences in short numbers
            if len(number) >= 6:
                ascending = all(int(number[i]) == int(number[i-1]) + 1 for i in range(1, len(number)))
                descending = all(int(number[i]) == int(number[i-1]) - 1 for i in range(1, len(number)))
                
                if ascending or descending:
                    return True
        
        # For longer numbers (8+ digits), only reject if there are very few unique digits
        # Allow some sequential patterns in longer numbers as they might be real
        if len(set(number)) <= 2 and len(number) >= 8:
            # Count occurrences of most common digit
            digit_counts = {}
            for digit in number:
                digit_counts[digit] = digit_counts.get(digit, 0) + 1
            max_count = max(digit_counts.values())
            # If one digit appears more than 80% of the time, it's probably too uniform
            if max_count / len(number) > 0.8:
                return True
        
        return False

    def _get_analysis_explanation(self):
        """Returns analysis explanation for driver's license number detection."""
        return AnalysisExplanation(
            recognizer=AuDriversLicenseRecognizer.__name__,
            original_score=self.SCORE,
            textual_explanation="Detected as Australian driver's license number with valid state-specific format",
        )