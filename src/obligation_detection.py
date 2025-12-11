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

def is_index(sentence:str) -> bool:
    sent = sentence.split(" ")[0]
    if len(sent) <= 1:
        return sent in ["I", "V", "X", "L", "C", "D", "M"]
    if sent[0] == '(':
        return False
    if sent[-1] == ')':
        return True
    try:
        val = RomanNumeral.from_string(sent)
        if int(val) > 0:
            return True
        else: return False
    except:
        return False

def extract_modal(sentences, idx, MAX, modals) -> tuple[list[dict], bool]:
    sent = unicodedata.normalize("NFC", sentences[idx]).strip()
    # printf(sent, "unicode.txt")
    # tokens = sent_tokenize(sent)
    # printf(tokens, "token.txt")
    pot_deontic = []
    refs = get_refs(sent, idx)
    if bool(re.search(modals, sent)):
        # If the sentence contains any of the obligation modals,
        # we proceed to extracting references.
        pot_deontic.append({"sentence": sent, "references": refs})
    if sent[-1] == ':' and is_index(sentences[idx+1]):
        sub_sents = []
        for i in range(idx+1, MAX):
            sub, is_part = extract_modal(sentences, i, MAX, modals)
            if is_part:
                sub_sents.extend(sub)
            else:
                break
        for sub in sub_sents:
            merged_sent = sent + " " + sub["sentence"]
            merged_refs = refs + sub["references"]
            pot_deontic.append(
                {
                    "sentence": merged_sent,
                    "references": merged_refs,
                }
            )
    if is_index(sent):
        printf(sent, "subs.txt")
        pot_deontic.append(
            {"sentence": sent,
                "references": refs}
        )
        return pot_deontic, True
    return pot_deontic, False


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

    for i in range(N_SENT):
        pot_deontic, _ = extract_modal(
            sentences, i, N_SENT,
            obligation_modals_re
        )
        d.append(
            {
             "par_id": i,
             "text": sentences[i],
             "potential_deontic": pot_deontic
            }
        )
                
    # Save the extracted data to a JSON file.
    with open("../data/" + name + ".json", "w") as f:
        json.dump(d, f, indent=4)
    
    return d


if __name__ == "__main__":
    obligation_detection(None, "PLIA")