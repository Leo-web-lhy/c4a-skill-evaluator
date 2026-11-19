import os

def collect(root):
    files = []
    for dirpath, _, names in os.walk(root):
        for name in sorted(names):
            files.append(os.path.join(dirpath, name))
    return sorted(files)
