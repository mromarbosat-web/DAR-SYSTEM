import re

# Arabic presentation forms B mapping: (isolated, end/final, start/initial, middle/medial)
ARABIC_GLYPHS = {
    '\u0621': ('\ufe80', '\ufe80', '\ufe80', '\ufe80'), # Hamza
    '\u0622': ('\ufe81', '\ufe82', '\ufe81', '\ufe82'), # Alef with Madda
    '\u0623': ('\ufe83', '\ufe84', '\ufe83', '\ufe84'), # Alef with Hamza Above
    '\u0624': ('\ufe85', '\ufe86', '\ufe85', '\ufe86'), # Waw with Hamza Above
    '\u0625': ('\ufe87', '\ufe88', '\ufe87', '\ufe88'), # Alef with Hamza Below
    '\u0626': ('\ufe89', '\ufe8a', '\ufe8b', '\ufe8c'), # Yeh with Hamza Above
    '\u0627': ('\ufe8d', '\ufe8e', '\ufe8d', '\ufe8e'), # Alef
    '\u0628': ('\ufe8f', '\ufe90', '\ufe91', '\ufe92'), # Beh
    '\u0629': ('\ufe93', '\ufe94', '\ufe93', '\ufe94'), # Teh Marbuta
    '\u062a': ('\ufe95', '\ufe96', '\ufe97', '\ufe98'), # Teh
    '\u062b': ('\ufe99', '\ufe9a', '\ufe9b', '\ufe9c'), # Theh
    '\u062c': ('\ufe9d', '\ufe9e', '\ufe9f', '\ufea0'), # Jeem
    '\u062d': ('\ufea1', '\ufea2', '\ufea3', '\ufea4'), # Hah
    '\u062e': ('\ufea5', '\ufea6', '\ufea7', '\ufea8'), # Khah
    '\u062f': ('\ufea9', '\ufeaa', '\ufea9', '\ufeaa'), # Dal
    '\u0630': ('\ufeab', '\ufeac', '\ufeab', '\ufeac'), # Thal
    '\u0631': ('\ufead', '\ufeae', '\ufead', '\ufeae'), # Reh
    '\u0632': ('\ufeaf', '\ufeb0', '\ufeaf', '\ufeb0'), # Zain
    '\u0633': ('\ufeb1', '\ufeb2', '\ufeb3', '\ufeb4'), # Seen
    '\u0634': ('\ufeb5', '\ufeb6', '\ufeb7', '\ufeb8'), # Sheen
    '\u0635': ('\ufeb9', '\ufeba', '\ufebb', '\ufebc'), # Sad
    '\u0636': ('\ufebd', '\ufebe', '\ufebf', '\ufec0'), # Dad
    '\u0637': ('\ufec1', '\ufec2', '\ufec3', '\ufec4'), # Tah
    '\u0638': ('\ufec5', '\ufec6', '\ufec7', '\ufec8'), # Zah
    '\u0639': ('\ufec9', '\ufeca', '\ufecb', '\ufecc'), # Ain
    '\u063a': ('\ufecd', '\ufece', '\ufecf', '\ufed0'), # Ghain
    '\u0641': ('\ufed1', '\ufed2', '\ufed3', '\ufed4'), # Feh
    '\u0642': ('\ufed5', '\ufed6', '\ufed7', '\ufed8'), # Qaf
    '\u0643': ('\ufed9', '\ufeda', '\ufedb', '\ufedc'), # Kaf
    '\u0644': ('\ufedd', '\ufede', '\ufedf', '\ufee0'), # Lam
    '\u0645': ('\ufee1', '\ufee2', '\ufee3', '\ufee4'), # Meem
    '\u0646': ('\ufee5', '\ufee6', '\ufee7', '\ufee8'), # Noon
    '\u0647': ('\ufee9', '\ufeea', '\ufeeb', '\ufeec'), # Heh
    '\u0648': ('\ufeed', '\ufeee', '\ufeed', '\ufeee'), # Waw
    '\u0649': ('\ufeef', '\ufef0', '\ufeef', '\ufef0'), # Alef Maksura
    '\u064a': ('\ufef1', '\ufef2', '\ufef3', '\ufef4'), # Yeh
    '\u0671': ('\ufb50', '\ufb51', '\ufb50', '\ufb51'), # Wasla
    '\u067e': ('\ufb56', '\ufb57', '\ufb58', '\ufb59'), # Peh
    '\u0686': ('\ufb7a', '\ufb7b', '\ufb7c', '\ufb7d'), # Tcheh
    '\u0698': ('\ufb8a', '\ufb8b', '\ufb8a', '\ufb8b'), # Jeh
    '\u06af': ('\ufb92', '\ufb93', '\ufb94', '\ufb95'), # Gaf
    '\u06cc': ('\ufef1', '\ufef2', '\ufef3', '\ufef4'), # Farsi Yeh
}

# Characters that do NOT connect to the next character (Left disconnectors)
NON_CONNECTING_AFTER = {
    '\u0621', '\u0622', '\u0623', '\u0624', '\u0625', '\u0627',
    '\u062f', '\u0630', '\u0631', '\u0632', '\u0648', '\u0649',
    '\u0671', '\u0698', '\ufe80', '\ufe81', '\ufe82', '\ufe83',
    '\ufe84', '\ufe85', '\ufe86', '\ufe87', '\ufe88', '\ufe8d',
    '\ufe8e', '\ufea9', '\ufeaa', '\ufeab', '\ufeac', '\ufead',
    '\ufeae', '\ufeaf', '\ufeb0', '\ufeed', '\ufeee'
}

# Lam-Alef ligatures: (Lam + Alef variant) -> (isolated, final)
LAM_ALEF_LIGATURES = {
    ('\u0644', '\u0622'): ('\ufef5', '\ufef6'), # Madda
    ('\u0644', '\u0623'): ('\ufef7', '\ufef8'), # Hamza above
    ('\u0644', '\u0625'): ('\ufef9', '\ufefa'), # Hamza below
    ('\u0644', '\u0627'): ('\ufefb', '\ufefc'), # Plain Alef
}

def is_arabic_char(ch: str) -> bool:
    code = ord(ch)
    return (0x0600 <= code <= 0x06FF) or (0x0750 <= code <= 0x077F) or (0xFB50 <= code <= 0xFDFF) or (0xFE70 <= code <= 0xFEFF)

def reshape_arabic_word(word: str) -> str:
    """Reshapes an Arabic word by replacing glyphs with contextual forms (initial, medial, final, isolated)."""
    if not word:
        return ""
    
    # First replace Lam-Alef combinations
    chars = list(word)
    i = 0
    merged = []
    while i < len(chars):
        if i < len(chars) - 1 and (chars[i], chars[i+1]) in LAM_ALEF_LIGATURES:
            prev_connects = (i > 0 and chars[i-1] in ARABIC_GLYPHS and chars[i-1] not in NON_CONNECTING_AFTER)
            lig = LAM_ALEF_LIGATURES[(chars[i], chars[i+1])]
            merged.append(lig[1] if prev_connects else lig[0])
            i += 2
        else:
            merged.append(chars[i])
            i += 1
            
    result = []
    n = len(merged)
    for idx, ch in enumerate(merged):
        if ch not in ARABIC_GLYPHS:
            result.append(ch)
            continue
            
        forms = ARABIC_GLYPHS[ch]
        
        # Check if connected to previous character
        prev_connected = False
        if idx > 0:
            prev_ch = merged[idx - 1]
            if (prev_ch in ARABIC_GLYPHS or prev_ch in NON_CONNECTING_AFTER) and prev_ch not in NON_CONNECTING_AFTER:
                prev_connected = True
                
        # Check if connects to next character
        next_connected = False
        if idx < n - 1 and ch not in NON_CONNECTING_AFTER:
            next_ch = merged[idx + 1]
            if next_ch in ARABIC_GLYPHS:
                next_connected = True
                
        if prev_connected and next_connected:
            result.append(forms[3]) # Medial
        elif prev_connected:
            result.append(forms[1]) # Final
        elif next_connected:
            result.append(forms[2]) # Initial
        else:
            result.append(forms[0]) # Isolated
            
    return "".join(result)

def process_bidi_text(text: str) -> str:
    """
    Properly handles bidirectional mixed Arabic-English text for PIL rendering.
    Splits text into words/tokens, reshapes Arabic words, and reverses RTL sequences.
    """
    if not text:
        return ""
        
    # Check if string has any Arabic characters
    has_arabic = any(is_arabic_char(c) for c in text)
    if not has_arabic:
        return text
        
    tokens = re.split(r'(\s+|[^\w\s]+)', text)
    reshaped_tokens = []
    for token in tokens:
        if any(is_arabic_char(c) for c in token):
            reshaped_word = reshape_arabic_word(token)
            # Reverse Arabic characters for RTL display
            reshaped_tokens.append(reshaped_word[::-1])
        else:
            reshaped_tokens.append(token)
            
    # Reverse overall token flow for mostly Arabic lines
    reshaped_tokens.reverse()
    return "".join(reshaped_tokens)
