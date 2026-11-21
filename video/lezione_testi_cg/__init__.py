"""Testi della video lezione «Controllo di gestione e bilancio nelle imprese di trasporto» (Univ. Genova): capitoli arg1.py ... arg10.py. S è definita in lezione.py (import ritardato per evitare cicli)."""
def S(*a, **k):
    import lezione
    return lezione.S(*a, **k)
