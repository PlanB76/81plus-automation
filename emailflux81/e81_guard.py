"""e81_guard.py · semantic guard: blocca claim vietati prima dell'invio."""
BLOCK = ["rischio zero","zero multe","garantito","roi garantito","guadagno garantito",
         "100% conforme","evita ogni sanzione","rendimento garantito"]
def violations(text):
    t=(text or "").lower(); return [b for b in BLOCK if b in t]
