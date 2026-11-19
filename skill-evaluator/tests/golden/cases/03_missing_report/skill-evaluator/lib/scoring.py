def score(dim, probes):
    raw = sum(p["weight"] for p in probes if p["hit"])
    return min(raw, dim)
