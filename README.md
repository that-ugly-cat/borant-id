# Borant ID

Un ingresso solo per gli strumenti accademici su `borant.eu`.

Al posto di dodici moduli `auth.py` scritti a mano, quattro schemi di hashing
password in parallelo e sei nomi di cookie diversi, un servizio che fa **due
cose**: autentica una persona, e dice alle app chi è entrato.

Il guadagno che si racconta è il login unico. Quello che conta davvero è un
altro: fino a oggi **nessuna sessione era revocabile** in nessuna delle app,
perché portano tutte JWT stateless. Un cookie rubato valeva finché non scadeva.

Per il disegno completo vedi `SPEC.md`.

## Stato, al 21 agosto 2026

**Sei app dietro il gate**, tutte per-path: `paper2md`, `onopedia`, `roompulse`,
`lssr`, `papertrail`, `contrarian`. Ne restano cinque nel perimetro —
`grantradar`, `survey`, `topictracker`, `autocode`, `argumap` — e la checklist
per migrarne una sta nel §13 della spec.

Tre cose imparate migrandone sei, che valgono più di qualunque elenco di
funzionalità:

- **«Non cambia una riga di codice» non è mai stato vero.** Tutte e sei hanno
  avuto bisogno del lettore di header, comprese quelle date per «solo la porta».
  Un'app che ha un modo *suo* di riconoscere chi entra non lo perde perché gli
  metti un gate davanti: senza codice ottieni due porte in fila, non una.
- **Che superficie pubblica ha un'app non è solo una domanda sul codice.** Per
  `paper2md` la risposta stava sul sito, che la annunciava come «no login»:
  gatarla tutta ha reso falsa una pagina pubblica per mezza giornata.
- **La protezione può stare in un middleware.** Un censimento delle rotte che
  guarda solo i corpi delle funzioni produce un elenco di falsi positivi con
  l'aria di essere completo.

## Il vincolo che viene prima di tutto

**Ogni app continua a funzionare senza Borant ID.** Non è una promessa di
compatibilità, è un requisito: non tutti i deploy futuri di queste app staranno
su una macchina che ha il gate.

Quindi Borant ID non è un pezzo delle app, è una **modalità**:

```
AUTH_MODE=local     (default)   l'app autentica da sé, come ha sempre fatto
AUTH_MODE=gateway               l'app si fida degli header X-Borant-*
```

`local` è il default per sicurezza prima che per portabilità: un'app che crede
agli header e finisce deployata senza gate davanti regala l'identità a chiunque
sappia scrivere un header.

## Come funziona

```
browser → Caddy → (path pubblico? → app, anonimo)
                → forward_auth → Borant ID → 200 + X-Borant-Sub/Email/Name/Level/Hint
                                           → 302 al login  ·  401 se è una fetch
```

Le app **non parlano mai** con Borant ID: nessun client OAuth, nessun segreto
condiviso, nessuna libreria. Leggono un header che Caddy attacca.

Non è un provider OIDC e non lo diventerà: niente discovery, JWKS, PKCE,
refresh, consent. È esattamente la parte dove gli IdP artigianali muoiono, e non
serve.

## Cosa fa

- utenti, password bcrypt, TOTP opzionale (RFC 6238, stdlib) e codici di backup
- **ORCID** come metodo d'accesso alternativo e collegabile
- sessioni **stateful, scorrevoli e revocabili** — cookie opaco su `.borant.eu`
- **step-up**: due livelli, `one_factor` e `two_factor`. La 2FA non è
  obbligatoria in generale ma può esserlo per certe app, e la challenge *eleva
  la sessione esistente* invece di rimandare al login
- `apps` / `policies` / `grants`: chi entra dove, e che livello serve su quale
  path
- inviti e reset via SMTP, con il link a schermo quando la mail non parte
- audit log, notifiche di sicurezza, rate limiting

## Cosa non fa, per scelta

Provider OIDC · SAML · federazione in uscita · SCIM · **ruoli di dominio** (i
workspace di PaperTrail, le membership di LSSR, i coder di AutoCode restano dove
sono: Borant ID dice *chi sei*, l'app decide *cosa puoi*) · autorizzazione
per-risorsa · gestione delle API key MCP.

## Faccia e lingue

**Palette scura dei tool**, la stessa di LSSR, AutoCode e ArguMap: fondo
`#0f1117`, card `#1a1d27`, primario `#0a3c8a`, accento `#63b3ed`, font di
sistema a 15px, `.topbar` / `.container` / `.card` / `.btn` / `.badge` /
`.flash` come nomi di classe.

Non è l'identità corporate di `borant.eu` (navy `#0D1B3E` e arancio `#E87722`
su fondo bianco): quella è la faccia dell'azienda verso chi arriva da fuori,
questa è la faccia degli attrezzi verso chi ci lavora dentro. Del sito
corporate resta soltanto il **logo**, nella topbar.

**Quattro lingue** — it, en, de, fr — in `locales.py`, sul pattern di RoomPulse
e ArguMap. Si sceglie da `/lang/{code}`, si ricorda in un cookie di un anno, e
al primo arrivo si indovina da `Accept-Language` rispettando i q-value. I
pannelli `/admin` restano in italiano: li usa una persona sola.

## Sviluppo

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv -r requirements.txt

export FERNET_KEY=$(.venv/Scripts/python.exe -c \
  "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export COOKIE_DOMAIN= COOKIE_SECURE=0     # niente dominio, http locale

.venv/Scripts/python.exe seed.py --email tu@example.com --name Tu --apps
.venv/Scripts/python.exe -m uvicorn main:app --port 8019
```

`--apps` registra le undici app del perimetro con la policy di default e i
`two_factor` dove la SPEC li chiede. **Registrare non è gatare**: il gate lo
accende un blocco Caddy, un'app alla volta.

### Provare /verify a mano

```bash
curl -i -H "X-Forwarded-Host: papertrail.borant.eu" \
        -H "X-Forwarded-Uri: /admin" \
        -H "Sec-Fetch-Mode: navigate" -H "Accept: text/html" \
        -b "borant_session=..." http://127.0.0.1:8019/verify
```

## Struttura

| file | cosa c'è |
|---|---|
| `models.py` | tabelle, ULID, hashing dei token, engine SQLite in WAL |
| `auth.py` | sessioni, cache con invalidazione, normalizzazione dei path, la decisione di `/verify` |
| `main.py` | `/verify` e le rotte umane |
| `admin.py` | utenti, app, policy, grant, sessioni, log, configurazione |
| `orcid.py` | code flow ORCID, a mano, senza stack OIDC |
| `mailer.py` | SMTP, e la garanzia che nulla qui solleva eccezioni |
| `settings.py` | configurazione in database, con la password SMTP cifrata |
| `totp.py` | TOTP e codici di backup, stdlib — terza copia in casa dopo survey e autocode |
| `crypto.py` | Fernet per i secret recuperabili |

## Licenza

Non ancora decisa. Finché non lo è, considerarlo privato.
