"""
Telugu and Indian language transliteration support
Converts script-based input to romanized/English equivalent
"""

# Telugu to English transliteration mapping
TELUGU_TO_ENGLISH = {
    # Vowels
    'అ': 'a',
    'ఆ': 'aa',
    'ఇ': 'i',
    'ఈ': 'ii',
    'ఉ': 'u',
    'ఊ': 'uu',
    'ఋ': 'ri',
    'ౠ': 'rii',
    'ఌ': 'li',
    'ౡ': 'lii',
    'ఎ': 'e',
    'ఏ': 'ee',
    'ఐ': 'ai',
    'ఒ': 'o',
    'ఓ': 'oo',
    'ఔ': 'ou',
    
    # Consonants
    'క': 'ka',
    'ఖ': 'kha',
    'గ': 'ga',
    'ఘ': 'gha',
    'ఙ': 'nga',
    'చ': 'cha',
    'ఛ': 'chha',
    'జ': 'ja',
    'ఝ': 'jha',
    'ఞ': 'nja',
    'ట': 'ta',
    'ఠ': 'tha',
    'డ': 'da',
    'ఢ': 'dha',
    'ణ': 'na',
    'త': 'tha',
    'థ': 'tha',
    'ద': 'da',
    'ధ': 'dha',
    'న': 'na',
    'ప': 'pa',
    'ఫ': 'pha',
    'బ': 'ba',
    'భ': 'bha',
    'మ': 'ma',
    'య': 'ya',
    'ర': 'ra',
    'ల': 'la',
    'వ': 'va',
    'శ': 'sha',
    'ష': 'sha',
    'స': 'sa',
    'హ': 'ha',
    'ళ': 'la',
    'క్ష': 'ksha',
    
    # Vowel diacritics (matras)
    'ా': 'aa',
    'ి': 'i',
    'ీ': 'ii',
    'ు': 'u',
    'ూ': 'uu',
    'ృ': 'ri',
    'ౄ': 'rii',
    'ෙ': 'e',
    'ೆ': 'e',
    'ేے': 'ee',
    'ై': 'ai',
    'ో': 'o',
    'ౌ': 'ou',
    
    # Special characters
    '్': '',  # Halant (virama)
    'ం': 'm',  # Anusvara
    'ඃ': 'h',  # Visarga
    'ः': 'h',
    '।': '.',  # Danda
    '॥': '.',  # Double danda
    '०': '0',
    '१': '1',
    '२': '2',
    '३': '3',
    '४': '4',
    '५': '5',
    '६': '6',
    '७': '7',
    '८': '8',
    '९': '9',
    
    # Additional Telugu specific
    'ఱ': 'rra',
    'ౠ': 'ru',
    'ౢ': 'lu',
    'ఀ': 'om',
    'ఁ': 'candrabindu',
}

# Hindi to English (additional support)
HINDI_TO_ENGLISH = {
    # Hindi consonants
    'क': 'ka',
    'ख': 'kha',
    'ग': 'ga',
    'घ': 'gha',
    'ङ': 'nga',
    'च': 'cha',
    'छ': 'chha',
    'ज': 'ja',
    'झ': 'jha',
    'ञ': 'nja',
    'ट': 'ta',
    'ठ': 'tha',
    'ड': 'da',
    'ढ': 'dha',
    'ण': 'na',
    'त': 'ta',
    'थ': 'tha',
    'द': 'da',
    'ध': 'dha',
    'न': 'na',
    'प': 'pa',
    'फ': 'pha',
    'ब': 'ba',
    'भ': 'bha',
    'म': 'ma',
    'य': 'ya',
    'र': 'ra',
    'ल': 'la',
    'व': 'va',
    'श': 'sha',
    'ष': 'sha',
    'स': 'sa',
    'ह': 'ha',
    'क्ष': 'ksha',
    'ज्ञ': 'gya',
    
    # Hindi vowels
    'अ': 'a',
    'आ': 'aa',
    'इ': 'i',
    'ई': 'ii',
    'उ': 'u',
    'ऊ': 'uu',
    'ऋ': 'ri',
    'ए': 'e',
    'ऐ': 'ai',
    'ओ': 'o',
    'औ': 'ou',
}


def transliterate_telugu_to_english(text):
    """
    Convert Telugu script text to English/romanized form.
    Also handles mixed script input.
    
    Args:
        text: String potentially containing Telugu characters
    
    Returns:
        Transliterated English string
    """
    if not text:
        return text
    
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        
        # Check for two-character sequences first (like క్ష)
        if i + 1 < len(text):
            two_char = char + text[i + 1]
            if two_char in TELUGU_TO_ENGLISH:
                result.append(TELUGU_TO_ENGLISH[two_char])
                i += 2
                continue
        
        # Single character transliteration
        if char in TELUGU_TO_ENGLISH:
            result.append(TELUGU_TO_ENGLISH[char])
        elif char in HINDI_TO_ENGLISH:
            result.append(HINDI_TO_ENGLISH[char])
        elif char.isascii():
            # Keep ASCII characters as-is
            result.append(char)
        else:
            # Keep unknown characters as-is
            result.append(char)
        
        i += 1
    
    # Clean up the result
    transliterated = ''.join(result)
    
    # Remove extra spaces and clean up
    transliterated = ' '.join(transliterated.split())
    
    return transliterated


def detect_script(text):
    """
    Detect if text contains Telugu, Hindi, or other Indic script characters.
    
    Args:
        text: String to analyze
    
    Returns:
        Script type: 'telugu', 'hindi', 'mixed', or 'english'
    """
    if not text:
        return 'english'
    
    has_telugu = any(char in TELUGU_TO_ENGLISH for char in text)
    has_hindi = any(char in HINDI_TO_ENGLISH for char in text)
    has_ascii = any(char.isascii() for char in text)
    
    if has_telugu and not has_hindi:
        return 'telugu'
    elif has_hindi and not has_telugu:
        return 'hindi'
    elif has_telugu or has_hindi:
        return 'mixed'
    else:
        return 'english'


def process_query(query):
    """
    Process a search query, transliterating if needed.
    If query contains Indic script, converts to English.
    Otherwise returns as-is.
    
    Args:
        query: User search query (may contain Telugu, Hindi, or English)
    
    Returns:
        Tuple of (processed_query, original_query, script_type)
    """
    if not query:
        return query, query, 'english'
    
    script_type = detect_script(query)
    
    if script_type == 'english':
        return query, query, script_type
    elif script_type == 'telugu':
        transliterated = transliterate_telugu_to_english(query)
        return transliterated, query, script_type
    elif script_type == 'hindi':
        transliterated = transliterate_telugu_to_english(query)
        return transliterated, query, script_type
    else:  # mixed
        transliterated = transliterate_telugu_to_english(query)
        return transliterated, query, script_type
