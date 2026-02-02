import requests #type: ignore
import requests_cache #type: ignore
from bs4 import BeautifulSoup #type: ignore
import re
import nltk #type: ignore
import unicodedata
import json
# import spacy #type: ignore
from nltk.tokenize import sent_tokenize #type: ignore

nltk.download('punkt_tab', quiet=True)
requests_cache.install_cache('deontic_cache')

import br_utils as br

from roman_numerals import RomanNumeral #type: ignore

files = []

def printf(text: str, file="t.txt"):
    mode = 'a'
    if file not in files:
        files.append(file)
        mode = 'w'
    my_file = open("../data/tests/" + file, mode)
    print(text, file=(my_file))
    print("===================", file=(my_file))
    my_file.close()

def get_url_text(url: str) -> str:
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

def get_html_text(file_path: str) -> str:
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

def get_txt_text(file_path: str) -> str:
    txt = open(file_path, 'r')
    txt = "".join(txt.readlines()).strip()
    return txt

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

def get_idx_lv(sentence:str) -> int:
    """
    This function checks if a sentence is an index
      (like "I", "II", "III", etc. or a), b), c), etc.)
    and returns:
    - 0 if it's not an index
    - 1 if it's a roman-numeral index
    - 2 if it's a letter with ) index
    """
    sent = sentence.split(" ")[0]
    if sent == "":
        return 0
    if sent in ["§", "Parágrafo", "Art.", "Artigo", "Art"]:
        return -1
    if len(sent) == 1 and sent in ["I", "V", "X", "L", "C", "D", "M"]:
        return 1
    if sent[-1] == ')':
        return 2
    try:
        val = RomanNumeral.from_string(sent)
        if int(val) > 0:
            return 1
        else: return 0
    except:
        return 0


# Global variable to hold the current paragraph ID
par_id = [0, 0, 0, 0, 0, 0]  # H1 to H6

def update_par_id(sentence: str) -> None:
    """
    This function updates the par_id list based on the
    hierarchical level of the current sentence.
    H1: CAPÍTULO (Ex: CAPÍTULO I DISPOSIÇÕES PRELIMINARES)
    É a divisão principal do texto apresentado.
    H2: Seção (Ex: Seção I Dos Direitos da Pessoa...)
    É uma subdivisão dentro dos Capítulos.
    Nota: Nem todos os capítulos possuem seções.
    Onde não houver, o fluxo segue direto do H1 para o H3.
    H3: Artigo (Ex: Art. 1º, Art. 15.)
    É a unidade básica da lei (o caput).
    Não são atualizados pelas hierarquias superiores (H1 e H2).
    H4: Parágrafo (Ex: § 1º, Parágrafo único)
    É o desdobramento imediato do artigo.
    H5: Inciso (Ex: I –, II –, XX –)
    Representado por algarismos romanos. Pode aparecer subordinado diretamente ao Artigo (H3) ou a um Parágrafo (H4).
    Para manter a consistência da árvore, ele ocupa a 5ª posição hierárquica.
    H6: Alínea (Ex: a), b), c))
    Representada por letras minúsculas. É uma subdivisão dos incisos.
    """
    global par_id
    art = par_id[2]
    if sentence.startswith("CAPÍTULO"):
        par_id[0] += 1
        par_id[1:] = [0, art, 0, 0, 0]
    elif sentence.startswith("Seção"):
        par_id[1] += 1
        par_id[2:] = [art, 0, 0, 0]
    elif re.match(r"^(Art\.|Artigo)", sentence):
        art = sentence.split(" ")[1]
        if art.endswith(".") or art.endswith("º"):
            art = art[:-1]
        try:
            art_num = int(re.findall(r"\d+", art)[0])
        except:
            art_num = par_id[2] + 1
        par_id[2] = art_num
        par_id[3:] = [0, 0, 0]
    elif re.match(r"^(§|Parágrafo)", sentence):
        par_id[3] += 1
        par_id[4:] = [0, 0]
    elif re.match(r"^[IVXLCDM]+(\s–|-)", sentence):
        par_id[4] += 1
        par_id[5:] = [0]
    elif re.match(r"^[a-z]+(\)|\))", sentence):
        par_id[5] += 1

MAX = 0 # Global variable to hold the maximum number of sentences
def extract_modal(sentences, idx, modals) -> tuple[list[dict], int, str]:
    global MAX
    if idx >= MAX:
        return [], idx, ""
    sent = unicodedata.normalize("NFC", sentences[idx]).strip()
    update_par_id(sent)
    global par_id
    this_id = ".".join([str(p) for p in par_id])
    # printf(sent, "unicode.txt")
    # tokens = sent_tokenize(sent)
    # printf(tokens, "token.txt")
    pot_deontic = []
    refs = get_refs(sent, idx)
    idx_level = get_idx_lv(sent)
    if sent[-1] != ':' and ((idx_level != 0) or bool(re.search(modals, sent))):
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
        while True:
            if sub_idx >= MAX:
                idx = sub_idx - 1
                break
            sub_level = get_idx_lv(sentences[sub_idx])
            if (sub_level == -1 and idx_level == 0) or (idx_level == -1 and sub_level == 1):
                # Paragrafos complementam o artigo, mas não os incisos,
                # Parágrafo dentro de uma lista de incisos, interrompe a busca.
                # Parágrafo dentro de um artigo, continua a busca.
                pass
            elif sub_level != idx_level + 1:
                # Se o subnível não for exatamente um nível abaixo
                # do nível atual, acabou a lista de subitens.
                idx = sub_idx - 1
                break
            sub, sub_idx, _ = extract_modal(sentences, sub_idx, modals)
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
    return pot_deontic, idx + 1, this_id


def obligation_detection(url, name):
    # This function extracts potential deontic references.
    # The extraction is based on the presence of specific obligation modals in the text.

    regulations = {
        "DSA": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2065",
        "AI_Act": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689",
        "GDPR": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
        "LGPD": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
        "PLIA": "../data/PLIA.html",
    }

    if not url:
        url = regulations[name]

    preformated = False
    if url.find("data/") == -1:
        txt = get_url_text(url)
    elif url.endswith(".html"):
        txt = get_html_text(url)
    elif url.endswith(".txt"):
        preformated = True
        txt = get_txt_text(url)
    else:
        print("File format not supported.")
        return
    if not preformated:
        printf(txt, "original.txt")
        txt = trim_whitespace(txt)
        printf(txt, "trimmed.txt")
        txt = br.parse_br_lines(txt)
        printf(txt, "parsed.txt")
    sentences = txt.split("\n")

    obligation_modals_re = r"|".join(br.MODALS)

    d = []

    global MAX
    MAX = len(sentences)

    idx = 0
    while idx < MAX:
        pot_deontic, new_idx, this_id = extract_modal(
            sentences, idx,
            obligation_modals_re
        )
        d.append(
            {
             "par_id": this_id,
             "text": sentences[idx],
             "potential_deontic": pot_deontic
            }
        )
        idx = new_idx

    # Save the extracted data to a JSON file.
    with open("../data/" + name + ".json", "w") as f:
        # formats with UTF-8 to allow special characters
        json.dump(d, f, indent=4, ensure_ascii=False)

    return d


if __name__ == "__main__":
    # mkdir data/tests
    obligation_detection("../data/PLIA.txt", "PLIA")