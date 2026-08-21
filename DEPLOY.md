# Deploy — Borant ID

VPS `borant.eu`, `/opt/apps/borantid`, porta **8019**, dietro Caddy su
`id.borant.eu`.

Non 8018: quella è di Onopedia. La tabella nella pagina wiki del VPS la dava
per libera ed era ferma; prima di assegnare una porta, `docker ps` sul server.

---

## 0. Prerequisiti

- [ ] record **A** per `id.borant.eu` in Cloudflare, **Proxy status: DNS only**
      (arancione rompe Let's Encrypt)
- [ ] client ORCID pubblico registrato su orcid.org → Developer Tools, con
      redirect URI `https://id.borant.eu/orcid/callback` — si può anche fare
      dopo, il resto funziona lo stesso
- [ ] casella SMTP scelta — **non serve al deploy**, si configura da
      `/admin/config` a servizio acceso

## 1. Prima installazione

```bash
ssh <utente>@<vps>
sudo mkdir -p /opt/apps/borantid && cd /opt/apps/borantid
git clone https://github.com/that-ugly-cat/borant-id .
cp docker-compose.yml.example docker-compose.yml
cp .env.example .env
```

> Indirizzo del server, utente e chiave SSH non stanno qui: questo repo è
> pubblico. Sono nella pagina wiki dell'infrastruttura.

Genera la chiave e mettila nel `.env`:

```bash
docker run --rm python:3.12-slim sh -c \
  "pip -q install cryptography && python -c \
   'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
```

> **`FERNET_KEY` va messa al sicuro subito.** Se la perdi: i secret TOTP
> diventano illeggibili (tutti riattivano il secondo fattore) e la password
> SMTP va reinserita. Le password degli utenti non sono toccate — sono hash
> bcrypt e non passano di lì.

Poi:

```bash
docker compose up --build -d
docker exec -it borantid python seed.py --email TUA@MAIL --name Spit --apps
```

`seed.py` stampa una password generata. Cambiala dal profilo al primo accesso.

## 2. Caddy

Nel `Caddyfile`, **due** snippet riutilizzabili e il blocco del gate:

```
# Da importare nei blocchi PUBBLICI di *.borant.eu: nessuna app deve mai
# vedere il cookie di sessione del gate.
(nocookie) {
    request_header Cookie "borant_session=[^;]*;?\s*" ""
}

# route{} impone l'ordine di esecuzione, ed è tutto. Vedi la nota qui sotto.
(borantid) {
    route {
        request_header -X-Borant-Sub
        request_header -X-Borant-Email
        request_header -X-Borant-Name
        request_header -X-Borant-Level
        request_header -X-Borant-Hint
        request_header -X-Borant-Expires

        forward_auth localhost:8019 {
            uri /verify
            copy_headers X-Borant-Sub X-Borant-Email X-Borant-Name X-Borant-Level X-Borant-Hint X-Borant-Expires
        }

        import nocookie
    }
}

id.borant.eu {
    # /verify è solo per la forward_auth interna, mai per il pubblico
    respond /verify 404
    reverse_proxy localhost:8019
}
```

> **`route{}` non è cosmetica, e senza di essa la configurazione è rotta in due
> modi opposti.** Verificato sul campo il 20/8/2026, non dedotto.
>
> Fuori da un `route{}` Caddy riordina le direttive a modo suo, e le
> cancellazioni `request_header -X-Borant-*` finiscono **dopo** `copy_headers`:
> il risultato è che spariscono anche gli header veri, e l'app riceve
> un'identità vuota. Sintomo: tutto sembra funzionare, ma a valle non arriva
> nessuno.
>
> Il cookie ha il vincolo **opposto**: `forward_auth` inoltra gli header della
> richiesta originale, quindi se `nocookie` gira *prima*, il gate non vede mai
> la sessione e nessuno entra più. Deve girare **dopo**.
>
> Tre fasi in un ordine solo: cancella → autentica → togli il cookie. È
> esattamente quello che `route{}` garantisce e che l'ordinamento automatico
> non garantisce.

```bash
sudo systemctl reload caddy
```

A questo punto Borant ID **è in piedi e non gata niente**. È il punto giusto in
cui fermarsi e fare il passo 3.

## 3. La prova a vuoto — non saltarla

Prima di mettere il gate davanti a un'app vera, mettilo davanti a niente:

```
prova.borant.eu {
    import borantid
    respond "ciao {http.request.header.X-Borant-Email}"
}
```

Tre verifiche, tutte e tre da fare:

```bash
# 1. header forgiato: la risposta NON deve contenere pippo@male.it
curl -s -H "X-Borant-Email: pippo@male.it" -b "borant_session=…" https://prova.borant.eu/

# 2. senza cookie: deve rimbalzare al login
curl -si https://prova.borant.eu/ | head -3

# 3. traversata: /pubblico/../admin non deve valere come /pubblico
```

La prima è l'invariante su cui poggia tutta l'autenticazione. L'ordine delle
direttive di Caddy *dovrebbe* far girare `request_header -X-Borant-*` prima
della `forward_auth`, ma "dovrebbe" non basta: si guarda cosa arriva davvero
dall'altra parte.

## 4. Una app alla volta

Ordine: **paper2md** (solo tu, niente pubblico, niente MCP) → onopedia →
grantradar → contrarian → survey → topictracker → poi le cinque di categoria B
(roompulse → lssr → papertrail → autocode → argumap).

Per ogni app, nell'ordine:

1. inviti mandati e **accettati** da tutti gli utenti attivi
2. (categoria B) colonna `borant_sub`, script di mappatura, report letto
3. riga in `/admin/apps`, policy `two_factor` dove serve, grant assegnati
4. blocco Caddy con i path pubblici **letti dal codice**, non ipotizzati
5. le tre prove del passo 3, su quell'app
6. prova con un utente non-admin, non solo col tuo account
7. **rollback provato** prima di considerare chiuso il passo

Esempio, LSSR:

```
lssr.borant.eu {
    @pubbliche path /r/* /health /static/*
    handle @pubbliche {
        import nocookie
        reverse_proxy localhost:8013
    }
    handle {
        import borantid
        reverse_proxy localhost:8013
    }
}
```

**Rollback**, sempre in due mosse indipendenti dalle altre app:
`AUTH_MODE=local` nell'`.env` dell'app più `docker compose up -d`, e togliere
`import borantid` dal blocco Caddy. La prima da sola basta.

## Manutenzione

```bash
docker logs borantid --tail 100
docker compose up --build -d          # dopo un aggiornamento
docker exec -it borantid python seed.py --email … --apps   # riallinea le app
```

Il database sta in `/opt/apps/borantid/data/borantid.db`, su volume, e
sopravvive ai redeploy. È incluso nei backup Hetzner del server.

## Se il gate è giù

Tutto il perimetro gated è giù: è il prezzo del disegno, ed è per questo che
`restart: always` e l'healthcheck sono nel compose.

Per entrare comunque in una singola app: `AUTH_MODE=local` nel suo `.env` e
riavviala. Venti secondi, nessuna migrazione, nessuna perdita di dati.

> Attenzione al monitoraggio: `/healthz` sta **fuori** dal gate, quindi resta
> verde anche quando il gate è morto e nessuno riesce più a entrare da nessuna
> parte. Un controllo utile deve puntare anche a una rotta gated.
