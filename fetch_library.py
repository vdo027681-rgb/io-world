import os
import requests

LIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library")
SOURCES = {
    "вертер": "https://www.gutenberg.org/cache/epub/2407/pg2407.txt",
}

def download(word, out_name=None, max_chars=400000):
    os.makedirs(LIB_DIR, exist_ok=True)
    url = SOURCES.get(word) or SOURCES.get(word.lower())
    if url is None:
        return None
    out_name = out_name or (word + ".txt")
    path = os.path.join(LIB_DIR, out_name)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text
    # вырезать примечания Гутенберга
    for marker in ("*** START", "*** END"):
        if marker in text:
            text = text.split(marker, 1)[-1] if marker == "*** START" else text.split(marker, 1)[0]
    text = text[:max_chars]
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def read_corpus(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
