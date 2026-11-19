import re

def probe(pattern, text):
    return [m.start() for m in re.finditer(pattern, text)]
