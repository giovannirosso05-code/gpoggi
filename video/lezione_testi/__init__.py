"""Contenuto della video lezione: la funzione S è definita in lezione.py (importata qui per comodità: import ritardato per evitare cicli)."""
def S(*a, **k):
    import lezione
    return lezione.S(*a, **k)
