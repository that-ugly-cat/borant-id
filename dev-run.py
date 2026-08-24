"""Avvio locale del pannello, per guardarlo in un browser.

DB usa-e-getta in `.devdata/`, chiave Fernet letta da lì, cookie non-secure
perché in locale non c'è HTTPS: non tocca niente di produzione, e non ha modo
di farlo — `BORANTID_DB` punta altrove.

È uno script Python e non uno shell script di proposito: l'anteprima lancia
`bash` sotto WSL, che vede percorsi `/mnt/c/...` mentre l'interprete è un
binario Windows, e i due non si mettono d'accordo su cosa sia una directory.
Qui l'interprete è già quello giusto e non c'è nessuna traduzione da fare.
"""
import os
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
DEV = BASE / ".devdata"
DEV.mkdir(exist_ok=True)

chiave = DEV / "fernet.key"
if not chiave.exists():
    from cryptography.fernet import Fernet
    chiave.write_text(Fernet.generate_key().decode(), encoding="utf-8")

os.environ.setdefault("BORANTID_DB", str(DEV / "dev.db"))
os.environ.setdefault("FERNET_KEY", chiave.read_text(encoding="utf-8").strip())
os.environ.setdefault("COOKIE_SECURE", "0")
# In produzione il cookie e' su `.borant.eu`, cosi' vale per tutti i
# sottodomini. Su localhost quel dominio non combacia e il browser lo scarta in
# silenzio: si resta sulla pagina di login senza nessun errore da leggere.
os.environ.setdefault("COOKIE_DOMAIN", "")

os.chdir(BASE)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8019)
