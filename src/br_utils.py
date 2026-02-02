import re


MODALS = [
    "adotarão",
    "cabe ",
    "caberá",
    "cabendo",
    "Compete à",
    "comunicará",
    "comunicarão",
    "deve",
    "devem ",
    "deverá",
    "deverão",
    "devendo",
    "definirá",
    "disciplinará",
    "disponibilizará",
    "disporá",
    "é obrigação do",
    "estabelecerá",
    "exercerá",
    "ficam sujeitos a",
    "fomentará",
    "implementará",
    "informarão",
    "inverterá o ônus da prova",
    "manterá",
    "observarão",
    "permanece sujeita a",
    "permanecem sujeitos a",
    "regulamentará",
    "regulamentarão",
    "São vedados",
    "será fornecida",
    "será fornecido",
    "serão públicas",
    "terá",
    "verificará"
]


CHAR_MATCH = {
    'á': 'a',
    'à': 'a',
    'ã': 'a',
    'â': 'a',
    'Á': 'A',
    'À': 'A',
    'Ã': 'A',
    'Â': 'A',

    'ç': 'c',
    'Ç': 'C',

    'é': 'e',
    'ê': 'e',
    'ẽ': 'e',
    'Ê': 'E',
    'Ẽ': 'E',
    'É': "E",
    'É': 'E',

    'í': 'i',
    'Í': 'I',

    'ó': 'o',
    'õ': 'o',
    'ô': 'o',
    'Ó': 'O',
    'Õ': 'O',
    'Ô': 'O',

    'ú': 'u',
    'ü': 'u',
    'Ú': 'U',
    'Ü': 'U',

    'º': 'o',
    '°': 'o',
    'ª': 'a',
    '§': '>',
    '\u201c': '',
    '\u2013': '-',
    '\u2212': '-',
    '”': '',
}

def remove_br_chars(txt: str) -> str:
    # Build a regex pattern from the translation table

    pattern = re.compile("|".join(re.escape(key) for key in CHAR_MATCH.keys()))

    match_char = lambda x: CHAR_MATCH[x.group(0)]

    # Replace special characters using the regex pattern
    return pattern.sub(match_char, txt)

def parse_br_lines(txt: str) -> str:
    txt = txt.replace("..", "")
    txt = re.sub(r'\nVigência\n', '\n', txt)
    txt = re.sub(r'\n,\n', ', ', txt)
    txt = re.sub(r'\n.\n', '.\n', txt)
    txt = re.sub(r'\n;\n', ';\n', txt)
    txt = re.sub(r'\n\(', ' (', txt)
    txt = re.sub(r'\)\n', ').. ', txt)
    txt = txt.replace("; e\n", "<> e ")
    txt = txt.replace("; ou\n", "<> ou ")
    txt = txt.replace(":\n", ":>< ")
    txt = txt.replace('.\n', ".. ")
    txt = txt.replace(';\n', ";; ")
    txt = txt.replace('\n', ". ")
    txt = txt.replace('.. ', ".\n")
    txt = txt.replace(';; ', ";\n")
    txt = txt.replace("<> e ", "; e\n")
    txt = txt.replace("<> ou ", "; ou\n")
    txt = txt.replace(":>< ", ":\n")
    txt = txt.replace(". Art.", "\nArt.")
    txt = txt.replace(". Seção", "\nSeção")
    return txt