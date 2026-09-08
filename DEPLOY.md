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

Nel `Caddyfile`, **tre** snippet riutilizzabili e il blocco del gate. Vanno
definiti **prima di qualunque blocco di sito**: `import` si risolve in ordine di
lettura, e uno snippet scritto in fondo non esiste per le app scritte sopra —
Caddy lo segnala con «File to import not found», che manda a cercare un file
inesistente invece dell'ordine sbagliato.

```
# Invariante numero uno: nessuna app deve mai ricevere un X-Borant-* messo dal
# client. Va importato in OGNI ramo, gated e pubblico. Vedi la seconda nota.
(noforge) {
    request_header -X-Borant-Sub
    request_header -X-Borant-Email
    request_header -X-Borant-Name
    request_header -X-Borant-Level
    request_header -X-Borant-Hint
    request_header -X-Borant-Expires
}

# Da importare in OGNI blocco di *.borant.eu: nessuna app deve mai vedere il
# cookie di sessione del gate.
(nocookie) {
    request_header Cookie "borant_session=[^;]*;?\s*" ""
}

# route{} impone l'ordine di esecuzione, ed è tutto. Vedi la prima nota.
(borantid) {
    route {
        import noforge

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

Un'app **per-path** — cioè quasi tutte — si scrive così, e il matcher va sui
path **pubblici** e non su quelli privati, di proposito: il ramo di default
dev'essere quello gated, così una rotta aggiunta fra sei mesi nasce chiusa
invece che aperta.

```
esempio.borant.eu {
    @pubbliche path /health /static/* /login /logout
    handle @pubbliche {
        import noforge
        import nocookie
        reverse_proxy localhost:80xx
    }
    handle {
        import borantid
        reverse_proxy localhost:80xx
    }
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

> **`noforge` va importato anche nei rami pubblici, ed è la riga che sembra
> inutile.** Trovato il 21/8/2026 con una prova a vuoto, prima che riguardasse
> un'app vera.
>
> Prima della correzione, un `X-Borant-Sub: 01FORGIATO` spedito verso un path
> **pubblico** arrivava all'app intatto. La cancellazione viveva solo dentro
> `(borantid)`, che i rami pubblici non importano — e su un path pubblico non
> c'è nessuna `forward_auth` che rimetta i valori veri: quello che manda il
> client è tutto quello che l'app riceve.
>
> Il secondo lucchetto **non copre questo caso**, ed è il motivo per cui vale la
> pena scriverlo: `BORANT_TRUSTED_PROXY` verifica *da dove* arriva la richiesta,
> e la richiesta forgiata arriva da Caddy, cioè proprio dalla sorgente che quel
> controllo dichiara fidata. Protegge dal container esposto per sbaglio, non da
> qui.
>
> Per un'app tutta gated non cambia niente. Per un'app per-path in
> `AUTH_MODE=gateway` è un bypass completo dell'identità.

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

## 5. Provisioning anticipato — opzionale, e per app

Serve a una cosa: che il profilo di una persona esista nell'app **prima** che
quella persona ci arrivi. Senza, un centinaio di studenti non esiste di là
finché non ha cliccato, quindi non lo si può mettere in un workspace o in un
corso, e la preparazione di una lezione si sposta dalla sera prima al minuto
dopo l'inizio. È un'aggiunta e non un requisito: le app dove non lo accendi
continuano a creare i profili al primo accesso, come hanno sempre fatto.

**Una rete docker interna, e il bind sul loopback non si tocca.** Le porte
pubblicate restano su `127.0.0.1` (invariante §4). Questa è una seconda rete,
dove il gate e l'app si chiamano per nome senza passare da Caddy e senza
esistere per internet.

```bash
docker network create borant_provision
docker network inspect borant_provision -f '{{(index .IPAM.Config 0).Subnet}}'
```

**La sottorete si legge, non si indovina**: la sceglie docker, e
`172.17.0.0/16` è il *bridge di default*, che è un'altra cosa. Quel valore è ciò
che va in `PROVISION_TRUSTED` dentro l'app.

**La trappola che costa il login, e si paga subito.** Aggiungere una seconda
rete a un container **cambia l'indirizzo da cui il proxy sembra arrivare**.
Docker sceglie fra i gateway delle reti del container in ordine alfabetico di
nome, quindi su RoomPulse `borant_provision` è passata davanti a
`roompulse_default` e le richieste di Caddy hanno smesso di arrivare da
`192.168.0.1` per arrivare da `192.168.240.1`. Il valore in
`BORANT_TRUSTED_PROXY` non combaciava più, l'app ha ignorato gli header del gate,
e **nessuno poteva più entrare** — verificato in produzione l'8 settembre 2026,
con tre righe `X-Borant-Sub da 192.168.240.1, fuori da BORANT_TRUSTED_PROXY` nel
log. Su ArguMap l'ordine è caduto dall'altra parte (`argumap_default` viene prima)
e non è successo niente, che è il modo peggiore di scoprire una regola.

Quindi, insieme alla rete, **sempre**: `BORANT_TRUSTED_PROXY` diventa una lista
con dentro anche il gateway di `borant_provision`.

```
BORANT_TRUSTED_PROXY=192.168.0.1,192.168.240.1
```

Il campo accetta virgole e CIDR da sempre. Metterceli tutt'e due non è
ridondanza difensiva: è che l'ordine può cambiare al prossimo `up -d` senza che
nessuno abbia toccato niente. E la verifica non è «l'app risponde 200» — una
pagina gated risponde 302 sia perché non sei loggato sia perché l'app ha
buttato via l'identità. Si prova **con una sessione vera**, e si guarda il log
dell'app.

Poi, per ogni app che ci sta dentro:

1. Aggiungi la rete a **tutt'e due** i compose, quello dell'app e questo:

   ```yaml
   services:
     borantid:
       networks: [default, borant_provision]
   networks:
     borant_provision:
       external: true
   ```

2. Nell'`.env` dell'app: `PROVISION_SECRET` (una stringa lunga a caso) e
   `PROVISION_TRUSTED` (la sottorete letta sopra). Mancandone una, la rotta di
   là risponde 404 come se non ci fosse.

3. Qui, in `/admin/apps` → l'app → **Provisioning anticipato**: lo stesso
   segreto, e l'indirizzo del container. Attenzione alla porta: è quella su cui
   l'app ascolta **dentro** il container, non quella pubblicata sull'host.

   | app | indirizzo | porta host, da non usare |
   |---|---|---|
   | roompulse | `http://roompulse:8080/internal/provision` | 8011 |
   | argumap | `http://argumap:8000/internal/provision` | 8012 |

4. Premi **«Risincronizza»**. Spinge chi ha già un grant, ed è la prova che il
   cablaggio funziona: se torna un numero, funziona; se torna «non riuscito»,
   il messaggio dice se è la rete (`ConnectError`) o il segreto (`http_404`).

**Cosa può fare la rotta di là, e cosa no.** Crea profili che non ci sono, e
basta: non aggiorna, non promuove, non disattiva. Un segreto rubato compra
account vuoti, non il lavoro di qualcuno — ed è la ragione per cui questo non
viola il §2. Non lega mai per indirizzo: un profilo locale che ha già quella
email e nessun `borant_sub` torna indietro come **conflitto**, intatto, e si
risolve con `map_borant.py` sull'app.

**Il modo `invito` spinge all'accettazione, non all'invio.** Finché l'invito non
è accettato non esiste un account, quindi non c'è nessun subject da annunciare.
È visibile nella pagina del batch: in modo `crea` i numeri del push compaiono
subito, in modo `invito` arrivano uno alla volta man mano che la gente accetta.

**Conseguenza da sapere, non da temere.** Con il push acceso, il profilo orfano
diventa la norma: revocare un grant qui lascia comunque il profilo di là, anche
per chi non è mai entrato. È il limite già noto della cancellazione (SPEC §19),
che adesso capita più spesso.

## Manutenzione

```bash
docker logs borantid --tail 100
docker compose up --build -d          # dopo un aggiornamento
docker exec -it borantid python seed.py --email … --apps   # riallinea le app
docker exec -it borantid python seed.py --apps --descriptions  # e le descrizioni
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
