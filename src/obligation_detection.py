import requests
import requests_cache #type: ignore
from bs4 import BeautifulSoup #type: ignore
import re
import nltk #type: ignore
import unicodedata
import json
import spacy #type: ignore
from nltk.tokenize import sent_tokenize #type: ignore

nltk.download('punkt_tab')
requests_cache.install_cache('deontic_cache')

from br_utils import obligation_modals, indexers

from roman_numerals import RomanNumeral #type: ignore

def is_index(sentence:str) -> bool:
    sent = sentence.split(" ")[0]
    if len(sent) == 1:
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



def texttoref(curr_id, ref):
    # This function converts a reference string into a standardized format.
    if ref[0].lower().startswith('article'):
        if "and" in ref[1].rstrip():
            newref = []
            for item in re.findall(r"\d+", ref[1]):
                newref.append(item.zfill(3) + ".")
        elif "to" in ref[1].rstrip():
            newref = []
            idx = re.search(r"(\d+).+to.+(\d+)", ref[1])
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
        if "and" in ref[1].rstrip():
            newref = []
            for item in re.findall(r"\d+", ref[1]):
                print(item)
                newref.append([curr_split + item.zfill(3)])
        elif "to" in ref[1].rstrip():
            newref = []
            idx = re.search(r"(\d+).+to.+(\d+)", ref[1])
            if idx == None:
                return
            for i in range(int(idx.group(1)), int(idx.group(2))+1):
                newref.append([curr_split + str(i).zfill(3)])
        else:
            newref = curr_split + ref[1].zfill(3)
    return newref

def get_refs(s, x):
    refs_str = re.findall(r"(artigo|parágrafo)s? (\d+(?:\(\d+\))?(?:(?:, \d)+,?)?(?: (?:and|to) \d+)?)( of (?:regulation)|(?:directive))?", s, re.IGNORECASE)
    refs = []
    for r in refs_str:
        if r[2] != '':
            continue
        refs.append(texttoref(x.get('id'), r))

def obligation_detection(url, name):
    # This function parses the HTML content of a given URL and extracts potential deontic references.
    # The extraction is based on the presence of specific obligation modals in the text.

    regulations = {
        "DSA": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2065",
        "AI_Act": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401689",
        "GDPR": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679"
    }

    if not url:
        url = regulations[name]

    r = requests.get(url)

    obligation_modals = ["shall", "must", "is to", "are to", "should", "has to", "have to"]
    obligation_modals_re = r"|".join(obligation_modals)

    bs = BeautifulSoup(r.text, 'html.parser')

    all_div = bs.find_all('div', id=re.compile("^\d+\.\d+"))
    d = []

    for x in all_div:
        text = unicodedata.normalize("NFKD", re.sub(r"\n+", " ", x.text)).strip()
        sentences = sent_tokenize(text)
        pot_deontic = []
        for i, s in enumerate(sentences):
            if bool(re.search(obligation_modals_re, s)):
                # If the sentence contains any of the obligation modals, we proceed to extracting references.
                refs = get_refs(s, x)
                pot_deontic.append({"sentence": s, "references": refs})
            if s[-1] == ':':
                refs = get_refs(s, x)
                if is_index(sentences[i+1]):
                    for subs in sentences[i+1:]:
                        if is_index(subs):
                            rep = s + " " + subs
                            pot_deontic.append({"sentence": rep, "references": refs})
                        else:
                            break
        d.append({"par_id": x.get('id'), "text": text, "potential_deontic": pot_deontic})
                
    # Save the extracted data to a JSON file.
    with open(name + ".json", "w") as f:
        json.dump(d, f, indent=4)
    
    print("HERE")
    return d


if __name__ == "__main__":
    obligation_detection(None, "AI_Act")