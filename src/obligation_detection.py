import requests #type: ignore
import requests_cache #type: ignore
from bs4 import BeautifulSoup #type: ignore
import re
import nltk #type: ignore
import unicodedata
import json
import spacy #type: ignore
from nltk.tokenize import sent_tokenize #type: ignore

nltk.download('punkt_tab', quiet=True)
requests_cache.install_cache('deontic_cache')

import br_utils as br

from roman_numerals import RomanNumeral #type: ignore

files = []

def printf(text, file="t.txt"):
    mode = 'a'
    if file not in files:
        files.append(file)
        mode = 'w'
    my_file = open("../data/tests/" + file, mode)
    print(text, file=(my_file))
    print("===================", file=(my_file))
    my_file.close()

def get_url_text(url) -> str:
    # This function parses the HTML content of a given URL
    # Specifically directed to Brazillian Goverment sites

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        )
    }
    
    r = requests.get(url, headers=headers)
    r.encoding = "latin-1"   # or "windows-1252"
    html_text = r.text

    html_text = BeautifulSoup(html_text, 'html.parser').text
    return html_text

def get_html_text(file_path) -> str:
    html_text = open(file_path, 'r')
    html_text = "\n".join(html_text.readlines())
    html_text = html_text.replace(".</p><p>", ".\n")
    html_text = html_text.replace(",</p><p>", ",\n")
    html_text = html_text.replace(";</p><p>", ";\n")
    html_text = html_text.replace(":</p><p>", ":\n")
    html_text = html_text.replace("</p><p>", ".\n")
    html_text = html_text.replace("</p>", "\n")
    html_text = html_text.replace("<p>", "\n")

    html_text = BeautifulSoup(html_text, 'html.parser').text
    return html_text

def trim_whitespace(txt: str) -> str:
    # Remove control characters (like \u0096)
    txt = re.sub(r'[\x00-\x1F\x7F-\x9F]', '\n', txt)
    # Replace all types of line breaks with a single line break
    txt = re.sub(r'\r\n|\r', '\n', txt)
    # Remove blank lines (lines that don't contain any characters)
    txt = re.sub(r'\n\s*\n+', '\n', txt)
    # Normalize whitespace (tabs and spaces)
    txt = re.sub(r'\t|\u00a0'  , ' ', txt)
    # trim repeated spaces
    txt = re.sub(r" +", " ", txt)
    # Strip leading/trailing whitespace from the whole text
    txt = txt.strip()
    # another attempt to remoe excess sspaces
    txt_l = txt.split("\n")
    txt_l = [i.strip() for i in txt_l]
    txt = "\n".join(txt_l)
    return txt

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
    return txt

def remove_br_chars(txt: str) -> str:
    # Create a translation table for special characters
    global translation_table
    # Build a regex pattern from the translation table
    pattern = re.compile("|".join(re.escape(key) for key in br.CHAR_MATCH.keys()))

    match_char = lambda x: br.CHAR_MATCH[x.group(0)]

    # Replace special characters using the regex pattern
    return pattern.sub(match_char, txt)

def texttoref(curr_id, ref):
    # This function converts a reference string into a standardized format.
    if ref[0].lower().startswith('art'):
        if "e" in ref[1].rstrip():
            newref = []
            for item in re.findall(r"\d+", ref[1]):
                newref.append(item.zfill(3) + ".")
        elif "para" in ref[1].rstrip():
            newref = []
            idx = re.search(r"(\d+).+para.+(\d+)", ref[1])
            if idx == None:
                return
            for i in range(int(idx.group(1)), int(idx.group(2))+1):
                newref.append(str(i).zfill(3) + ".")
        else:
            s_res = re.search(r"(\d+)(?:\.(\d+))?", ref[1].rstrip())
            if s_res == None:
                return
            newref = s_res.group(1).zfill(3) + "."
            if s_res.group(2) is not None:
                newref += s_res.group(2).zfill(3)
    else:
        curr_split = curr_id.split(".")[0] + "."
        if "e" in ref[1].rstrip():
            newref = []
            for item in re.findall(r"\d+", ref[1]):
                print(item)
                newref.append([curr_split + item.zfill(3)])
        elif "para" in ref[1].rstrip():
            newref = []
            idx = re.search(r"(\d+).+para.+(\d+)", ref[1])
            if idx == None:
                return
            for i in range(int(idx.group(1)), int(idx.group(2))+1):
                newref.append([curr_split + str(i).zfill(3)])
        else:
            newref = curr_split + ref[1].zfill(3)
    return newref

def get_refs(s, i) -> list:
    refs_str = re.findall(r"(art.|artigo|paragrafo)s? (\d+(?:\(\d+\))?(?:(?:, \d)+,?)?(?: (?:e|para) \d+)?)( of (?:regulamentacao)|(?:diretiva))?", s, re.IGNORECASE)
    refs = []
    for r in refs_str:
        if r[2] != '':
            continue
        refs.append(texttoref(i, r))
    return refs

def is_index(sentence:str) -> int:
    """
    Docstring for is_index
    
    :param sentence: Description
    :type sentence: str
    :return: Description
    :rtype: int

    This function checks if a sentence is an index
      (like "I", "II", "III", etc. or a), b), c), etc.)
    and returns:
    - 0 if it's not an index
    - 1 if it's a roman-numeral index
    - 2 if it's a letter with ) index
    """
    sent = sentence.split(" ")[0]
    if len(sent) <= 1:
        return int(sent in ["I", "V", "X", "L", "C", "D", "M"])
    if sent[0] == '(':
        return 0
    if sent[-1] == ')':
        return 2
    try:
        val = RomanNumeral.from_string(sent)
        if int(val) > 0:
            return 1
        else: return 0
    except:
        return 0

def extract_modal(sentences, idx, MAX, modals) -> tuple[list[dict], int]:
    sent = unicodedata.normalize("NFC", sentences[idx]).strip()
    # printf(sent, "unicode.txt")
    # tokens = sent_tokenize(sent)
    # printf(tokens, "token.txt")
    pot_deontic = []
    refs = get_refs(sent, idx)
    idx_level = is_index(sent)
    if sent[-1] != ':' and ((idx_level > 0) or bool(re.search(modals, sent))):
        # If the sentence is not the start of a list,
        #   and 
        #
        # is part of an index list (needed to return something),
        #   or
        # contains any of the obligation modals,
        # we proceed to extracting references.
        pot_deontic.append({"sentence": sent, "references": refs})
    if sent[-1] == ':':
        sub_sents = []
        sub_idx = idx+1
        while sub_idx < MAX:
            if idx_level + 1 != is_index(sentences[sub_idx]):
                idx = sub_idx - 1
                break
            sub, sub_idx = extract_modal(sentences, sub_idx, MAX, modals)
            sub_sents.extend(sub)
        for sub in sub_sents:
            merged_sent = sent + " " + sub["sentence"]
            merged_refs = refs + sub["references"]
            pot_deontic.append(
                {
                    "sentence": merged_sent,
                    "references": merged_refs,
                }
            )
    return pot_deontic, idx + 1


def obligation_detection(url, name):
    # This function extracts potential deontic references.
    # The extraction is based on the presence of specific obligation modals in the text.

    regulations = {
        "DSA": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2065",
        "AI_Act": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689",
        "GDPR": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
        "LGPD": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
        "PLIA": "../data/PLIA.html"
    }

    if not url:
        url = regulations[name]
    
    if url.find("data/") != -1:
        txt = get_html_text(url)
    else:
        txt = get_url_text(url)
    printf(txt, "original.txt")
    txt = trim_whitespace(txt)
    printf(txt, "trimmed.txt")
    txt = parse_br_lines(txt)
    printf(txt, "parsed.txt")
    # txt = remove_br_chars(txt)
    # printf(txt, "formatted.txt")
    sentences = txt.split("\n")

    obligation_modals_re = r"|".join(br.MODALS)

    d = []

    N_SENT = len(sentences)

    idx = 0
    par = 0
    while idx < N_SENT:
        pot_deontic, new_idx = extract_modal(
            sentences, idx, N_SENT,
            obligation_modals_re
        )
        par += 1
        d.append(
            {
             "par_id": par,
             "text": sentences[idx],
             "potential_deontic": pot_deontic
            }
        )
        idx = new_idx
                
    # Save the extracted data to a JSON file.
    with open("../data/" + name + ".json", "w") as f:
        json.dump(d, f, indent=4)
    
    return d


if __name__ == "__main__":
    obligation_detection(None, "PLIA")