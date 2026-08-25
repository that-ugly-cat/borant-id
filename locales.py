"""
Stringhe UI di Borant ID — it, en, de, fr.

Pattern allineato a `roompulse/app/locales.py` e a quello di ArguMap: un'unica
sorgente per tutte le stringhe, e ogni chiave va aggiunta in **tutte e quattro**
le lingue insieme. Una chiave mancante ricade sull'italiano invece di esplodere,
ma quello è un paracadute, non un permesso.

**Cosa è tradotto: tutto quello che si vede**, `/admin` compreso. Il pannello
è stato in italiano fino al 25 agosto 2026, con la ragione che lo leggeva una
persona sola. Quella ragione reggeva finché nessuno provava a cambiare lingua
stando dentro: lo switcher sta in `base.html`, quindi su `/admin` traduceva la
barra in alto e lasciava italiana la pagina sotto. Uno switcher che promette e
non mantiene costa più delle righe che risparmia, e le chiavi `adm_*` sono il
prezzo pagato per toglierlo di mezzo.

La lingua si sceglie con `/lang/{code}`, si ricorda in un cookie di un anno, e
al primo arrivo si indovina da `Accept-Language`.

**Alcune chiavi non sono testo ma forma.** `fmt_datetime`, `fmt_datetime_short`,
`fmt_date` e `fmt_datetime_sec` sono stringhe di `strftime`, e stanno qui perché
una data è tanto tradotta quanto una frase — `24/08/2026` è il 24 agosto per tre
lettori su quattro e il niente per il quarto. Niente `%b` fuori dall'inglese:
senza `setlocale` Python lo rende comunque in inglese, quindi lì sarebbe una
parola non tradotta travestita da formato.

`plural_zero_singular` è della stessa famiglia: dice se lo zero vuole il
singolare, che è l'unico disaccordo di plurale fra queste quattro lingue. Si
legge da `singular()`, non a mano.

**Le frasi con un numero dentro hanno due chiavi**, `_one` e l'altra, e la
scelta passa da `singular()`. Non è pedanteria: l'italiano perdona «1 app», ma
«1 tools», «1 Werkzeuge» e «1 outils» sono sbagliate tutte e tre.

**Gli errori arrivano come codice, non come frase.** `orcid.exchange`,
`mailer.send` e `_delete_blockers` tornano un identificatore; la frase la
sceglie chi rende la pagina, nella lingua di chi guarda. È la regola che
impedisce a una stringa italiana di riaffiorare dentro una pagina tedesca, che
è com'era finita agli errori ORCID.

**Quello che il database dice, il dizionario non lo può dire.** Nomi e
descrizioni delle app arrivano da `apps`, non da qui, e si vedono uguali in
tutte e quattro le lingue: sono in inglese per la stessa ragione delle vetrine
pubbliche, e il testo canonico sta in `seed.py`.
"""

SUPPORTED = ("it", "en", "de", "fr")
DEFAULT = "it"
COOKIE = "borant_lang"

LANGUAGE_NAMES = {"it": "Italiano", "en": "English", "de": "Deutsch", "fr": "Français"}

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── ITALIANO ──────────────────────────────────────────────────────────────
    "it": {
        # chrome
        "nav_profile": "Profilo",
        "nav_users": "Utenti",
        "nav_apps": "App",
        "nav_sessions": "Sessioni",
        "nav_log": "Log",
        "nav_config": "Configurazione",
        "nav_logout": "Esci",
        "logout_title": "Uscire da Borant ID?",
        "logout_sub": "Chiude la sessione qui e in tutti gli strumenti che stanno dietro a questo ingresso, non solo in quello da cui sei arrivato.",
        "logout_confirm": "Esci",
        "logout_cancel": "Annulla",
        "tagline": "Accesso unico agli strumenti di ricerca",

        # comune
        "email": "Email",
        "password": "Password",
        "back": "Torna indietro",
        "save": "Salva",
        "fmt_datetime": "%d/%m/%Y %H:%M",
        "fmt_datetime_short": "%d/%m %H:%M",

        # login
        "login_title": "Accedi",
        "login_sub": "Un ingresso solo per gli strumenti su borant.eu.",
        "login_enter": "Entra",
        "login_forgot": "Password dimenticata",
        "login_err": "Email o password non validi.",
        "login_rate": "Troppi tentativi. Riprova fra un quarto d'ora.",
        "login_orcid": "Entra con ORCID",
        "login_orcid_note": "Funziona se il tuo ORCID è già collegato a un account qui. "
                            "Se non lo è, chiedi un invito: potrai accettarlo proprio con ORCID.",
        "cookie_trouble_title": "Il cookie di sessione non si posa.",
        "cookie_trouble_body": "Risulti autenticato, ma il browser non riporta indietro la "
                               "sessione: di solito è un blocco dei cookie, un orologio molto "
                               "sfasato, oppure il dominio del cookie configurato male. Prova a "
                               "riaccedere; se ricapita, segnalalo a un amministratore invece di "
                               "insistere.",

        # secondo fattore
        "twofa_title": "Secondo fattore",
        "twofa_sub": "Questa destinazione chiede una verifica in più. Non stai rifacendo il "
                     "login: la sessione che hai già viene elevata.",
        "twofa_code": "Codice dell'app di autenticazione",
        "twofa_verify": "Verifica",
        "twofa_backup_note": "Puoi usare anche uno dei codici di backup, nel formato "
                             "<code>abcd-1234</code>.",
        "twofa_err": "Codice non valido.",
        "twofa_err_retry": "Codice non valido. Riprova.",
        "twofa_rate": "Troppi tentativi. Aspetta qualche minuto.",

        # arruolamento
        "enroll_title": "Attiva il secondo fattore",
        "enroll_sub": "La destinazione che hai chiesto richiede due fattori e tu non ne hai "
                      "ancora uno. Si attiva qui, adesso: sei già autenticato, quindi non c'è "
                      "nessun vicolo cieco.",
        "enroll_qr_alt": "QR code per l'app di autenticazione",
        "enroll_manual": "Oppure inserisci a mano questa chiave",
        "enroll_apps": "Va bene qualsiasi app TOTP: Ente Auth, Aegis, Google Authenticator.",
        "enroll_confirm": "Conferma con il codice che l'app mostra adesso",
        "enroll_activate": "Attiva",
        "enroll_note": "La chiave viene salvata solo dopo che un codice ha dimostrato che l'app "
                       "ce l'ha davvero.",

        # codici di backup
        "codes_title": "Codici di backup",
        "codes_sub": "Dieci codici, ognuno usabile una volta sola, al posto del codice dell'app "
                     "quando non hai il telefono. <strong>Non li rivedrai.</strong>",
        "codes_invalidated": "I codici precedenti, se ce n'erano, sono stati invalidati.",
        "codes_done": "Fatto, li ho messi al sicuro",

        # home
        "home_hello": "Ciao",
        "home_sub": "Gli strumenti a cui hai accesso.",
        "home_col_app": "App",
        "home_col_address": "Indirizzo",
        "home_open": "Apri",
        "home_empty": "Nessuna app associata al tuo account. Se dovresti averne una, chiedi a un "
                      "amministratore.",
        "home_note": "Dal profilo puoi cambiare password, attivare il secondo fattore, collegare "
                     "ORCID e chiudere le sessioni aperte.",

        # non autorizzato
        "forbidden_title": "Non hai accesso a questa app",
        "forbidden_sub": "Sei autenticato correttamente. È l'accesso a questo indirizzo che non "
                         "è previsto per il tuo account.",
        "forbidden_ask": "Chiedi accesso",
        "forbidden_mine": "Le mie app",
        "forbidden_sent_title": "Richiesta inviata",
        "forbidden_sent_body": "Gli amministratori sono stati avvisati.",
        "gate_unknown_host": "Questo indirizzo non è registrato in Borant ID. Non è il tuo "
                             "account a mancare di qualcosa: è la configurazione del gate. "
                             "Segnalalo a un amministratore.",

        # invito
        "invite_title": "Attiva il tuo accesso",
        "invite_for": "Invito per",
        "invite_name": "Nome",
        "invite_pw": "Password (almeno 10 caratteri)",
        "invite_pw2": "Ripeti la password",
        "invite_activate": "Attiva",
        "invite_err": "La password deve essere di almeno 10 caratteri e le due copie devono "
                      "coincidere.",
        "invite_orcid_note": "Potrai collegare il tuo ORCID subito dopo, dal profilo. Il "
                             "collegamento avviene solo da una sessione già autenticata: mai per "
                             "corrispondenza automatica di email.",
        "invite_bad_title": "Invito non valido",
        "invite_bad_body": "Il link è scaduto o è già stato usato. Chiedine un altro.",

        # reset
        "reset_title": "Reimposta la password",
        "reset_sub": "Ti mandiamo un link valido un'ora.",
        "reset_send": "Mandami il link",
        "reset_sent": "Se quell'indirizzo ha un account qui, è partita una mail con il link. "
                      "Scade fra un'ora e si usa una volta sola.",
        "reset_privacy": "Non ti diciamo se l'indirizzo esiste: non è una cosa che un form debba "
                         "rivelare. Se la mail non arriva, chiedi a un amministratore — può darti "
                         "il link a mano.",
        "reset_back": "Torna al login",
        "reset_new_title": "Nuova password",
        "reset_new_sub": "Tutte le sessioni aperte verranno chiuse.",
        "reset_err": "Almeno 10 caratteri, e le due copie devono coincidere.",
        "reset_expired_title": "Link scaduto",
        "reset_expired_body": "Il link di reimpostazione non è più valido. Chiedine un altro.",
        "reset_done_title": "Password aggiornata",
        "reset_done_body": "Tutte le sessioni aperte sono state chiuse. Puoi accedere con la "
                           "password nuova.",

        # profilo
        "profile_title": "Profilo",
        "profile_pw": "Password",
        "profile_pw_current": "Password attuale",
        "profile_pw_new": "Nuova",
        "profile_pw_repeat": "Ripeti",
        "profile_pw_change": "Cambia",
        "profile_pw_note": "Cambiando la password si chiudono tutte le altre sessioni, questa "
                           "esclusa.",
        "profile_pw_err": "Password attuale non corretta.",
        "profile_pw_short": "Almeno 10 caratteri, e le due copie devono coincidere.",
        "profile_2fa": "Secondo fattore",
        "profile_2fa_on": "Attivo",
        "profile_2fa_off": "Non attivo",
        "profile_2fa_codes": "Codici di backup non ancora usati:",
        "profile_2fa_regen": "Rigenera i codici di backup",
        "profile_2fa_always_on": "Chiedimelo a ogni accesso",
        "profile_2fa_always_off": "Non chiedermelo a ogni accesso",
        "profile_2fa_disable": "Disattiva",
        "profile_2fa_note": "Non è obbligatorio in generale, ma alcune app lo richiedono: quando "
                            "ne apri una, l'attivazione ti viene proposta lì per lì.",
        "profile_2fa_activate": "Attivalo adesso",
        "profile_2fa_msg": "Autenticazione a due fattori attiva. Genera i codici di backup e "
                           "mettili al sicuro.",
        "profile_orcid": "ORCID",
        "profile_orcid_linked": "Collegato:",
        "profile_orcid_one": "ORCID vale come <strong>un fattore solo</strong>: il suo token non "
                             "dice in modo affidabile se hai fatto la verifica in due passaggi da "
                             "loro, quindi per le app che chiedono due fattori serve comunque il "
                             "codice qui.",
        "profile_orcid_note": "Collegarlo ti permette di entrare con ORCID invece che con la "
                              "password.",
        "profile_orcid_link": "Collega il mio ORCID",
        "profile_orcid_none": "ORCID non è ancora configurato su questo server.",
        "profile_sessions": "Sessioni aperte",
        "profile_s_opened": "Aperta",
        "profile_s_last": "Ultimo accesso",
        "profile_s_origin": "Origine",
        "profile_s_level": "Livello",
        "profile_s_this": "questa",
        "profile_s_two": "due fattori",
        "profile_s_one": "un fattore",
        "profile_s_close": "Chiudi",
        "profile_s_close_all": "Chiudi tutte, anche questa",
        "profile_s_note": "Questa lista è il motivo per cui Borant ID esiste: fino a oggi nessuna "
                          "delle app sapeva dirti quali sessioni fossero aperte, né chiuderne una.",
        "orcid_taken_title": "ORCID già collegato",
        "orcid_taken_body": "Quell'ORCID iD è già associato a un altro account. Scrivi a un "
                            "amministratore.",
        "orcid_fail_title": "Accesso ORCID non riuscito",
        "orcid_fail_body": "La richiesta è scaduta o non corrisponde. Riprova.",
        "orcid_err_unconfigured": "ORCID non è configurato su questo server.",
        "orcid_err_unreachable": "Non siamo riusciti a raggiungere ORCID. Riprova fra poco.",
        "orcid_err_rejected": "ORCID ha rifiutato lo scambio. Riprova; se ricapita, segnalalo a "
                              "un amministratore.",
        "orcid_err_unreadable": "La risposta di ORCID è illeggibile. Segnalalo a un amministratore.",
        "orcid_err_no_id": "ORCID non ha restituito un iD. Segnalalo a un amministratore.",
        "orcid_unknown_title": "Nessun account collegato",
        "orcid_unknown_body": "Quell'ORCID iD non è collegato a nessun account qui. Chiedi un "
                              "invito, e potrai accettarlo proprio con ORCID.",

        # registrazione aperta
        "login_register": "Non hai un account? Registrati",
        "register_title": "Crea un account",
        "register_sub": "Registrarsi non dà accesso a niente: l'account nasce vuoto, e l'accesso alle app si chiede dopo.",
        "register_btn": "Registrati",
        "register_have": "Hai già un account? Accedi",
        "register_domains": "Sono ammessi solo gli indirizzi di:",
        "reg_closed_title": "Registrazioni chiuse",
        "reg_closed_body": "Al momento non è possibile registrarsi da soli. Chiedi un invito a un amministratore.",
        "reg_bad_email": "Indirizzo email non valido.",
        "reg_bad_domain": "Questo indirizzo non è fra i domini ammessi.",
        "reg_taken": "Esiste già un account con questa email. Prova ad accedere, o a reimpostare la password.",
        "reg_confirmed_title": "Indirizzo confermato",
        "reg_confirmed_body": "Grazie. Ora puoi chiedere l'accesso alle app dalla tua pagina iniziale.",
        "req_unverified_title": "Conferma prima l'email",
        "req_unverified_body": "Per chiedere l'accesso a un'app serve un indirizzo confermato. Controlla la posta, o chiedi a un amministratore di rimandarti il link.",
        "req_sent_title": "Richiesta inviata",
        "req_sent_body": "Un amministratore la vedrà e deciderà. Riceverai una mail quando è fatta.",
        "home_unverified": "Il tuo indirizzo non è ancora confermato: fino ad allora non puoi chiedere l'accesso alle app.",
        "home_others": "Altre app",
        "home_others_sub": "Non hai accesso a queste. Puoi chiederlo.",
        "home_request": "Chiedi accesso",
        "home_pending": "richiesta in attesa",
        "home_why": "perché ti serve (facoltativo)",

        # ── /admin ───────────────────────────────────────────────────────────────
        "fmt_date": "%d/%m/%Y",
        "fmt_datetime_sec": "%d/%m %H:%M:%S",
        "adm_in_page": "In questa pagina",
        "adm_col_when": "Quando",
        "adm_col_who": "Chi",
        "adm_col_event": "Evento",
        "adm_col_detail": "Dettaglio",
        "adm_col_user": "Utente",
        "adm_col_expires": "Scade",
        "adm_col_outcome": "Esito",
        "adm_col_why": "Perché",
        "adm_col_recipient": "Destinatario",
        "adm_col_created": "Creato",
        "adm_col_by": "Da",
        "adm_col_prefix": "Prefisso",
        "adm_col_elevation": "Elevazione valida (min)",
        "adm_col_note": "Nota",
        "adm_back_users": "Torna agli utenti",
        "adm_back_config": "Torna alla configurazione",
        "adm_lvl_two": "due",
        "adm_lvl_one": "uno",
        "adm_deactivate": "Disattiva",
        "adm_reactivate": "Riattiva",
        "adm_audit_sub": "Ultimi 400 eventi.",
        "adm_audit_ph": "filtra per evento: login, grant, 2fa, verify…",
        "adm_audit_filter": "Filtra",
        "adm_audit_note": "<code>verify.unknown_host</code> significa che una "
                          "richiesta è arrivata dal gate per un host che non è "
                          "registrato qui: è un errore di configurazione in "
                          "Caddy, e il gate ha chiuso la porta.",
        "adm_sessions_title": "Sessioni attive",
        "adm_sessions_sub": "Tutte le sessioni vive del perimetro, e il bottone "
                            "per chiuderle. Fino a oggi questa pagina non poteva"
                            " esistere: le app portano JWT stateless, che "
                            "nessuno può revocare.",
        "adm_sessions_note": "Una revoca ha effetto entro trenta secondi, che è "
                             "la durata della cache davanti al database. La "
                             "cache viene svuotata subito per l'utente toccato, "
                             "quindi in pratica è immediata; i trenta secondi "
                             "sono il caso peggiore con più worker.",
        "adm_batch_title": "Creazione in blocco",
        "adm_batch_sub": "%(n)s righe elaborate, modalità",
        "adm_batch_pw_b": "Le password compaiono solo adesso.",
        "adm_batch_pw": "Copiale prima di lasciare questa pagina: sono hashate "
                        "nel database e non c'è modo di rileggerle. Chi le perde"
                        " passa dal reset.",
        "adm_batch_col_link": "Link (se la mail non è partita)",
        "adm_batch_r_existing": "già presente, grant aggiornati",
        "adm_batch_r_created": "account creato",
        "adm_batch_r_invited": "invito inviato",
        "adm_batch_r_mail_failed": "mail non partita",
        "adm_del_title": "Cancella %(who)s",
        "adm_del_h": "Cancellare %(who)s?",
        "adm_del_cannot": "Non si può.",
        "adm_del_block_no_user": "Utente inesistente.",
        "adm_del_block_self": "Non puoi cancellare il tuo stesso account.",
        "adm_del_block_last_admin": "È l'ultimo amministratore attivo. Nominane "
                                    "un altro prima, o resti fuori tu.",
        "adm_del_err_confirm": "Riscrivi esattamente l'indirizzo per confermare.",
        "adm_del_h_what": "Cosa succede qui",
        "adm_del_l1": "L'account sparisce, e con lui <strong>%(n)s</strong> "
                      "grant, i codici di backup e il secondo fattore.",
        "adm_del_l2_one": "<strong>%(n)s</strong> sessione aperta viene chiusa "
                          "subito.",
        "adm_del_l2_many": "<strong>%(n)s</strong> sessioni aperte vengono "
                           "chiuse subito.",
        "adm_del_l3": "<strong>%(n)s</strong> righe di log "
                      "<strong>restano</strong>, slegate dall'utente e ripulite "
                      "dall'indirizzo. Un log che sparisce insieme a chi ha "
                      "agito non è un log.",
        "adm_del_l4": "L'evento viene registrato con il <span "
                      "class=\"mono\">subject</span>, non con l'email: tenerla lì "
                      "significherebbe cancellare l'indirizzo da ogni riga "
                      "tranne quella che dice che è stato cancellato.",
        "adm_del_h_notwhat": "Cosa <em>non</em> succede",
        "adm_del_apps_b": "Le app non vengono toccate.",
        "adm_del_apps": "Se questa persona è già entrata da qualche parte, lì è "
                        "rimasto un profilo locale con il suo <span "
                        "class=\"mono\">borant_sub</span> ormai orfano — e con "
                        "dentro il suo lavoro, il suo nome e il suo indirizzo. "
                        "Per una cancellazione vera devi passare da ognuna.",
        "adm_del_had": "Aveva accesso a:",
        "adm_del_local": "crea profili locali",
        "adm_del_nogrant": "Nessun grant: se non è mai entrata da nessuna parte,"
                           " non c'è altro da ripulire. Controlla comunque le "
                           "app aperte a tutti gli autenticati.",
        "adm_del_h_confirm": "Conferma",
        "adm_del_retype": "Riscrivi %(email)s per confermare",
        "adm_del_note": "Si riscrive a mano di proposito: in un elenco di trenta"
                        " studenti un bottone rosso accanto al nome sbagliato è "
                        "un incidente che aspetta. Se volevi solo togliere "
                        "l'accesso, <strong>disattiva</strong> invece: è "
                        "reversibile e conserva tutto.",
        "adm_del_btn": "Cancella definitivamente",
        "adm_msg_title_sent": "Messaggio inviato",
        "adm_msg_title_confirm": "Conferma invio",
        "adm_msg_sent_h": "Inviato a %(ok)s su %(tot)s",
        "adm_msg_subject_l": "Oggetto",
        "adm_msg_recipients_l": "destinatari",
        "adm_msg_partial": "Qualcuna non è partita. Se l'errore parla di limite,"
                           " è la finestra scorrevole di 24 ore di Infomaniak: i"
                           " destinatari si contano uno per uno, e gli slot si "
                           "liberano ventiquattro ore dopo ciascun invio, non a "
                           "mezzanotte.",
        "adm_msg_all_ok": "Tutte partite.",
        "adm_msg_r_ok": "inviata",
        "adm_msg_about_one": "Stai per scrivere a %(n)s persona",
        "adm_msg_about_many": "Stai per scrivere a %(n)s persone",
        "adm_msg_send_one": "Manda a %(n)s persona",
        "adm_msg_send_many": "Manda a %(n)s persone",
        "adm_msg_limit_b": "%(n)s destinatari.",
        "adm_msg_limit": "Il limite Infomaniak è 200 o 500 ogni 24 ore secondo "
                         "il piano, e i destinatari si contano uno per uno: con "
                         "questo invio ne consumi %(n)s. La finestra è "
                         "scorrevole, quindi gli slot tornano poco a poco e non "
                         "tutti a mezzanotte.",
        "adm_msg_h_message": "Il messaggio",
        "adm_msg_placeholders": "<code>{nome}</code> e <code>{email}</code> "
                                "vengono sostituiti per ogni destinatario. Il "
                                "testo parte in chiaro, senza HTML.",
        "adm_msg_h_towhom": "A chi",
        "adm_msg_one_each_b": "Una mail per persona, non una in copia nascosta.",
        "adm_msg_one_each": "Così nessuno vede gli indirizzi degli altri, e se "
                            "qualcuna fallisce sai quale. In BCC non si "
                            "risparmierebbe nulla comunque: il conto dei "
                            "destinatari è lo stesso.",
        "adm_msg_pb_subject": "Servono un oggetto e un testo.",
        "adm_msg_pb_norecipients": "Nessun destinatario con questa selezione.",
        "adm_msg_pb_smtpoff": "SMTP non è attivo: la mail non partirebbe.",
        "adm_rcp_all": "tutti gli utenti attivi",
        "adm_rcp_grant": "chi ha un grant su %(app)s",
        "adm_rcp_single": "un utente solo",
        "adm_rcp_bad": "selezione non valida",
        "adm_rcp_noapp": "app inesistente",
        "adm_mail_smtp_off": "SMTP non attivo: configuralo in /admin/config",
        "adm_mail_smtp_incomplete": "SMTP incompleto: mancano host o indirizzo "
                                    "mittente",
        "adm_mail_no_recipient": "Nessun destinatario",
        "adm_mail_auth_refused": "Autenticazione SMTP rifiutata. Su Infomaniak "
                                 "serve la password della casella; con Gmail una"
                                 " app password; su Microsoft 365 il tenant "
                                 "potrebbe avere SMTP AUTH disabilitato.",
        "adm_cfg_sub": "Il relay SMTP si imposta qui e non nell'ambiente: la "
                       "casella non si conosce al momento del deploy. Le chiavi "
                       "(JWT, Fernet, ORCID) restano dove sono, cioè fuori dalla"
                       " portata di un form.",
        "adm_cfg_h_general": "Generale",
        "adm_cfg_name": "Nome",
        "adm_cfg_url": "URL pubblico",
        "adm_cfg_url_note": "L'URL pubblico finisce nei link degli inviti e nei "
                            "redirect verso ORCID: se è sbagliato, il flusso "
                            "ORCID smette di funzionare.",
        "adm_cfg_h_reg": "Registrazione",
        "adm_cfg_reg_open": "registrazione aperta a chiunque",
        "adm_cfg_domains": "Domini ammessi (separati da virgola, vuoto = tutti)",
        "adm_cfg_reg_note": "Aprire le registrazioni <strong>non apre nessuna "
                            "app</strong>: un account nuovo nasce con zero grant"
                            " e non raggiunge niente, quindi chi si registra "
                            "ottiene il diritto di <em>chiedere</em>, non di "
                            "entrare. Quello che cambia è che la tabella utenti "
                            "si riempie di chiunque passi, e le richieste vanno "
                            "smaltite. Governa anche ORCID: a registrazioni "
                            "aperte, «entra con ORCID» crea l'account se non "
                            "esiste — sempre senza grant.",
        "adm_cfg_enabled": "attivo",
        "adm_cfg_host": "Host",
        "adm_cfg_port": "Porta",
        "adm_cfg_security": "Sicurezza",
        "adm_cfg_user": "Utente",
        "adm_cfg_pw_set": "impostata",
        "adm_cfg_pw_keep": "lascia vuoto per non cambiarla",
        "adm_cfg_pw_clear": "cancella",
        "adm_cfg_from": "Mittente",
        "adm_cfg_fromname": "Nome mittente",
        "adm_cfg_h_test": "Prova di invio",
        "adm_cfg_test_btn": "Manda una mail di prova",
        "adm_cfg_h_write": "Scrivi agli utenti",
        "adm_cfg_opt_all": "Tutti gli utenti attivi (%(n)s)",
        "adm_cfg_opt_grant": "Chi ha un grant su %(app)s",
        "adm_cfg_opt_one": "Solo %(who)s",
        "adm_cfg_body": "Testo",
        "adm_cfg_body_ph": "Ciao {nome},",
        "adm_cfg_msg_note": "<code>{nome}</code> e <code>{email}</code> vengono "
                            "sostituiti per ogni destinatario. Testo semplice, "
                            "niente HTML. Parte <strong>una mail per "
                            "persona</strong>, mai una in copia nascosta: "
                            "nessuno vede gli indirizzi degli altri, e se "
                            "qualcuna fallisce sai quale. Solo utenti registrati"
                            " — qui non c'è un campo per indirizzi liberi, di "
                            "proposito.",
        "adm_cfg_preview_btn": "Vedi chi riceve, poi conferma",
        "adm_cfg_traps_b": "Due trappole note.",
        "adm_cfg_traps": "Con Gmail serve l'autenticazione a due fattori attiva "
                         "sull'account più una <em>app password</em> "
                         "(<code>smtp.gmail.com:587</code>, STARTTLS): la "
                         "password normale viene rifiutata. Su Microsoft 365 "
                         "molti tenant hanno <strong>SMTP AUTH disabilitato per "
                         "default</strong>, e in quel caso serve "
                         "l'amministratore del tenant: nessuna configurazione "
                         "qui può aggirarlo.<br><br>In ogni caso la mail resta "
                         "una dipendenza <em>degradabile</em>: se il relay è "
                         "giù, gli inviti mostrano il link da copiare a mano "
                         "invece di fallire.",
        "adm_cfg_msg_saved": "Configurazione salvata",
        "adm_cfg_msg_test": "Mail di prova inviata a %(to)s",
        "adm_apps_title": "App e policy",
        "adm_apps_sub": "Qui si decide <em>che livello serve su quale path</em>."
                        " Se un path passi dal gate oppure resti pubblico lo "
                        "decide Caddy, non questa pagina: sono due domande con "
                        "due proprietari.",
        "adm_apps_nav_register": "Registra",
        "adm_apps_h_register": "Registra un'app",
        "adm_apps_slug": "Slug",
        "adm_apps_access": "Accesso",
        "adm_apps_acc_grant": "solo chi ha un grant",
        "adm_apps_acc_any": "chiunque sia autenticato",
        "adm_apps_desc": "Descrizione",
        "adm_apps_roles_l": "Ruoli usati da questa app (separati da virgola, "
                            "facoltativo)",
        "adm_apps_roles_ph": "es. free, full, admin",
        "adm_apps_h_list": "App registrate",
        "adm_apps_off": "disattivata",
        "adm_apps_open_all": "aperta a tutti gli autenticati",
        "adm_apps_2f_paths": "%(n)s path a due fattori",
        "adm_apps_require_grant": "Richiedi grant",
        "adm_apps_open_all_btn": "Apri a tutti",
        "adm_apps_h_roles": "Ruoli",
        "adm_apps_roles_ph2": "vuoto = questa app non ha ruoli, e il campo "
                              "sparisce dalle form",
        "adm_apps_save_roles": "Salva ruoli",
        "adm_apps_roles_note": "Riempie il menu del campo «ruolo suggerito» "
                               "nella form degli inviti e dei grant, e basta: il"
                               " gate non li interpreta e non li impone, perché "
                               "il vocabolario di dominio è dell'app. "
                               "<strong>Vuoto è una risposta</strong>, non una "
                               "dimenticanza — per le app che hanno un booleano "
                               "invece dei ruoli il campo non compare affatto, "
                               "così non c'è niente da ricordare e niente da "
                               "sbagliare. Si riempie al momento di gatare "
                               "l'app, leggendo il vocabolario vero dal suo "
                               "codice.",
        "adm_apps_h_policy": "Policy per path",
        "adm_apps_remove": "Togli",
        "adm_apps_maxage_ph": "vuoto = tutta la sessione",
        "adm_apps_save_policy": "Salva policy",
        "adm_apps_policy_note": "Vince il prefisso più lungo che combacia, "
                                "confrontato su path normalizzato e in "
                                "minuscolo.",
        "adm_users_sub": "Chi esiste, e a quali app può entrare.",
        "adm_users_nav_requests": "Richieste",
        "adm_users_nav_invite": "Invita",
        "adm_users_nav_batch": "In blocco",
        "adm_users_nav_pending": "Inviti aperti",
        "adm_users_nav_people": "Persone",
        "adm_users_mailfail_b": "La mail non è partita:",
        "adm_users_mailfail": "Il link d'invito è comunque valido — passalo a "
                              "mano:",
        "adm_users_pwok": "Password di <strong>%(who)s</strong> cambiata. Le sue"
                          " sessioni aperte sono state chiuse, e gliel'abbiamo "
                          "scritto.",
        "adm_users_pwerr": "Password di <strong>%(who)s</strong> "
                           "<strong>non</strong> cambiata: ne servono almeno "
                           "dieci caratteri.",
        "adm_users_h_requests": "Richieste di accesso (%(n)s)",
        "adm_users_unverified": "email non confermata",
        "adm_users_approve": "Approva",
        "adm_users_deny": "Rifiuta",
        "adm_users_req_note": "Il ruolo si sceglie <strong>qui</strong>, "
                              "approvando, non quando la richiesta viene fatta: "
                              "è l'unico momento in cui si sa cosa concedere. "
                              "Per un'app che spende — ArguMap paga le chiamate "
                              "LLM dalla chiave del server — concedere per "
                              "inerzia un ruolo che sblocca la pipeline apre un "
                              "rubinetto.",
        "adm_users_orcid_hint": "ORCID atteso (facoltativo)",
        "adm_users_is_admin": "amministratore",
        "adm_users_h_apps": "Accesso alle app",
        "adm_users_role_hint": "Ruolo suggerito (X-Borant-Hint)",
        "adm_users_role_hint2": "Ruolo suggerito",
        "adm_users_noroles": "— questa app non ha ruoli",
        "adm_users_invite_btn": "Manda l'invito",
        "adm_users_people_l": "Una persona per riga — <span "
                              "class=\"mono\">email</span> oppure <span "
                              "class=\"mono\">email, Nome Cognome</span>",
        "adm_users_batch_note": "Accetta anche punto e virgola e tabulazioni, "
                                "perché è così che escono gli elenchi incollati "
                                "da un foglio. Le righe vuote e quelle che "
                                "iniziano con <span class=\"mono\">#</span> si "
                                "saltano, i doppioni pure. Chi ha già un account"
                                " non viene toccato: gli si aggiungono solo i "
                                "grant mancanti, così un batch rilanciato per "
                                "sbaglio non azzera niente.",
        "adm_users_h_how": "Come",
        "adm_users_mode_invite": "manda un invito: scelgono loro la password, e "
                                 "l'indirizzo risulta verificato",
        "adm_users_mode_create": "crea subito con password generate: compaiono "
                                 "una volta sola, da copiare",
        "adm_users_batch_btn": "Elabora",
        "adm_users_h_pending": "Inviti in attesa",
        "adm_users_deleted": "Utente cancellato. Ricorda che <strong>le app non "
                             "sono state toccate</strong>: il profilo locale è "
                             "ancora là dove era già entrato.",
        "adm_users_people_sub": "<strong>Disattiva</strong> è reversibile e "
                                "conserva tutto — è quasi sempre quello che "
                                "serve. <strong>Cancella</strong> è definitivo e"
                                " non tocca le app. <strong>Imposta</strong> una"
                                " password serve quando il reset per posta non è"
                                " una strada: un account condiviso di cui "
                                "nessuno legge la casella, un indirizzo che "
                                "rimbalza, una password generata e persa. Chiude"
                                " tutte le sessioni di quella persona e gliela "
                                "manda a dire.",
        "adm_users_badge_admin": "admin",
        "adm_users_badge_off": "disattivato",
        "adm_users_badge_everywhere": "entra ovunque",
        "adm_users_badge_napps": "%(n)s app",
        "adm_users_badge_noaccess": "nessun accesso",
        "adm_users_admin_off": "Togli admin",
        "adm_users_admin_on": "Rendi admin",
        "adm_users_pw_confirm": "Cambiare la password di %(email)s? Le sue "
                                "sessioni aperte verranno chiuse e riceverà una "
                                "mail.",
        "adm_users_pw_ph": "nuova password",
        "adm_users_pw_btn": "Imposta",
        "adm_users_reset2fa": "Azzera 2FA",
        "adm_users_delete_link": "Cancella…",
        "adm_users_open_all": "aperta a tutti",
        "adm_users_offlist": "fuori lista",
        "adm_users_offlist_title": "Non è fra i ruoli dichiarati per questa app",
        "adm_users_norole": "nessun ruolo dichiarato",
        "adm_users_update": "Aggiorna",
        "adm_users_give": "Concedi",
        "adm_users_revoke": "Revoca",
        "plural_zero_singular": "",
        "adm_batch_sub_one": "%(n)s riga elaborata, modalità",
        "adm_del_l1_one": "L'account sparisce, e con lui "
                          "<strong>%(n)s</strong> grant, i codici di backup e "
                          "il secondo fattore.",
        "adm_del_l3_one": "<strong>%(n)s</strong> riga di log "
                          "<strong>resta</strong>, slegata dall'utente e "
                          "ripulita dall'indirizzo. Un log che sparisce "
                          "insieme a chi ha agito non è un log.",
        "adm_users_badge_napps_one": "%(n)s app",
        "adm_apps_2f_paths_one": "%(n)s path a due fattori",
    },

    # ── ENGLISH ───────────────────────────────────────────────────────────────
    "en": {
        "nav_profile": "Profile",
        "nav_users": "Users",
        "nav_apps": "Apps",
        "nav_sessions": "Sessions",
        "nav_log": "Log",
        "nav_config": "Configuration",
        "nav_logout": "Sign out",
        "logout_title": "Sign out of Borant ID?",
        "logout_sub": "This ends your session here and in every tool behind this sign-in, not only the one you came from.",
        "logout_confirm": "Sign out",
        "logout_cancel": "Cancel",
        "tagline": "Single sign-on for the research tools",

        "email": "Email",
        "password": "Password",
        "back": "Go back",
        "save": "Save",
        "fmt_datetime": "%d %b %Y %H:%M",
        "fmt_datetime_short": "%d %b %H:%M",

        "login_title": "Sign in",
        "login_sub": "One way in for every tool on borant.eu.",
        "login_enter": "Sign in",
        "login_forgot": "Forgot your password",
        "login_err": "Wrong email or password.",
        "login_rate": "Too many attempts. Try again in fifteen minutes.",
        "login_orcid": "Sign in with ORCID",
        "login_orcid_note": "This works if your ORCID is already linked to an account here. If it "
                            "is not, ask for an invitation — you can accept it with ORCID.",
        "cookie_trouble_title": "The session cookie is not sticking.",
        "cookie_trouble_body": "You appear to be signed in, but your browser is not sending the "
                               "session back. Usually that means blocked cookies, a badly wrong "
                               "clock, or a misconfigured cookie domain. Try signing in again; if "
                               "it happens twice, tell an administrator rather than retrying.",

        "twofa_title": "Second factor",
        "twofa_sub": "This destination asks for one more check. You are not signing in again: "
                     "the session you already have is being raised.",
        "twofa_code": "Code from your authenticator app",
        "twofa_verify": "Verify",
        "twofa_backup_note": "A backup code also works, in the form <code>abcd-1234</code>.",
        "twofa_err": "Invalid code.",
        "twofa_err_retry": "Invalid code. Try again.",
        "twofa_rate": "Too many attempts. Wait a few minutes.",

        "enroll_title": "Set up your second factor",
        "enroll_sub": "The destination you asked for requires two factors and you do not have one "
                      "yet. You can set it up right here: you are already signed in, so this is "
                      "not a dead end.",
        "enroll_qr_alt": "QR code for your authenticator app",
        "enroll_manual": "Or enter this key by hand",
        "enroll_apps": "Any TOTP app will do: Ente Auth, Aegis, Google Authenticator.",
        "enroll_confirm": "Confirm with the code your app is showing now",
        "enroll_activate": "Activate",
        "enroll_note": "The key is only stored once a code has proved your app really has it.",

        "codes_title": "Backup codes",
        "codes_sub": "Ten codes, each usable once, instead of the app code when you do not have "
                     "your phone. <strong>You will not see them again.</strong>",
        "codes_invalidated": "Any previous codes have been invalidated.",
        "codes_done": "Done, they are somewhere safe",

        "home_hello": "Hello",
        "home_sub": "The tools you have access to.",
        "home_col_app": "Tool",
        "home_col_address": "Address",
        "home_open": "Open",
        "home_empty": "No tools are linked to your account. If you think one should be, ask an "
                      "administrator.",
        "home_note": "From your profile you can change your password, turn on the second factor, "
                     "link ORCID and close open sessions.",

        "forbidden_title": "You do not have access to this tool",
        "forbidden_sub": "You are signed in correctly. It is access to this address that your "
                         "account does not have.",
        "forbidden_ask": "Request access",
        "forbidden_mine": "My tools",
        "forbidden_sent_title": "Request sent",
        "forbidden_sent_body": "The administrators have been notified.",
        "gate_unknown_host": "This address is not registered in Borant ID. Nothing is "
                             "missing from your account: it is the gate's configuration. "
                             "Tell an administrator.",

        "invite_title": "Activate your account",
        "invite_for": "Invitation for",
        "invite_name": "Name",
        "invite_pw": "Password (at least 10 characters)",
        "invite_pw2": "Repeat the password",
        "invite_activate": "Activate",
        "invite_err": "The password must be at least 10 characters, and both copies must match.",
        "invite_orcid_note": "You can link your ORCID right afterwards, from your profile. "
                             "Linking only happens from an already authenticated session — never "
                             "by matching email addresses.",
        "invite_bad_title": "Invitation not valid",
        "invite_bad_body": "The link has expired or has already been used. Ask for another one.",

        "reset_title": "Reset your password",
        "reset_sub": "We will send you a link valid for one hour.",
        "reset_send": "Send me the link",
        "reset_sent": "If that address has an account here, an email with the link is on its way. "
                      "It expires in an hour and works once.",
        "reset_privacy": "We do not tell you whether the address exists: that is not something a "
                         "form should reveal. If the email does not arrive, ask an administrator — "
                         "they can hand you the link directly.",
        "reset_back": "Back to sign in",
        "reset_new_title": "New password",
        "reset_new_sub": "Every open session will be closed.",
        "reset_err": "At least 10 characters, and both copies must match.",
        "reset_expired_title": "Link expired",
        "reset_expired_body": "This reset link is no longer valid. Ask for another one.",
        "reset_done_title": "Password updated",
        "reset_done_body": "Every open session has been closed. You can sign in with the new "
                           "password.",

        "profile_title": "Profile",
        "profile_pw": "Password",
        "profile_pw_current": "Current password",
        "profile_pw_new": "New",
        "profile_pw_repeat": "Repeat",
        "profile_pw_change": "Change",
        "profile_pw_note": "Changing your password closes every other session, this one excepted.",
        "profile_pw_err": "Current password is wrong.",
        "profile_pw_short": "At least 10 characters, and both copies must match.",
        "profile_2fa": "Second factor",
        "profile_2fa_on": "On",
        "profile_2fa_off": "Off",
        "profile_2fa_codes": "Backup codes not yet used:",
        "profile_2fa_regen": "Generate new backup codes",
        "profile_2fa_always_on": "Ask me at every sign-in",
        "profile_2fa_always_off": "Stop asking at every sign-in",
        "profile_2fa_disable": "Turn off",
        "profile_2fa_note": "It is not required in general, but some tools ask for it: when you "
                            "open one of those, you are offered the setup on the spot.",
        "profile_2fa_activate": "Set it up now",
        "profile_2fa_msg": "Two-factor authentication is on. Generate your backup codes and put "
                           "them somewhere safe.",
        "profile_orcid": "ORCID",
        "profile_orcid_linked": "Linked:",
        "profile_orcid_one": "ORCID counts as <strong>one factor only</strong>: its token does not "
                             "reliably say whether you passed their own two-step check, so tools "
                             "that ask for two factors still need the code from here.",
        "profile_orcid_note": "Linking it lets you sign in with ORCID instead of a password.",
        "profile_orcid_link": "Link my ORCID",
        "profile_orcid_none": "ORCID is not configured on this server yet.",
        "profile_sessions": "Open sessions",
        "profile_s_opened": "Opened",
        "profile_s_last": "Last seen",
        "profile_s_origin": "Origin",
        "profile_s_level": "Level",
        "profile_s_this": "this one",
        "profile_s_two": "two factors",
        "profile_s_one": "one factor",
        "profile_s_close": "Close",
        "profile_s_close_all": "Close all, including this one",
        "profile_s_note": "This list is why Borant ID exists: until today not one of the tools "
                          "could tell you which sessions were open, let alone close one.",
        "orcid_taken_title": "ORCID already linked",
        "orcid_taken_body": "That ORCID iD already belongs to another account. Write to an "
                            "administrator.",
        "orcid_fail_title": "ORCID sign-in failed",
        "orcid_fail_body": "The request expired or did not match. Try again.",
        "orcid_err_unconfigured": "ORCID is not configured on this server.",
        "orcid_err_unreachable": "We could not reach ORCID. Try again shortly.",
        "orcid_err_rejected": "ORCID refused the exchange. Try again; if it happens twice, tell "
                              "an administrator.",
        "orcid_err_unreadable": "The answer from ORCID was unreadable. Tell an administrator.",
        "orcid_err_no_id": "ORCID did not return an iD. Tell an administrator.",
        "orcid_unknown_title": "No account linked",
        "orcid_unknown_body": "That ORCID iD is not linked to any account here. Ask for an "
                              "invitation — you will be able to accept it with ORCID.",

        "login_register": "No account? Register",
        "register_title": "Create an account",
        "register_sub": "Registering gives you access to nothing: the account starts empty, and access to tools is requested afterwards.",
        "register_btn": "Register",
        "register_have": "Already have an account? Sign in",
        "register_domains": "Only addresses from these domains are accepted:",
        "reg_closed_title": "Registration closed",
        "reg_closed_body": "Self-registration is not open at the moment. Ask an administrator for an invitation.",
        "reg_bad_email": "That email address is not valid.",
        "reg_bad_domain": "That address is not in an accepted domain.",
        "reg_taken": "An account with this email already exists. Try signing in, or resetting the password.",
        "reg_confirmed_title": "Address confirmed",
        "reg_confirmed_body": "Thank you. You can now request access to tools from your home page.",
        "req_unverified_title": "Confirm your email first",
        "req_unverified_body": "Requesting access needs a confirmed address. Check your inbox, or ask an administrator to send the link again.",
        "req_sent_title": "Request sent",
        "req_sent_body": "An administrator will see it and decide. You will get an email once they have.",
        "home_unverified": "Your address is not confirmed yet: until it is, you cannot request access to tools.",
        "home_others": "Other tools",
        "home_others_sub": "You do not have access to these. You can ask for it.",
        "home_request": "Request access",
        "home_pending": "request pending",
        "home_why": "why you need it (optional)",

        # ── /admin ───────────────────────────────────────────────────────────────
        "fmt_date": "%d %b %Y",
        "fmt_datetime_sec": "%d %b %H:%M:%S",
        "adm_in_page": "On this page",
        "adm_col_when": "When",
        "adm_col_who": "Who",
        "adm_col_event": "Event",
        "adm_col_detail": "Detail",
        "adm_col_user": "User",
        "adm_col_expires": "Expires",
        "adm_col_outcome": "Outcome",
        "adm_col_why": "Why",
        "adm_col_recipient": "Recipient",
        "adm_col_created": "Created",
        "adm_col_by": "By",
        "adm_col_prefix": "Prefix",
        "adm_col_elevation": "Elevation valid (min)",
        "adm_col_note": "Note",
        "adm_back_users": "Back to users",
        "adm_back_config": "Back to configuration",
        "adm_lvl_two": "two",
        "adm_lvl_one": "one",
        "adm_deactivate": "Deactivate",
        "adm_reactivate": "Reactivate",
        "adm_audit_sub": "The last 400 events.",
        "adm_audit_ph": "filter by event: login, grant, 2fa, verify…",
        "adm_audit_filter": "Filter",
        "adm_audit_note": "<code>verify.unknown_host</code> means a request "
                          "arrived from the gate for a host that is not "
                          "registered here: it is a configuration mistake in "
                          "Caddy, and the gate closed the door.",
        "adm_sessions_title": "Active sessions",
        "adm_sessions_sub": "Every live session in the perimeter, and the button"
                            " that closes them. Until today this page could not "
                            "exist: the tools carry stateless JWTs, which nobody"
                            " can revoke.",
        "adm_sessions_note": "A revocation takes effect within thirty seconds, "
                             "which is how long the cache in front of the "
                             "database lives. The cache is flushed immediately "
                             "for the user touched, so in practice it is "
                             "instant; the thirty seconds are the worst case "
                             "with several workers.",
        "adm_batch_title": "Bulk creation",
        "adm_batch_sub": "%(n)s rows processed, mode",
        "adm_batch_pw_b": "The passwords appear only now.",
        "adm_batch_pw": "Copy them before you leave this page: they are hashed "
                        "in the database and there is no way to read them back. "
                        "Whoever loses one goes through the reset.",
        "adm_batch_col_link": "Link (if the email did not go out)",
        "adm_batch_r_existing": "already there, grants updated",
        "adm_batch_r_created": "account created",
        "adm_batch_r_invited": "invitation sent",
        "adm_batch_r_mail_failed": "email did not go out",
        "adm_del_title": "Delete %(who)s",
        "adm_del_h": "Delete %(who)s?",
        "adm_del_cannot": "Not possible.",
        "adm_del_block_no_user": "No such user.",
        "adm_del_block_self": "You cannot delete your own account.",
        "adm_del_block_last_admin": "This is the last active administrator. "
                                    "Appoint another one first, or you lock "
                                    "yourself out.",
        "adm_del_err_confirm": "Retype the address exactly to confirm.",
        "adm_del_h_what": "What happens here",
        "adm_del_l1": "The account disappears, and with it "
                      "<strong>%(n)s</strong> grants, the backup codes and the "
                      "second factor.",
        "adm_del_l2_one": "<strong>%(n)s</strong> open session is closed at "
                          "once.",
        "adm_del_l2_many": "<strong>%(n)s</strong> open sessions are closed at "
                           "once.",
        "adm_del_l3": "<strong>%(n)s</strong> log rows <strong>stay</strong>, "
                      "detached from the user and stripped of the address. A log"
                      " that disappears along with whoever acted is not a log.",
        "adm_del_l4": "The event is recorded with the <span "
                      "class=\"mono\">subject</span>, not the email: keeping it "
                      "there would mean erasing the address from every row "
                      "except the one that says it was erased.",
        "adm_del_h_notwhat": "What does <em>not</em> happen",
        "adm_del_apps_b": "The tools are not touched.",
        "adm_del_apps": "If this person has signed in anywhere, a local profile "
                        "stayed behind there with a now orphaned <span "
                        "class=\"mono\">borant_sub</span> — and their work, their "
                        "name and their address inside it. A real deletion means"
                        " going through each one.",
        "adm_del_had": "They had access to:",
        "adm_del_local": "creates local profiles",
        "adm_del_nogrant": "No grants: if they never signed in anywhere, there "
                           "is nothing else to clean up. Check the tools open to"
                           " every authenticated user all the same.",
        "adm_del_h_confirm": "Confirm",
        "adm_del_retype": "Retype %(email)s to confirm",
        "adm_del_note": "You retype it by hand on purpose: in a list of thirty "
                        "students a red button next to the wrong name is an "
                        "accident waiting. If all you wanted was to take access "
                        "away, <strong>deactivate</strong> instead: that is "
                        "reversible and keeps everything.",
        "adm_del_btn": "Delete permanently",
        "adm_msg_title_sent": "Message sent",
        "adm_msg_title_confirm": "Confirm sending",
        "adm_msg_sent_h": "Sent to %(ok)s of %(tot)s",
        "adm_msg_subject_l": "Subject",
        "adm_msg_recipients_l": "recipients",
        "adm_msg_partial": "Some did not go out. If the error mentions a limit, "
                           "it is Infomaniak's rolling 24-hour window: "
                           "recipients are counted one by one, and slots free up"
                           " twenty-four hours after each send, not at midnight.",
        "adm_msg_all_ok": "All went out.",
        "adm_msg_r_ok": "sent",
        "adm_msg_about_one": "You are about to write to %(n)s person",
        "adm_msg_about_many": "You are about to write to %(n)s people",
        "adm_msg_send_one": "Send to %(n)s person",
        "adm_msg_send_many": "Send to %(n)s people",
        "adm_msg_limit_b": "%(n)s recipients.",
        "adm_msg_limit": "The Infomaniak limit is 200 or 500 every 24 hours "
                         "depending on the plan, and recipients are counted one "
                         "by one: this send uses %(n)s of them. The window is "
                         "rolling, so slots come back little by little and not "
                         "all at midnight.",
        "adm_msg_h_message": "The message",
        "adm_msg_placeholders": "<code>{nome}</code> and <code>{email}</code> "
                                "are substituted for each recipient. The text "
                                "goes out as plain text, no HTML.",
        "adm_msg_h_towhom": "To whom",
        "adm_msg_one_each_b": "One email per person, not one in blind copy.",
        "adm_msg_one_each": "That way nobody sees anybody else's address, and if"
                            " one fails you know which. BCC would save nothing "
                            "anyway: the recipient count is the same.",
        "adm_msg_pb_subject": "A subject and a body are both needed.",
        "adm_msg_pb_norecipients": "No recipients with this selection.",
        "adm_msg_pb_smtpoff": "SMTP is off: the mail would not go out.",
        "adm_rcp_all": "every active user",
        "adm_rcp_grant": "everyone with a grant on %(app)s",
        "adm_rcp_single": "one user only",
        "adm_rcp_bad": "selection not valid",
        "adm_rcp_noapp": "no such tool",
        "adm_mail_smtp_off": "SMTP is off: configure it in /admin/config",
        "adm_mail_smtp_incomplete": "SMTP incomplete: host or sender address "
                                    "missing",
        "adm_mail_no_recipient": "No recipient",
        "adm_mail_auth_refused": "SMTP authentication refused. Infomaniak wants "
                                 "the mailbox password; Gmail wants an app "
                                 "password; on Microsoft 365 the tenant may have"
                                 " SMTP AUTH disabled.",
        "adm_cfg_sub": "The SMTP relay is set here and not in the environment: "
                       "the mailbox is not known at deploy time. The keys (JWT, "
                       "Fernet, ORCID) stay where they are, that is, out of "
                       "reach of a form.",
        "adm_cfg_h_general": "General",
        "adm_cfg_name": "Name",
        "adm_cfg_url": "Public URL",
        "adm_cfg_url_note": "The public URL ends up in invitation links and in "
                            "the redirects to ORCID: if it is wrong, the ORCID "
                            "flow stops working.",
        "adm_cfg_h_reg": "Registration",
        "adm_cfg_reg_open": "registration open to anyone",
        "adm_cfg_domains": "Accepted domains (comma-separated, empty = all)",
        "adm_cfg_reg_note": "Opening registration <strong>opens no "
                            "tool</strong>: a new account starts with zero "
                            "grants and reaches nothing, so whoever registers "
                            "earns the right to <em>ask</em>, not to enter. What"
                            " changes is that the users table fills up with "
                            "whoever passes by, and the requests have to be "
                            "worked through. It governs ORCID too: with "
                            "registration open, «sign in with ORCID» creates the"
                            " account if it does not exist — still with no "
                            "grants.",
        "adm_cfg_enabled": "on",
        "adm_cfg_host": "Host",
        "adm_cfg_port": "Port",
        "adm_cfg_security": "Security",
        "adm_cfg_user": "Username",
        "adm_cfg_pw_set": "set",
        "adm_cfg_pw_keep": "leave empty to keep it",
        "adm_cfg_pw_clear": "clear",
        "adm_cfg_from": "Sender",
        "adm_cfg_fromname": "Sender name",
        "adm_cfg_h_test": "Test send",
        "adm_cfg_test_btn": "Send a test email",
        "adm_cfg_h_write": "Write to the users",
        "adm_cfg_opt_all": "Every active user (%(n)s)",
        "adm_cfg_opt_grant": "Everyone with a grant on %(app)s",
        "adm_cfg_opt_one": "Only %(who)s",
        "adm_cfg_body": "Body",
        "adm_cfg_body_ph": "Hello {nome},",
        "adm_cfg_msg_note": "<code>{nome}</code> and <code>{email}</code> are "
                            "substituted for each recipient. Plain text, no "
                            "HTML. <strong>One email per person</strong> goes "
                            "out, never one in blind copy: nobody sees anybody "
                            "else's address, and if one fails you know which. "
                            "Registered users only — there is no field for free-"
                            "form addresses here, on purpose.",
        "adm_cfg_preview_btn": "See who receives it, then confirm",
        "adm_cfg_traps_b": "Two known traps.",
        "adm_cfg_traps": "Gmail needs two-factor authentication on the account "
                         "plus an <em>app password</em> "
                         "(<code>smtp.gmail.com:587</code>, STARTTLS): the "
                         "normal password is refused. On Microsoft 365 many "
                         "tenants have <strong>SMTP AUTH disabled by "
                         "default</strong>, and then it takes the tenant "
                         "administrator: no configuration here can get around "
                         "it.<br><br>Either way mail stays a <em>degradable</em>"
                         " dependency: if the relay is down, invitations show "
                         "the link to copy by hand instead of failing.",
        "adm_cfg_msg_saved": "Configuration saved",
        "adm_cfg_msg_test": "Test email sent to %(to)s",
        "adm_apps_title": "Tools and policies",
        "adm_apps_sub": "Here you decide <em>which level a path needs</em>. "
                        "Whether a path goes through the gate or stays public is"
                        " Caddy's decision, not this page's: two questions with "
                        "two owners.",
        "adm_apps_nav_register": "Register",
        "adm_apps_h_register": "Register a tool",
        "adm_apps_slug": "Slug",
        "adm_apps_access": "Access",
        "adm_apps_acc_grant": "only those with a grant",
        "adm_apps_acc_any": "anyone authenticated",
        "adm_apps_desc": "Description",
        "adm_apps_roles_l": "Roles this tool uses (comma-separated, optional)",
        "adm_apps_roles_ph": "e.g. free, full, admin",
        "adm_apps_h_list": "Registered tools",
        "adm_apps_off": "deactivated",
        "adm_apps_open_all": "open to anyone authenticated",
        "adm_apps_2f_paths": "%(n)s two-factor paths",
        "adm_apps_require_grant": "Require a grant",
        "adm_apps_open_all_btn": "Open to everyone",
        "adm_apps_h_roles": "Roles",
        "adm_apps_roles_ph2": "empty = this tool has no roles, and the field "
                              "disappears from the forms",
        "adm_apps_save_roles": "Save roles",
        "adm_apps_roles_note": "It fills the menu of the «suggested role» field "
                               "in the invitation and grant forms, and nothing "
                               "else: the gate does not interpret them and does "
                               "not impose them, because the domain vocabulary "
                               "belongs to the tool. <strong>Empty is an "
                               "answer</strong>, not an oversight — for tools "
                               "that have a boolean instead of roles the field "
                               "does not show up at all, so there is nothing to "
                               "remember and nothing to get wrong. You fill it "
                               "when you gate the tool, reading the real "
                               "vocabulary out of its code.",
        "adm_apps_h_policy": "Policies by path",
        "adm_apps_remove": "Remove",
        "adm_apps_maxage_ph": "empty = the whole session",
        "adm_apps_save_policy": "Save policy",
        "adm_apps_policy_note": "The longest matching prefix wins, compared on a"
                                " normalised, lowercased path.",
        "adm_users_sub": "Who exists, and which tools they can enter.",
        "adm_users_nav_requests": "Requests",
        "adm_users_nav_invite": "Invite",
        "adm_users_nav_batch": "In bulk",
        "adm_users_nav_pending": "Open invitations",
        "adm_users_nav_people": "People",
        "adm_users_mailfail_b": "The email did not go out:",
        "adm_users_mailfail": "The invitation link is valid all the same — hand "
                              "it over yourself:",
        "adm_users_pwok": "Password for <strong>%(who)s</strong> changed. Their "
                          "open sessions were closed, and we told them so.",
        "adm_users_pwerr": "Password for <strong>%(who)s</strong> "
                           "<strong>not</strong> changed: it takes at least ten "
                           "characters.",
        "adm_users_h_requests": "Access requests (%(n)s)",
        "adm_users_unverified": "email not confirmed",
        "adm_users_approve": "Approve",
        "adm_users_deny": "Deny",
        "adm_users_req_note": "The role is chosen <strong>here</strong>, on "
                              "approval, not when the request is made: this is "
                              "the only moment when you know what to grant. For "
                              "a tool that spends — ArguMap pays for the LLM "
                              "calls out of the server key — granting out of "
                              "inertia a role that unlocks the pipeline opens a "
                              "tap.",
        "adm_users_orcid_hint": "Expected ORCID (optional)",
        "adm_users_is_admin": "administrator",
        "adm_users_h_apps": "Access to the tools",
        "adm_users_role_hint": "Suggested role (X-Borant-Hint)",
        "adm_users_role_hint2": "Suggested role",
        "adm_users_noroles": "— this tool has no roles",
        "adm_users_invite_btn": "Send the invitation",
        "adm_users_people_l": "One person per line — <span "
                              "class=\"mono\">email</span> or <span "
                              "class=\"mono\">email, First Last</span>",
        "adm_users_batch_note": "Semicolons and tabs work too, because that is "
                                "how lists pasted out of a spreadsheet come. "
                                "Empty lines and lines starting with <span "
                                "class=\"mono\">#</span> are skipped, and so are "
                                "duplicates. Anyone who already has an account "
                                "is left alone: only the missing grants are "
                                "added, so a batch re-run by mistake zeroes "
                                "nothing.",
        "adm_users_h_how": "How",
        "adm_users_mode_invite": "send an invitation: they choose the password "
                                 "themselves, and the address comes out verified",
        "adm_users_mode_create": "create right away with generated passwords: "
                                 "they appear once, to be copied",
        "adm_users_batch_btn": "Process",
        "adm_users_h_pending": "Pending invitations",
        "adm_users_deleted": "User deleted. Remember that <strong>the tools were"
                             " not touched</strong>: the local profile is still "
                             "there, wherever they had already signed in.",
        "adm_users_people_sub": "<strong>Deactivate</strong> is reversible and "
                                "keeps everything — it is almost always what you"
                                " want. <strong>Delete</strong> is final and "
                                "does not touch the tools. <strong>Set</strong> "
                                "a password is for when reset by mail is not a "
                                "road: a shared account whose mailbox nobody "
                                "reads, an address that bounces, a generated "
                                "password that got lost. It closes all that "
                                "person's sessions and tells them so.",
        "adm_users_badge_admin": "admin",
        "adm_users_badge_off": "deactivated",
        "adm_users_badge_everywhere": "enters everywhere",
        "adm_users_badge_napps": "%(n)s tools",
        "adm_users_badge_noaccess": "no access",
        "adm_users_admin_off": "Remove admin",
        "adm_users_admin_on": "Make admin",
        "adm_users_pw_confirm": "Change the password for %(email)s? Their open "
                                "sessions will be closed and they will get an "
                                "email.",
        "adm_users_pw_ph": "new password",
        "adm_users_pw_btn": "Set",
        "adm_users_reset2fa": "Reset 2FA",
        "adm_users_delete_link": "Delete…",
        "adm_users_open_all": "open to everyone",
        "adm_users_offlist": "off the list",
        "adm_users_offlist_title": "Not among the roles declared for this tool",
        "adm_users_norole": "no role declared",
        "adm_users_update": "Update",
        "adm_users_give": "Grant",
        "adm_users_revoke": "Revoke",
        "plural_zero_singular": "",
        "adm_batch_sub_one": "%(n)s row processed, mode",
        "adm_del_l1_one": "The account disappears, and with it "
                          "<strong>%(n)s</strong> grant, the backup codes and "
                          "the second factor.",
        "adm_del_l3_one": "<strong>%(n)s</strong> log row "
                          "<strong>stays</strong>, detached from the user and "
                          "stripped of the address. A log that disappears "
                          "along with whoever acted is not a log.",
        "adm_users_badge_napps_one": "%(n)s tool",
        "adm_apps_2f_paths_one": "%(n)s two-factor path",
    },

    # ── DEUTSCH ───────────────────────────────────────────────────────────────
    "de": {
        "nav_profile": "Profil",
        "nav_users": "Benutzer",
        "nav_apps": "Anwendungen",
        "nav_sessions": "Sitzungen",
        "nav_log": "Protokoll",
        "nav_config": "Konfiguration",
        "nav_logout": "Abmelden",
        "logout_title": "Von Borant ID abmelden?",
        "logout_sub": "Damit endet die Sitzung hier und in allen Werkzeugen hinter diesem Zugang, nicht nur in dem, aus dem Sie kommen.",
        "logout_confirm": "Abmelden",
        "logout_cancel": "Abbrechen",
        "tagline": "Einheitlicher Zugang zu den Forschungswerkzeugen",

        "email": "E-Mail",
        "password": "Passwort",
        "back": "Zurück",
        "save": "Speichern",
        "fmt_datetime": "%d.%m.%Y %H:%M",
        "fmt_datetime_short": "%d.%m. %H:%M",

        "login_title": "Anmelden",
        "login_sub": "Ein Zugang für alle Werkzeuge auf borant.eu.",
        "login_enter": "Anmelden",
        "login_forgot": "Passwort vergessen",
        "login_err": "E-Mail oder Passwort ungültig.",
        "login_rate": "Zu viele Versuche. Bitte in einer Viertelstunde erneut versuchen.",
        "login_orcid": "Mit ORCID anmelden",
        "login_orcid_note": "Das funktioniert, wenn Ihre ORCID bereits mit einem Konto hier "
                            "verknüpft ist. Andernfalls bitten Sie um eine Einladung — Sie können "
                            "sie mit ORCID annehmen.",
        "cookie_trouble_title": "Das Sitzungs-Cookie bleibt nicht bestehen.",
        "cookie_trouble_body": "Sie gelten als angemeldet, aber Ihr Browser sendet die Sitzung "
                               "nicht zurück. Meist liegt es an blockierten Cookies, einer stark "
                               "falsch gestellten Uhr oder einer falsch konfigurierten "
                               "Cookie-Domain. Versuchen Sie es erneut; passiert es wieder, "
                               "wenden Sie sich an eine Administratorin oder einen Administrator, "
                               "statt es weiter zu versuchen.",

        "twofa_title": "Zweiter Faktor",
        "twofa_sub": "Dieses Ziel verlangt eine zusätzliche Prüfung. Sie melden sich nicht neu "
                     "an: Ihre bestehende Sitzung wird höhergestuft.",
        "twofa_code": "Code aus Ihrer Authentifizierungs-App",
        "twofa_verify": "Prüfen",
        "twofa_backup_note": "Auch ein Backup-Code funktioniert, im Format <code>abcd-1234</code>.",
        "twofa_err": "Ungültiger Code.",
        "twofa_err_retry": "Ungültiger Code. Bitte erneut versuchen.",
        "twofa_rate": "Zu viele Versuche. Bitte einige Minuten warten.",

        "enroll_title": "Zweiten Faktor einrichten",
        "enroll_sub": "Das gewünschte Ziel verlangt zwei Faktoren, und Sie haben noch keinen. "
                      "Sie können ihn hier und jetzt einrichten: Sie sind bereits angemeldet, "
                      "also ist dies keine Sackgasse.",
        "enroll_qr_alt": "QR-Code für Ihre Authentifizierungs-App",
        "enroll_manual": "Oder geben Sie diesen Schlüssel von Hand ein",
        "enroll_apps": "Jede TOTP-App genügt: Ente Auth, Aegis, Google Authenticator.",
        "enroll_confirm": "Bestätigen Sie mit dem Code, den die App gerade anzeigt",
        "enroll_activate": "Aktivieren",
        "enroll_note": "Der Schlüssel wird erst gespeichert, wenn ein Code belegt hat, dass die "
                       "App ihn wirklich hat.",

        "codes_title": "Backup-Codes",
        "codes_sub": "Zehn Codes, jeder einmal verwendbar, anstelle des App-Codes, wenn Sie Ihr "
                     "Telefon nicht haben. <strong>Sie sehen sie kein zweites Mal.</strong>",
        "codes_invalidated": "Frühere Codes wurden ungültig gemacht.",
        "codes_done": "Erledigt, sie liegen sicher",

        "home_hello": "Hallo",
        "home_sub": "Die Werkzeuge, auf die Sie Zugriff haben.",
        "home_col_app": "Werkzeug",
        "home_col_address": "Adresse",
        "home_open": "Öffnen",
        "home_empty": "Mit Ihrem Konto ist kein Werkzeug verknüpft. Wenn das falsch ist, wenden "
                      "Sie sich an die Administration.",
        "home_note": "Im Profil können Sie Ihr Passwort ändern, den zweiten Faktor aktivieren, "
                     "ORCID verknüpfen und offene Sitzungen schliessen.",

        "forbidden_title": "Kein Zugriff auf dieses Werkzeug",
        "forbidden_sub": "Sie sind korrekt angemeldet. Nur der Zugriff auf diese Adresse ist für "
                         "Ihr Konto nicht vorgesehen.",
        "forbidden_ask": "Zugang beantragen",
        "forbidden_mine": "Meine Werkzeuge",
        "forbidden_sent_title": "Antrag gesendet",
        "forbidden_sent_body": "Die Administration wurde benachrichtigt.",
        "gate_unknown_host": "Diese Adresse ist in Borant ID nicht registriert. Es fehlt "
                             "nichts an Ihrem Konto: es ist die Konfiguration des Gates. "
                             "Wenden Sie sich an die Administration.",

        "invite_title": "Zugang aktivieren",
        "invite_for": "Einladung für",
        "invite_name": "Name",
        "invite_pw": "Passwort (mindestens 10 Zeichen)",
        "invite_pw2": "Passwort wiederholen",
        "invite_activate": "Aktivieren",
        "invite_err": "Das Passwort muss mindestens 10 Zeichen haben, und beide Eingaben müssen "
                      "übereinstimmen.",
        "invite_orcid_note": "Sie können Ihre ORCID gleich danach im Profil verknüpfen. Die "
                             "Verknüpfung erfolgt nur aus einer bereits angemeldeten Sitzung — "
                             "nie über übereinstimmende E-Mail-Adressen.",
        "invite_bad_title": "Einladung ungültig",
        "invite_bad_body": "Der Link ist abgelaufen oder wurde bereits verwendet. Bitten Sie um "
                           "einen neuen.",

        "reset_title": "Passwort zurücksetzen",
        "reset_sub": "Wir senden Ihnen einen Link, der eine Stunde gültig ist.",
        "reset_send": "Link senden",
        "reset_sent": "Falls diese Adresse hier ein Konto hat, ist eine E-Mail mit dem Link "
                      "unterwegs. Er läuft in einer Stunde ab und funktioniert einmal.",
        "reset_privacy": "Wir sagen Ihnen nicht, ob die Adresse existiert: das darf ein Formular "
                         "nicht preisgeben. Kommt die E-Mail nicht an, wenden Sie sich an die "
                         "Administration — sie kann Ihnen den Link direkt geben.",
        "reset_back": "Zurück zur Anmeldung",
        "reset_new_title": "Neues Passwort",
        "reset_new_sub": "Alle offenen Sitzungen werden geschlossen.",
        "reset_err": "Mindestens 10 Zeichen, und beide Eingaben müssen übereinstimmen.",
        "reset_expired_title": "Link abgelaufen",
        "reset_expired_body": "Dieser Link ist nicht mehr gültig. Bitten Sie um einen neuen.",
        "reset_done_title": "Passwort aktualisiert",
        "reset_done_body": "Alle offenen Sitzungen wurden geschlossen. Sie können sich mit dem "
                           "neuen Passwort anmelden.",

        "profile_title": "Profil",
        "profile_pw": "Passwort",
        "profile_pw_current": "Aktuelles Passwort",
        "profile_pw_new": "Neu",
        "profile_pw_repeat": "Wiederholen",
        "profile_pw_change": "Ändern",
        "profile_pw_note": "Beim Ändern des Passworts werden alle anderen Sitzungen geschlossen, "
                           "diese ausgenommen.",
        "profile_pw_err": "Aktuelles Passwort ist falsch.",
        "profile_pw_short": "Mindestens 10 Zeichen, und beide Eingaben müssen übereinstimmen.",
        "profile_2fa": "Zweiter Faktor",
        "profile_2fa_on": "Aktiv",
        "profile_2fa_off": "Nicht aktiv",
        "profile_2fa_codes": "Noch nicht verwendete Backup-Codes:",
        "profile_2fa_regen": "Neue Backup-Codes erzeugen",
        "profile_2fa_always_on": "Bei jeder Anmeldung fragen",
        "profile_2fa_always_off": "Nicht bei jeder Anmeldung fragen",
        "profile_2fa_disable": "Deaktivieren",
        "profile_2fa_note": "Er ist nicht generell vorgeschrieben, aber einige Werkzeuge "
                            "verlangen ihn: sobald Sie eines davon öffnen, wird Ihnen die "
                            "Einrichtung dort angeboten.",
        "profile_2fa_activate": "Jetzt einrichten",
        "profile_2fa_msg": "Zwei-Faktor-Authentifizierung ist aktiv. Erzeugen Sie Ihre "
                           "Backup-Codes und bewahren Sie sie sicher auf.",
        "profile_orcid": "ORCID",
        "profile_orcid_linked": "Verknüpft:",
        "profile_orcid_one": "ORCID zählt als <strong>nur ein Faktor</strong>: sein Token sagt "
                             "nicht zuverlässig, ob Sie dort die zweistufige Prüfung bestanden "
                             "haben. Werkzeuge, die zwei Faktoren verlangen, brauchen daher "
                             "trotzdem den Code von hier.",
        "profile_orcid_note": "Wenn Sie sie verknüpfen, können Sie sich mit ORCID statt mit "
                              "einem Passwort anmelden.",
        "profile_orcid_link": "Meine ORCID verknüpfen",
        "profile_orcid_none": "ORCID ist auf diesem Server noch nicht konfiguriert.",
        "profile_sessions": "Offene Sitzungen",
        "profile_s_opened": "Geöffnet",
        "profile_s_last": "Zuletzt gesehen",
        "profile_s_origin": "Herkunft",
        "profile_s_level": "Stufe",
        "profile_s_this": "diese",
        "profile_s_two": "zwei Faktoren",
        "profile_s_one": "ein Faktor",
        "profile_s_close": "Schliessen",
        "profile_s_close_all": "Alle schliessen, auch diese",
        "profile_s_note": "Diese Liste ist der Grund, warum es Borant ID gibt: bis heute konnte "
                          "keines der Werkzeuge sagen, welche Sitzungen offen sind — geschweige "
                          "denn eine schliessen.",
        "orcid_taken_title": "ORCID bereits verknüpft",
        "orcid_taken_body": "Diese ORCID iD gehört bereits zu einem anderen Konto. Wenden Sie "
                            "sich an die Administration.",
        "orcid_fail_title": "ORCID-Anmeldung fehlgeschlagen",
        "orcid_fail_body": "Die Anfrage ist abgelaufen oder stimmte nicht überein. Bitte erneut "
                           "versuchen.",
        "orcid_err_unconfigured": "ORCID ist auf diesem Server nicht konfiguriert.",
        "orcid_err_unreachable": "ORCID war nicht erreichbar. Bitte gleich noch einmal versuchen.",
        "orcid_err_rejected": "ORCID hat den Austausch abgelehnt. Versuchen Sie es erneut; passiert "
                              "es wieder, wenden Sie sich an die Administration.",
        "orcid_err_unreadable": "Die Antwort von ORCID war unlesbar. Wenden Sie sich an die Administration.",
        "orcid_err_no_id": "ORCID hat keine iD zurückgegeben. Wenden Sie sich an die Administration.",
        "orcid_unknown_title": "Kein Konto verknüpft",
        "orcid_unknown_body": "Diese ORCID iD ist hier mit keinem Konto verknüpft. Bitten Sie um "
                              "eine Einladung — Sie können sie mit ORCID annehmen.",

        "login_register": "Kein Konto? Registrieren",
        "register_title": "Konto erstellen",
        "register_sub": "Die Registrierung gewährt keinen Zugriff: das Konto beginnt leer, der Zugang zu den Werkzeugen wird danach beantragt.",
        "register_btn": "Registrieren",
        "register_have": "Schon ein Konto? Anmelden",
        "register_domains": "Zugelassen sind nur Adressen dieser Domains:",
        "reg_closed_title": "Registrierung geschlossen",
        "reg_closed_body": "Die Selbstregistrierung ist zurzeit nicht offen. Bitten Sie die Administration um eine Einladung.",
        "reg_bad_email": "Diese E-Mail-Adresse ist ungültig.",
        "reg_bad_domain": "Diese Adresse gehört zu keiner zugelassenen Domain.",
        "reg_taken": "Mit dieser E-Mail besteht bereits ein Konto. Versuchen Sie sich anzumelden oder das Passwort zurückzusetzen.",
        "reg_confirmed_title": "Adresse bestätigt",
        "reg_confirmed_body": "Danke. Sie können jetzt auf Ihrer Startseite Zugang zu Werkzeugen beantragen.",
        "req_unverified_title": "Bestätigen Sie zuerst Ihre E-Mail",
        "req_unverified_body": "Für einen Zugangsantrag braucht es eine bestätigte Adresse. Prüfen Sie Ihren Posteingang, oder bitten Sie die Administration, den Link erneut zu senden.",
        "req_sent_title": "Antrag gesendet",
        "req_sent_body": "Die Administration sieht ihn und entscheidet. Sie erhalten danach eine E-Mail.",
        "home_unverified": "Ihre Adresse ist noch nicht bestätigt: bis dahin können Sie keinen Zugang beantragen.",
        "home_others": "Weitere Werkzeuge",
        "home_others_sub": "Auf diese haben Sie keinen Zugriff. Sie können ihn beantragen.",
        "home_request": "Zugang beantragen",
        "home_pending": "Antrag offen",
        "home_why": "wofür Sie es brauchen (optional)",

        # ── /admin ───────────────────────────────────────────────────────────────
        "fmt_date": "%d.%m.%Y",
        "fmt_datetime_sec": "%d.%m. %H:%M:%S",
        "adm_in_page": "Auf dieser Seite",
        "adm_col_when": "Wann",
        "adm_col_who": "Wer",
        "adm_col_event": "Ereignis",
        "adm_col_detail": "Detail",
        "adm_col_user": "Benutzer",
        "adm_col_expires": "Läuft ab",
        "adm_col_outcome": "Ergebnis",
        "adm_col_why": "Wofür",
        "adm_col_recipient": "Empfänger",
        "adm_col_created": "Erstellt",
        "adm_col_by": "Von",
        "adm_col_prefix": "Präfix",
        "adm_col_elevation": "Erhöhung gültig (Min.)",
        "adm_col_note": "Notiz",
        "adm_back_users": "Zurück zu den Benutzern",
        "adm_back_config": "Zurück zur Konfiguration",
        "adm_lvl_two": "zwei",
        "adm_lvl_one": "eins",
        "adm_deactivate": "Deaktivieren",
        "adm_reactivate": "Reaktivieren",
        "adm_audit_sub": "Die letzten 400 Ereignisse.",
        "adm_audit_ph": "nach Ereignis filtern: login, grant, 2fa, verify…",
        "adm_audit_filter": "Filtern",
        "adm_audit_note": "<code>verify.unknown_host</code> heisst, dass eine "
                          "Anfrage vom Gate für einen Host kam, der hier nicht "
                          "registriert ist: ein Konfigurationsfehler in Caddy, "
                          "und das Gate hat zugemacht.",
        "adm_sessions_title": "Aktive Sitzungen",
        "adm_sessions_sub": "Alle lebenden Sitzungen des Perimeters, und der "
                            "Knopf, der sie schliesst. Bis heute konnte es diese"
                            " Seite nicht geben: die Werkzeuge tragen "
                            "zustandslose JWTs, die niemand widerrufen kann.",
        "adm_sessions_note": "Ein Widerruf greift innerhalb von dreissig "
                             "Sekunden, so lange lebt der Cache vor der "
                             "Datenbank. Für die betroffene Person wird der "
                             "Cache sofort geleert, in der Praxis wirkt es also "
                             "unmittelbar; die dreissig Sekunden sind der "
                             "schlimmste Fall mit mehreren Workern.",
        "adm_batch_title": "Anlegen in Serie",
        "adm_batch_sub": "%(n)s Zeilen verarbeitet, Modus",
        "adm_batch_pw_b": "Die Passwörter erscheinen nur jetzt.",
        "adm_batch_pw": "Kopieren Sie sie, bevor Sie diese Seite verlassen: sie "
                        "liegen gehasht in der Datenbank und lassen sich nicht "
                        "wieder auslesen. Wer eines verliert, geht über den "
                        "Reset.",
        "adm_batch_col_link": "Link (falls die E-Mail nicht rausging)",
        "adm_batch_r_existing": "schon vorhanden, Grants aktualisiert",
        "adm_batch_r_created": "Konto angelegt",
        "adm_batch_r_invited": "Einladung gesendet",
        "adm_batch_r_mail_failed": "E-Mail nicht rausgegangen",
        "adm_del_title": "%(who)s löschen",
        "adm_del_h": "%(who)s löschen?",
        "adm_del_cannot": "Geht nicht.",
        "adm_del_block_no_user": "Benutzer existiert nicht.",
        "adm_del_block_self": "Sie können Ihr eigenes Konto nicht löschen.",
        "adm_del_block_last_admin": "Das ist die letzte aktive Administration. "
                                    "Ernennen Sie zuerst eine weitere, sonst "
                                    "sperren Sie sich selbst aus.",
        "adm_del_err_confirm": "Tippen Sie die Adresse genau ab, um zu "
                               "bestätigen.",
        "adm_del_h_what": "Was hier passiert",
        "adm_del_l1": "Das Konto verschwindet, und mit ihm "
                      "<strong>%(n)s</strong> Grants, die Backup-Codes und der "
                      "zweite Faktor.",
        "adm_del_l2_one": "<strong>%(n)s</strong> offene Sitzung wird sofort "
                          "geschlossen.",
        "adm_del_l2_many": "<strong>%(n)s</strong> offene Sitzungen werden "
                           "sofort geschlossen.",
        "adm_del_l3": "<strong>%(n)s</strong> Log-Zeilen "
                      "<strong>bleiben</strong>, gelöst vom Konto und ohne die "
                      "Adresse. Ein Log, das mit der handelnden Person "
                      "verschwindet, ist kein Log.",
        "adm_del_l4": "Das Ereignis wird mit dem <span "
                      "class=\"mono\">subject</span> festgehalten, nicht mit der "
                      "E-Mail: sie dort zu lassen hiesse, die Adresse aus jeder "
                      "Zeile zu tilgen ausser aus der, die sagt, dass sie "
                      "getilgt wurde.",
        "adm_del_h_notwhat": "Was <em>nicht</em> passiert",
        "adm_del_apps_b": "Die Werkzeuge werden nicht angerührt.",
        "adm_del_apps": "Wenn diese Person sich irgendwo angemeldet hat, ist "
                        "dort ein lokales Profil zurückgeblieben, mit einem nun "
                        "verwaisten <span class=\"mono\">borant_sub</span> — und "
                        "darin ihre Arbeit, ihr Name und ihre Adresse. Eine "
                        "echte Löschung heisst, jedes einzeln durchzugehen.",
        "adm_del_had": "Zugang bestand zu:",
        "adm_del_local": "legt lokale Profile an",
        "adm_del_nogrant": "Keine Grants: wenn sich diese Person nirgends "
                           "angemeldet hat, gibt es nichts weiter aufzuräumen. "
                           "Prüfen Sie trotzdem die Werkzeuge, die allen "
                           "Angemeldeten offenstehen.",
        "adm_del_h_confirm": "Bestätigung",
        "adm_del_retype": "Tippen Sie %(email)s ab, um zu bestätigen",
        "adm_del_note": "Von Hand abtippen ist Absicht: in einer Liste von "
                        "dreissig Studierenden ist ein roter Knopf neben dem "
                        "falschen Namen ein Unfall, der wartet. Wenn Sie nur den"
                        " Zugang wegnehmen wollten, "
                        "<strong>deaktivieren</strong> Sie stattdessen: das ist "
                        "umkehrbar und behält alles.",
        "adm_del_btn": "Endgültig löschen",
        "adm_msg_title_sent": "Nachricht gesendet",
        "adm_msg_title_confirm": "Senden bestätigen",
        "adm_msg_sent_h": "An %(ok)s von %(tot)s gesendet",
        "adm_msg_subject_l": "Betreff",
        "adm_msg_recipients_l": "Empfänger",
        "adm_msg_partial": "Einige gingen nicht raus. Spricht der Fehler von "
                           "einem Limit, ist es Infomaniaks gleitendes "
                           "24-Stunden-Fenster: Empfänger zählen einzeln, und "
                           "Slots werden vierundzwanzig Stunden nach jedem "
                           "Versand frei, nicht um Mitternacht.",
        "adm_msg_all_ok": "Alle raus.",
        "adm_msg_r_ok": "gesendet",
        "adm_msg_about_one": "Sie schreiben gleich an %(n)s Person",
        "adm_msg_about_many": "Sie schreiben gleich an %(n)s Personen",
        "adm_msg_send_one": "An %(n)s Person senden",
        "adm_msg_send_many": "An %(n)s Personen senden",
        "adm_msg_limit_b": "%(n)s Empfänger.",
        "adm_msg_limit": "Das Infomaniak-Limit liegt je nach Tarif bei 200 oder "
                         "500 pro 24 Stunden, und Empfänger zählen einzeln: "
                         "dieser Versand verbraucht %(n)s davon. Das Fenster "
                         "gleitet, die Slots kommen also nach und nach zurück "
                         "und nicht alle um Mitternacht.",
        "adm_msg_h_message": "Die Nachricht",
        "adm_msg_placeholders": "<code>{nome}</code> und <code>{email}</code> "
                                "werden für jeden Empfänger ersetzt. Der Text "
                                "geht als reiner Text raus, ohne HTML.",
        "adm_msg_h_towhom": "An wen",
        "adm_msg_one_each_b": "Eine E-Mail pro Person, keine mit Blindkopie.",
        "adm_msg_one_each": "So sieht niemand die Adressen der anderen, und wenn"
                            " eine fehlschlägt, wissen Sie welche. Mit BCC würde"
                            " man ohnehin nichts sparen: die Empfängerzahl "
                            "bleibt dieselbe.",
        "adm_msg_pb_subject": "Betreff und Text werden beide gebraucht.",
        "adm_msg_pb_norecipients": "Keine Empfänger mit dieser Auswahl.",
        "adm_msg_pb_smtpoff": "SMTP ist aus: die Mail ginge nicht raus.",
        "adm_rcp_all": "alle aktiven Benutzer",
        "adm_rcp_grant": "alle mit einem Grant auf %(app)s",
        "adm_rcp_single": "nur ein Benutzer",
        "adm_rcp_bad": "Auswahl ungültig",
        "adm_rcp_noapp": "Werkzeug existiert nicht",
        "adm_mail_smtp_off": "SMTP ist aus: in /admin/config einrichten",
        "adm_mail_smtp_incomplete": "SMTP unvollständig: Host oder "
                                    "Absenderadresse fehlt",
        "adm_mail_no_recipient": "Kein Empfänger",
        "adm_mail_auth_refused": "SMTP-Authentifizierung abgelehnt. Infomaniak "
                                 "will das Passwort des Postfachs; Gmail ein "
                                 "App-Passwort; bei Microsoft 365 kann der "
                                 "Tenant SMTP AUTH abgeschaltet haben.",
        "adm_cfg_sub": "Das SMTP-Relay wird hier eingestellt und nicht in der "
                       "Umgebung: das Postfach ist zum Zeitpunkt des Deployments"
                       " nicht bekannt. Die Schlüssel (JWT, Fernet, ORCID) "
                       "bleiben, wo sie sind, also ausserhalb der Reichweite "
                       "eines Formulars.",
        "adm_cfg_h_general": "Allgemein",
        "adm_cfg_name": "Name",
        "adm_cfg_url": "Öffentliche URL",
        "adm_cfg_url_note": "Die öffentliche URL landet in den Einladungslinks "
                            "und in den Weiterleitungen zu ORCID: stimmt sie "
                            "nicht, funktioniert der ORCID-Ablauf nicht mehr.",
        "adm_cfg_h_reg": "Registrierung",
        "adm_cfg_reg_open": "Registrierung für alle offen",
        "adm_cfg_domains": "Zugelassene Domains (durch Komma getrennt, leer = "
                           "alle)",
        "adm_cfg_reg_note": "Die Registrierung zu öffnen <strong>öffnet kein "
                            "Werkzeug</strong>: ein neues Konto beginnt mit null"
                            " Grants und erreicht nichts, wer sich registriert "
                            "erwirbt also das Recht zu <em>fragen</em>, nicht "
                            "einzutreten. Was sich ändert: die Benutzertabelle "
                            "füllt sich mit allen, die vorbeikommen, und die "
                            "Anträge wollen abgearbeitet werden. Es steuert auch"
                            " ORCID: bei offener Registrierung legt «Mit ORCID "
                            "anmelden» das Konto an, falls es fehlt — weiterhin "
                            "ohne Grants.",
        "adm_cfg_enabled": "aktiv",
        "adm_cfg_host": "Host",
        "adm_cfg_port": "Port",
        "adm_cfg_security": "Sicherheit",
        "adm_cfg_user": "Benutzername",
        "adm_cfg_pw_set": "gesetzt",
        "adm_cfg_pw_keep": "leer lassen, um es zu behalten",
        "adm_cfg_pw_clear": "löschen",
        "adm_cfg_from": "Absender",
        "adm_cfg_fromname": "Absendername",
        "adm_cfg_h_test": "Testversand",
        "adm_cfg_test_btn": "Test-E-Mail senden",
        "adm_cfg_h_write": "An die Benutzer schreiben",
        "adm_cfg_opt_all": "Alle aktiven Benutzer (%(n)s)",
        "adm_cfg_opt_grant": "Alle mit einem Grant auf %(app)s",
        "adm_cfg_opt_one": "Nur %(who)s",
        "adm_cfg_body": "Text",
        "adm_cfg_body_ph": "Hallo {nome},",
        "adm_cfg_msg_note": "<code>{nome}</code> und <code>{email}</code> werden"
                            " für jeden Empfänger ersetzt. Reiner Text, kein "
                            "HTML. Es geht <strong>eine E-Mail pro "
                            "Person</strong> raus, nie eine mit Blindkopie: "
                            "niemand sieht die Adressen der anderen, und wenn "
                            "eine fehlschlägt, wissen Sie welche. Nur "
                            "registrierte Benutzer — ein Feld für freie Adressen"
                            " gibt es hier absichtlich nicht.",
        "adm_cfg_preview_btn": "Sehen, wer sie bekommt, dann bestätigen",
        "adm_cfg_traps_b": "Zwei bekannte Fallen.",
        "adm_cfg_traps": "Gmail verlangt Zwei-Faktor-Authentifizierung auf dem "
                         "Konto plus ein <em>App-Passwort</em> "
                         "(<code>smtp.gmail.com:587</code>, STARTTLS): das "
                         "normale Passwort wird abgelehnt. Bei Microsoft 365 "
                         "haben viele Tenants <strong>SMTP AUTH standardmässig "
                         "abgeschaltet</strong>, und dann braucht es die Tenant-"
                         "Administration: keine Einstellung hier kommt daran "
                         "vorbei.<br><br>So oder so bleibt Mail eine "
                         "<em>degradierbare</em> Abhängigkeit: liegt das Relay, "
                         "zeigen Einladungen den Link zum Abtippen, statt zu "
                         "scheitern.",
        "adm_cfg_msg_saved": "Konfiguration gespeichert",
        "adm_cfg_msg_test": "Test-E-Mail an %(to)s gesendet",
        "adm_apps_title": "Werkzeuge und Policies",
        "adm_apps_sub": "Hier wird entschieden, <em>welche Stufe ein Pfad "
                        "braucht</em>. Ob ein Pfad durchs Gate geht oder "
                        "öffentlich bleibt, entscheidet Caddy, nicht diese "
                        "Seite: zwei Fragen mit zwei Eigentümern.",
        "adm_apps_nav_register": "Registrieren",
        "adm_apps_h_register": "Ein Werkzeug registrieren",
        "adm_apps_slug": "Slug",
        "adm_apps_access": "Zugang",
        "adm_apps_acc_grant": "nur wer einen Grant hat",
        "adm_apps_acc_any": "alle Angemeldeten",
        "adm_apps_desc": "Beschreibung",
        "adm_apps_roles_l": "Rollen, die dieses Werkzeug verwendet (durch Komma "
                            "getrennt, optional)",
        "adm_apps_roles_ph": "z. B. free, full, admin",
        "adm_apps_h_list": "Registrierte Werkzeuge",
        "adm_apps_off": "deaktiviert",
        "adm_apps_open_all": "offen für alle Angemeldeten",
        "adm_apps_2f_paths": "%(n)s Pfade mit zwei Faktoren",
        "adm_apps_require_grant": "Grant verlangen",
        "adm_apps_open_all_btn": "Für alle öffnen",
        "adm_apps_h_roles": "Rollen",
        "adm_apps_roles_ph2": "leer = dieses Werkzeug hat keine Rollen, und das "
                              "Feld verschwindet aus den Formularen",
        "adm_apps_save_roles": "Rollen speichern",
        "adm_apps_roles_note": "Es füllt das Menü des Feldes «vorgeschlagene "
                               "Rolle» in den Einladungs- und Grant-Formularen, "
                               "mehr nicht: das Gate deutet sie nicht und "
                               "erzwingt sie nicht, denn das Fachvokabular "
                               "gehört dem Werkzeug. <strong>Leer ist eine "
                               "Antwort</strong>, kein Versehen — bei Werkzeugen"
                               " mit einem Booleschen statt Rollen erscheint das"
                               " Feld gar nicht, es gibt also nichts zu merken "
                               "und nichts falsch zu machen. Gefüllt wird es "
                               "beim Gaten des Werkzeugs, indem man das echte "
                               "Vokabular aus seinem Code liest.",
        "adm_apps_h_policy": "Policies pro Pfad",
        "adm_apps_remove": "Entfernen",
        "adm_apps_maxage_ph": "leer = die ganze Sitzung",
        "adm_apps_save_policy": "Policy speichern",
        "adm_apps_policy_note": "Es gewinnt das längste passende Präfix, "
                                "verglichen auf einem normalisierten Pfad in "
                                "Kleinschreibung.",
        "adm_users_sub": "Wer existiert, und in welche Werkzeuge diese Person "
                         "darf.",
        "adm_users_nav_requests": "Anträge",
        "adm_users_nav_invite": "Einladen",
        "adm_users_nav_batch": "In Serie",
        "adm_users_nav_pending": "Offene Einladungen",
        "adm_users_nav_people": "Personen",
        "adm_users_mailfail_b": "Die E-Mail ging nicht raus:",
        "adm_users_mailfail": "Der Einladungslink gilt trotzdem — geben Sie ihn "
                              "von Hand weiter:",
        "adm_users_pwok": "Passwort von <strong>%(who)s</strong> geändert. Die "
                          "offenen Sitzungen wurden geschlossen, und wir haben "
                          "es der Person geschrieben.",
        "adm_users_pwerr": "Passwort von <strong>%(who)s</strong> "
                           "<strong>nicht</strong> geändert: es braucht "
                           "mindestens zehn Zeichen.",
        "adm_users_h_requests": "Zugangsanträge (%(n)s)",
        "adm_users_unverified": "E-Mail nicht bestätigt",
        "adm_users_approve": "Genehmigen",
        "adm_users_deny": "Ablehnen",
        "adm_users_req_note": "Die Rolle wird <strong>hier</strong> gewählt, "
                              "beim Genehmigen, nicht beim Stellen des Antrags: "
                              "das ist der einzige Moment, in dem man weiss, was"
                              " zu gewähren ist. Bei einem Werkzeug, das Geld "
                              "ausgibt — ArguMap zahlt die LLM-Aufrufe aus dem "
                              "Serverschlüssel — öffnet eine aus Trägheit "
                              "gewährte Rolle, die die Pipeline freischaltet, "
                              "einen Hahn.",
        "adm_users_orcid_hint": "Erwartete ORCID (optional)",
        "adm_users_is_admin": "Administration",
        "adm_users_h_apps": "Zugang zu den Werkzeugen",
        "adm_users_role_hint": "Vorgeschlagene Rolle (X-Borant-Hint)",
        "adm_users_role_hint2": "Vorgeschlagene Rolle",
        "adm_users_noroles": "— dieses Werkzeug hat keine Rollen",
        "adm_users_invite_btn": "Einladung senden",
        "adm_users_people_l": "Eine Person pro Zeile — <span "
                              "class=\"mono\">E-Mail</span> oder <span "
                              "class=\"mono\">E-Mail, Vorname Nachname</span>",
        "adm_users_batch_note": "Semikolon und Tabulatoren gehen auch, denn so "
                                "kommen aus einer Tabelle kopierte Listen "
                                "heraus. Leere Zeilen und solche, die mit <span "
                                "class=\"mono\">#</span> beginnen, werden "
                                "übersprungen, Dubletten ebenfalls. Wer schon "
                                "ein Konto hat, bleibt unangetastet: es kommen "
                                "nur die fehlenden Grants dazu, ein "
                                "versehentlich erneut gestarteter Batch setzt "
                                "also nichts zurück.",
        "adm_users_h_how": "Wie",
        "adm_users_mode_invite": "eine Einladung senden: die Person wählt das "
                                 "Passwort selbst, und die Adresse gilt als "
                                 "bestätigt",
        "adm_users_mode_create": "sofort mit erzeugten Passwörtern anlegen: sie "
                                 "erscheinen ein einziges Mal, zum Kopieren",
        "adm_users_batch_btn": "Verarbeiten",
        "adm_users_h_pending": "Ausstehende Einladungen",
        "adm_users_deleted": "Benutzer gelöscht. Denken Sie daran, dass "
                             "<strong>die Werkzeuge nicht angerührt "
                             "wurden</strong>: das lokale Profil liegt weiterhin"
                             " dort, wo sich die Person bereits angemeldet "
                             "hatte.",
        "adm_users_people_sub": "<strong>Deaktivieren</strong> ist umkehrbar und"
                                " behält alles — fast immer ist es das, was "
                                "gebraucht wird. <strong>Löschen</strong> ist "
                                "endgültig und rührt die Werkzeuge nicht an. Ein"
                                " Passwort <strong>setzen</strong> braucht es, "
                                "wenn der Reset per Post kein Weg ist: ein "
                                "geteiltes Konto, dessen Postfach niemand liest,"
                                " eine Adresse, die zurückkommt, ein erzeugtes "
                                "und verlorenes Passwort. Es schliesst alle "
                                "Sitzungen dieser Person und sagt es ihr.",
        "adm_users_badge_admin": "Admin",
        "adm_users_badge_off": "deaktiviert",
        "adm_users_badge_everywhere": "kommt überall rein",
        "adm_users_badge_napps": "%(n)s Werkzeuge",
        "adm_users_badge_noaccess": "kein Zugriff",
        "adm_users_admin_off": "Admin entziehen",
        "adm_users_admin_on": "Zu Admin machen",
        "adm_users_pw_confirm": "Passwort von %(email)s ändern? Die offenen "
                                "Sitzungen werden geschlossen und die Person "
                                "bekommt eine E-Mail.",
        "adm_users_pw_ph": "neues Passwort",
        "adm_users_pw_btn": "Setzen",
        "adm_users_reset2fa": "2FA zurücksetzen",
        "adm_users_delete_link": "Löschen…",
        "adm_users_open_all": "für alle offen",
        "adm_users_offlist": "nicht auf der Liste",
        "adm_users_offlist_title": "Nicht unter den für dieses Werkzeug "
                                   "deklarierten Rollen",
        "adm_users_norole": "keine Rolle deklariert",
        "adm_users_update": "Aktualisieren",
        "adm_users_give": "Gewähren",
        "adm_users_revoke": "Widerrufen",
        "plural_zero_singular": "",
        "adm_batch_sub_one": "%(n)s Zeile verarbeitet, Modus",
        "adm_del_l1_one": "Das Konto verschwindet, und mit ihm "
                          "<strong>%(n)s</strong> Grant, die Backup-Codes und "
                          "der zweite Faktor.",
        "adm_del_l3_one": "<strong>%(n)s</strong> Log-Zeile "
                          "<strong>bleibt</strong>, gelöst vom Konto und ohne "
                          "die Adresse. Ein Log, das mit der handelnden "
                          "Person verschwindet, ist kein Log.",
        "adm_users_badge_napps_one": "%(n)s Werkzeug",
        "adm_apps_2f_paths_one": "%(n)s Pfad mit zwei Faktoren",
    },

    # ── FRANÇAIS ──────────────────────────────────────────────────────────────
    "fr": {
        "nav_profile": "Profil",
        "nav_users": "Utilisateurs",
        "nav_apps": "Applications",
        "nav_sessions": "Sessions",
        "nav_log": "Journal",
        "nav_config": "Configuration",
        "nav_logout": "Se déconnecter",
        "logout_title": "Se déconnecter de Borant ID ?",
        "logout_sub": "Cela met fin à la session ici et dans tous les outils situés derrière cet accès, pas seulement celui d'où vous venez.",
        "logout_confirm": "Se déconnecter",
        "logout_cancel": "Annuler",
        "tagline": "Accès unique aux outils de recherche",

        "email": "E-mail",
        "password": "Mot de passe",
        "back": "Retour",
        "save": "Enregistrer",
        "fmt_datetime": "%d/%m/%Y %H:%M",
        "fmt_datetime_short": "%d/%m %H:%M",

        "login_title": "Connexion",
        "login_sub": "Une seule entrée pour tous les outils sur borant.eu.",
        "login_enter": "Se connecter",
        "login_forgot": "Mot de passe oublié",
        "login_err": "E-mail ou mot de passe invalide.",
        "login_rate": "Trop de tentatives. Réessayez dans un quart d'heure.",
        "login_orcid": "Se connecter avec ORCID",
        "login_orcid_note": "Cela fonctionne si votre ORCID est déjà lié à un compte ici. Sinon, "
                            "demandez une invitation — vous pourrez l'accepter avec ORCID.",
        "cookie_trouble_title": "Le cookie de session ne tient pas.",
        "cookie_trouble_body": "Vous semblez connecté, mais votre navigateur ne renvoie pas la "
                               "session. C'est en général un blocage des cookies, une horloge "
                               "très décalée, ou un domaine de cookie mal configuré. Réessayez ; "
                               "si cela se reproduit, signalez-le à un administrateur plutôt que "
                               "d'insister.",

        "twofa_title": "Second facteur",
        "twofa_sub": "Cette destination demande une vérification supplémentaire. Vous ne vous "
                     "reconnectez pas : la session que vous avez déjà est élevée.",
        "twofa_code": "Code de votre application d'authentification",
        "twofa_verify": "Vérifier",
        "twofa_backup_note": "Un code de secours fonctionne aussi, au format "
                             "<code>abcd-1234</code>.",
        "twofa_err": "Code invalide.",
        "twofa_err_retry": "Code invalide. Réessayez.",
        "twofa_rate": "Trop de tentatives. Attendez quelques minutes.",

        "enroll_title": "Activer le second facteur",
        "enroll_sub": "La destination demandée exige deux facteurs et vous n'en avez pas encore. "
                      "Cela s'active ici, maintenant : vous êtes déjà authentifié, donc ce n'est "
                      "pas une impasse.",
        "enroll_qr_alt": "QR code pour votre application d'authentification",
        "enroll_manual": "Ou saisissez cette clé à la main",
        "enroll_apps": "N'importe quelle application TOTP convient : Ente Auth, Aegis, Google "
                       "Authenticator.",
        "enroll_confirm": "Confirmez avec le code que l'application affiche maintenant",
        "enroll_activate": "Activer",
        "enroll_note": "La clé n'est enregistrée qu'une fois qu'un code a prouvé que "
                       "l'application la possède vraiment.",

        "codes_title": "Codes de secours",
        "codes_sub": "Dix codes, utilisables une fois chacun, à la place du code de "
                     "l'application quand vous n'avez pas votre téléphone. <strong>Vous ne les "
                     "reverrez pas.</strong>",
        "codes_invalidated": "Les codes précédents, s'il y en avait, ont été invalidés.",
        "codes_done": "C'est fait, ils sont en lieu sûr",

        "home_hello": "Bonjour",
        "home_sub": "Les outils auxquels vous avez accès.",
        "home_col_app": "Outil",
        "home_col_address": "Adresse",
        "home_open": "Ouvrir",
        "home_empty": "Aucun outil n'est associé à votre compte. Si cela vous semble faux, "
                      "demandez à un administrateur.",
        "home_note": "Depuis votre profil vous pouvez changer de mot de passe, activer le second "
                     "facteur, lier ORCID et fermer les sessions ouvertes.",

        "forbidden_title": "Vous n'avez pas accès à cet outil",
        "forbidden_sub": "Vous êtes correctement authentifié. C'est l'accès à cette adresse qui "
                         "n'est pas prévu pour votre compte.",
        "forbidden_ask": "Demander l'accès",
        "forbidden_mine": "Mes outils",
        "forbidden_sent_title": "Demande envoyée",
        "forbidden_sent_body": "Les administrateurs ont été prévenus.",
        "gate_unknown_host": "Cette adresse n'est pas enregistrée dans Borant ID. Il ne "
                             "manque rien à votre compte : c'est la configuration de la "
                             "porte d'accès. Signalez-le à un administrateur.",

        "invite_title": "Activer votre accès",
        "invite_for": "Invitation pour",
        "invite_name": "Nom",
        "invite_pw": "Mot de passe (au moins 10 caractères)",
        "invite_pw2": "Répétez le mot de passe",
        "invite_activate": "Activer",
        "invite_err": "Le mot de passe doit faire au moins 10 caractères, et les deux copies "
                      "doivent correspondre.",
        "invite_orcid_note": "Vous pourrez lier votre ORCID juste après, depuis votre profil. La "
                             "liaison ne se fait que depuis une session déjà authentifiée — "
                             "jamais par correspondance automatique d'adresses.",
        "invite_bad_title": "Invitation invalide",
        "invite_bad_body": "Le lien a expiré ou a déjà été utilisé. Demandez-en un autre.",

        "reset_title": "Réinitialiser le mot de passe",
        "reset_sub": "Nous vous envoyons un lien valable une heure.",
        "reset_send": "Envoyez-moi le lien",
        "reset_sent": "Si cette adresse a un compte ici, un e-mail avec le lien est parti. Il "
                      "expire dans une heure et ne sert qu'une fois.",
        "reset_privacy": "Nous ne vous disons pas si l'adresse existe : ce n'est pas à un "
                         "formulaire de le révéler. Si l'e-mail n'arrive pas, demandez à un "
                         "administrateur — il peut vous donner le lien directement.",
        "reset_back": "Retour à la connexion",
        "reset_new_title": "Nouveau mot de passe",
        "reset_new_sub": "Toutes les sessions ouvertes seront fermées.",
        "reset_err": "Au moins 10 caractères, et les deux copies doivent correspondre.",
        "reset_expired_title": "Lien expiré",
        "reset_expired_body": "Ce lien de réinitialisation n'est plus valable. Demandez-en un "
                              "autre.",
        "reset_done_title": "Mot de passe mis à jour",
        "reset_done_body": "Toutes les sessions ouvertes ont été fermées. Vous pouvez vous "
                           "connecter avec le nouveau mot de passe.",

        "profile_title": "Profil",
        "profile_pw": "Mot de passe",
        "profile_pw_current": "Mot de passe actuel",
        "profile_pw_new": "Nouveau",
        "profile_pw_repeat": "Répétez",
        "profile_pw_change": "Changer",
        "profile_pw_note": "Changer de mot de passe ferme toutes les autres sessions, celle-ci "
                           "exceptée.",
        "profile_pw_err": "Mot de passe actuel incorrect.",
        "profile_pw_short": "Au moins 10 caractères, et les deux copies doivent correspondre.",
        "profile_2fa": "Second facteur",
        "profile_2fa_on": "Actif",
        "profile_2fa_off": "Inactif",
        "profile_2fa_codes": "Codes de secours pas encore utilisés :",
        "profile_2fa_regen": "Régénérer les codes de secours",
        "profile_2fa_always_on": "Me le demander à chaque connexion",
        "profile_2fa_always_off": "Ne plus me le demander à chaque connexion",
        "profile_2fa_disable": "Désactiver",
        "profile_2fa_note": "Ce n'est pas obligatoire en général, mais certains outils l'exigent : "
                            "quand vous en ouvrez un, l'activation vous est proposée sur place.",
        "profile_2fa_activate": "L'activer maintenant",
        "profile_2fa_msg": "L'authentification à deux facteurs est active. Générez vos codes de "
                           "secours et mettez-les en lieu sûr.",
        "profile_orcid": "ORCID",
        "profile_orcid_linked": "Lié :",
        "profile_orcid_one": "ORCID compte pour <strong>un seul facteur</strong> : son jeton ne "
                             "dit pas de façon fiable si vous avez passé leur vérification en "
                             "deux étapes. Les outils qui demandent deux facteurs ont donc quand "
                             "même besoin du code d'ici.",
        "profile_orcid_note": "Le lier vous permet de vous connecter avec ORCID au lieu d'un mot "
                              "de passe.",
        "profile_orcid_link": "Lier mon ORCID",
        "profile_orcid_none": "ORCID n'est pas encore configuré sur ce serveur.",
        "profile_sessions": "Sessions ouvertes",
        "profile_s_opened": "Ouverte",
        "profile_s_last": "Dernier accès",
        "profile_s_origin": "Origine",
        "profile_s_level": "Niveau",
        "profile_s_this": "celle-ci",
        "profile_s_two": "deux facteurs",
        "profile_s_one": "un facteur",
        "profile_s_close": "Fermer",
        "profile_s_close_all": "Tout fermer, celle-ci comprise",
        "profile_s_note": "Cette liste est la raison d'être de Borant ID : jusqu'à aujourd'hui "
                          "aucun des outils ne savait dire quelles sessions étaient ouvertes, "
                          "encore moins en fermer une.",
        "orcid_taken_title": "ORCID déjà lié",
        "orcid_taken_body": "Cet identifiant ORCID appartient déjà à un autre compte. Écrivez à "
                            "un administrateur.",
        "orcid_fail_title": "Échec de la connexion ORCID",
        "orcid_fail_body": "La requête a expiré ou ne correspondait pas. Réessayez.",
        "orcid_err_unconfigured": "ORCID n'est pas configuré sur ce serveur.",
        "orcid_err_unreachable": "Nous n'avons pas pu joindre ORCID. Réessayez dans un instant.",
        "orcid_err_rejected": "ORCID a refusé l'échange. Réessayez ; si cela se reproduit, "
                              "signalez-le à un administrateur.",
        "orcid_err_unreadable": "La réponse d'ORCID est illisible. Signalez-le à un administrateur.",
        "orcid_err_no_id": "ORCID n'a pas renvoyé d'iD. Signalez-le à un administrateur.",
        "orcid_unknown_title": "Aucun compte lié",
        "orcid_unknown_body": "Cet identifiant ORCID n'est lié à aucun compte ici. Demandez une "
                              "invitation — vous pourrez l'accepter avec ORCID.",

        "login_register": "Pas de compte ? Inscrivez-vous",
        "register_title": "Créer un compte",
        "register_sub": "S'inscrire ne donne accès à rien : le compte démarre vide, et l'accès aux outils se demande ensuite.",
        "register_btn": "S'inscrire",
        "register_have": "Vous avez déjà un compte ? Connectez-vous",
        "register_domains": "Seules les adresses de ces domaines sont acceptées :",
        "reg_closed_title": "Inscriptions fermées",
        "reg_closed_body": "L'inscription libre n'est pas ouverte pour le moment. Demandez une invitation à un administrateur.",
        "reg_bad_email": "Cette adresse n'est pas valide.",
        "reg_bad_domain": "Cette adresse n'appartient pas à un domaine accepté.",
        "reg_taken": "Un compte existe déjà avec cette adresse. Essayez de vous connecter, ou de réinitialiser le mot de passe.",
        "reg_confirmed_title": "Adresse confirmée",
        "reg_confirmed_body": "Merci. Vous pouvez maintenant demander l'accès aux outils depuis votre page d'accueil.",
        "req_unverified_title": "Confirmez d'abord votre adresse",
        "req_unverified_body": "Une demande d'accès exige une adresse confirmée. Vérifiez votre boîte, ou demandez à un administrateur de renvoyer le lien.",
        "req_sent_title": "Demande envoyée",
        "req_sent_body": "Un administrateur la verra et décidera. Vous recevrez un e-mail une fois fait.",
        "home_unverified": "Votre adresse n'est pas encore confirmée : d'ici là, vous ne pouvez pas demander l'accès aux outils.",
        "home_others": "Autres outils",
        "home_others_sub": "Vous n'avez pas accès à ceux-ci. Vous pouvez le demander.",
        "home_request": "Demander l'accès",
        "home_pending": "demande en attente",
        "home_why": "pourquoi vous en avez besoin (facultatif)",

        # ── /admin ───────────────────────────────────────────────────────────────
        "fmt_date": "%d/%m/%Y",
        "fmt_datetime_sec": "%d/%m %H:%M:%S",
        "adm_in_page": "Sur cette page",
        "adm_col_when": "Quand",
        "adm_col_who": "Qui",
        "adm_col_event": "Événement",
        "adm_col_detail": "Détail",
        "adm_col_user": "Utilisateur",
        "adm_col_expires": "Expire",
        "adm_col_outcome": "Résultat",
        "adm_col_why": "Pourquoi",
        "adm_col_recipient": "Destinataire",
        "adm_col_created": "Créé",
        "adm_col_by": "Par",
        "adm_col_prefix": "Préfixe",
        "adm_col_elevation": "Élévation valable (min)",
        "adm_col_note": "Note",
        "adm_back_users": "Retour aux utilisateurs",
        "adm_back_config": "Retour à la configuration",
        "adm_lvl_two": "deux",
        "adm_lvl_one": "un",
        "adm_deactivate": "Désactiver",
        "adm_reactivate": "Réactiver",
        "adm_audit_sub": "Les 400 derniers événements.",
        "adm_audit_ph": "filtrer par événement : login, grant, 2fa, verify…",
        "adm_audit_filter": "Filtrer",
        "adm_audit_note": "<code>verify.unknown_host</code> signifie qu'une "
                          "requête est arrivée du gate pour un hôte qui n'est "
                          "pas enregistré ici : c'est une erreur de "
                          "configuration dans Caddy, et le gate a fermé la "
                          "porte.",
        "adm_sessions_title": "Sessions actives",
        "adm_sessions_sub": "Toutes les sessions vivantes du périmètre, et le "
                            "bouton pour les fermer. Jusqu'à aujourd'hui cette "
                            "page ne pouvait pas exister : les outils portent "
                            "des JWT sans état, que personne ne peut révoquer.",
        "adm_sessions_note": "Une révocation prend effet en trente secondes, la "
                             "durée de vie du cache devant la base de données. "
                             "Le cache est vidé aussitôt pour la personne "
                             "concernée, donc en pratique c'est immédiat ; les "
                             "trente secondes sont le pire cas avec plusieurs "
                             "workers.",
        "adm_batch_title": "Création en lot",
        "adm_batch_sub": "%(n)s lignes traitées, mode",
        "adm_batch_pw_b": "Les mots de passe n'apparaissent que maintenant.",
        "adm_batch_pw": "Copiez-les avant de quitter cette page : ils sont "
                        "hachés dans la base de données et il n'y a aucun moyen "
                        "de les relire. Qui en perd un passe par la "
                        "réinitialisation.",
        "adm_batch_col_link": "Lien (si l'e-mail n'est pas parti)",
        "adm_batch_r_existing": "déjà présent, grants mis à jour",
        "adm_batch_r_created": "compte créé",
        "adm_batch_r_invited": "invitation envoyée",
        "adm_batch_r_mail_failed": "e-mail non parti",
        "adm_del_title": "Supprimer %(who)s",
        "adm_del_h": "Supprimer %(who)s ?",
        "adm_del_cannot": "Impossible.",
        "adm_del_block_no_user": "Utilisateur inexistant.",
        "adm_del_block_self": "Vous ne pouvez pas supprimer votre propre compte.",
        "adm_del_block_last_admin": "C'est le dernier administrateur actif. "
                                    "Nommez-en un autre d'abord, ou vous restez "
                                    "dehors.",
        "adm_del_err_confirm": "Retapez l'adresse exactement pour confirmer.",
        "adm_del_h_what": "Ce qui se passe ici",
        "adm_del_l1": "Le compte disparaît, et avec lui <strong>%(n)s</strong> "
                      "grants, les codes de secours et le second facteur.",
        "adm_del_l2_one": "<strong>%(n)s</strong> session ouverte est fermée "
                          "aussitôt.",
        "adm_del_l2_many": "<strong>%(n)s</strong> sessions ouvertes sont "
                           "fermées aussitôt.",
        "adm_del_l3": "<strong>%(n)s</strong> lignes de journal "
                      "<strong>restent</strong>, détachées du compte et "
                      "nettoyées de l'adresse. Un journal qui disparaît avec "
                      "celui qui a agi n'est pas un journal.",
        "adm_del_l4": "L'événement est enregistré avec le <span "
                      "class=\"mono\">subject</span>, pas avec l'adresse : la "
                      "garder là reviendrait à effacer l'adresse de chaque ligne"
                      " sauf celle qui dit qu'elle a été effacée.",
        "adm_del_h_notwhat": "Ce qui n'arrive <em>pas</em>",
        "adm_del_apps_b": "Les outils ne sont pas touchés.",
        "adm_del_apps": "Si cette personne s'est connectée quelque part, un "
                        "profil local y est resté avec un <span "
                        "class=\"mono\">borant_sub</span> désormais orphelin — et "
                        "dedans son travail, son nom et son adresse. Une vraie "
                        "suppression passe par chacun d'eux.",
        "adm_del_had": "Avait accès à :",
        "adm_del_local": "crée des profils locaux",
        "adm_del_nogrant": "Aucun grant : si cette personne ne s'est jamais "
                           "connectée nulle part, il n'y a rien d'autre à "
                           "nettoyer. Vérifiez quand même les outils ouverts à "
                           "tout utilisateur authentifié.",
        "adm_del_h_confirm": "Confirmation",
        "adm_del_retype": "Retapez %(email)s pour confirmer",
        "adm_del_note": "On retape à la main exprès : dans une liste de trente "
                        "étudiants, un bouton rouge à côté du mauvais nom est un"
                        " accident qui attend. Si vous vouliez seulement retirer"
                        " l'accès, <strong>désactivez</strong> plutôt : c'est "
                        "réversible et cela conserve tout.",
        "adm_del_btn": "Supprimer définitivement",
        "adm_msg_title_sent": "Message envoyé",
        "adm_msg_title_confirm": "Confirmer l'envoi",
        "adm_msg_sent_h": "Envoyé à %(ok)s sur %(tot)s",
        "adm_msg_subject_l": "Objet",
        "adm_msg_recipients_l": "destinataires",
        "adm_msg_partial": "Certains ne sont pas partis. Si l'erreur parle d'une"
                           " limite, c'est la fenêtre glissante de 24 heures "
                           "d'Infomaniak : les destinataires se comptent un par "
                           "un, et les créneaux se libèrent vingt-quatre heures "
                           "après chaque envoi, pas à minuit.",
        "adm_msg_all_ok": "Toutes parties.",
        "adm_msg_r_ok": "envoyé",
        "adm_msg_about_one": "Vous allez écrire à %(n)s personne",
        "adm_msg_about_many": "Vous allez écrire à %(n)s personnes",
        "adm_msg_send_one": "Envoyer à %(n)s personne",
        "adm_msg_send_many": "Envoyer à %(n)s personnes",
        "adm_msg_limit_b": "%(n)s destinataires.",
        "adm_msg_limit": "La limite Infomaniak est de 200 ou 500 par 24 heures "
                         "selon le plan, et les destinataires se comptent un par"
                         " un : cet envoi en consomme %(n)s. La fenêtre est "
                         "glissante, donc les créneaux reviennent peu à peu et "
                         "pas tous à minuit.",
        "adm_msg_h_message": "Le message",
        "adm_msg_placeholders": "<code>{nome}</code> et <code>{email}</code> "
                                "sont remplacés pour chaque destinataire. Le "
                                "texte part en clair, sans HTML.",
        "adm_msg_h_towhom": "À qui",
        "adm_msg_one_each_b": "Un e-mail par personne, pas un seul en copie "
                              "cachée.",
        "adm_msg_one_each": "Ainsi personne ne voit les adresses des autres, et "
                            "si l'un échoue vous savez lequel. En BCC on "
                            "n'économiserait rien de toute façon : le compte des"
                            " destinataires est le même.",
        "adm_msg_pb_subject": "Il faut un objet et un texte.",
        "adm_msg_pb_norecipients": "Aucun destinataire avec cette sélection.",
        "adm_msg_pb_smtpoff": "SMTP est éteint : le courrier ne partirait pas.",
        "adm_rcp_all": "tous les utilisateurs actifs",
        "adm_rcp_grant": "ceux qui ont un grant sur %(app)s",
        "adm_rcp_single": "un seul utilisateur",
        "adm_rcp_bad": "sélection non valide",
        "adm_rcp_noapp": "outil inexistant",
        "adm_mail_smtp_off": "SMTP éteint : configurez-le dans /admin/config",
        "adm_mail_smtp_incomplete": "SMTP incomplet : hôte ou adresse "
                                    "d'expéditeur manquant",
        "adm_mail_no_recipient": "Aucun destinataire",
        "adm_mail_auth_refused": "Authentification SMTP refusée. Infomaniak veut"
                                 " le mot de passe de la boîte ; Gmail un mot de"
                                 " passe d'application ; sur Microsoft 365 le "
                                 "tenant peut avoir désactivé SMTP AUTH.",
        "adm_cfg_sub": "Le relais SMTP se règle ici et non dans l'environnement "
                       ": la boîte n'est pas connue au moment du déploiement. "
                       "Les clés (JWT, Fernet, ORCID) restent où elles sont, "
                       "hors de portée d'un formulaire.",
        "adm_cfg_h_general": "Général",
        "adm_cfg_name": "Nom",
        "adm_cfg_url": "URL publique",
        "adm_cfg_url_note": "L'URL publique se retrouve dans les liens "
                            "d'invitation et dans les redirections vers ORCID : "
                            "si elle est fausse, le flux ORCID cesse de "
                            "fonctionner.",
        "adm_cfg_h_reg": "Inscription",
        "adm_cfg_reg_open": "inscription ouverte à tous",
        "adm_cfg_domains": "Domaines acceptés (séparés par des virgules, vide = "
                           "tous)",
        "adm_cfg_reg_note": "Ouvrir les inscriptions <strong>n'ouvre aucun "
                            "outil</strong> : un compte neuf démarre avec zéro "
                            "grant et n'atteint rien, donc qui s'inscrit gagne "
                            "le droit de <em>demander</em>, pas d'entrer. Ce qui"
                            " change, c'est que la table des utilisateurs se "
                            "remplit de quiconque passe, et que les demandes "
                            "sont à traiter. Cela gouverne aussi ORCID : "
                            "inscriptions ouvertes, «se connecter avec ORCID» "
                            "crée le compte s'il n'existe pas — toujours sans "
                            "grant.",
        "adm_cfg_enabled": "actif",
        "adm_cfg_host": "Hôte",
        "adm_cfg_port": "Port",
        "adm_cfg_security": "Sécurité",
        "adm_cfg_user": "Utilisateur",
        "adm_cfg_pw_set": "défini",
        "adm_cfg_pw_keep": "laissez vide pour le garder",
        "adm_cfg_pw_clear": "effacer",
        "adm_cfg_from": "Expéditeur",
        "adm_cfg_fromname": "Nom de l'expéditeur",
        "adm_cfg_h_test": "Envoi de test",
        "adm_cfg_test_btn": "Envoyer un e-mail de test",
        "adm_cfg_h_write": "Écrire aux utilisateurs",
        "adm_cfg_opt_all": "Tous les utilisateurs actifs (%(n)s)",
        "adm_cfg_opt_grant": "Ceux qui ont un grant sur %(app)s",
        "adm_cfg_opt_one": "Seulement %(who)s",
        "adm_cfg_body": "Texte",
        "adm_cfg_body_ph": "Bonjour {nome},",
        "adm_cfg_msg_note": "<code>{nome}</code> et <code>{email}</code> sont "
                            "remplacés pour chaque destinataire. Texte simple, "
                            "pas de HTML. Il part <strong>un e-mail par "
                            "personne</strong>, jamais un seul en copie cachée :"
                            " personne ne voit les adresses des autres, et si "
                            "l'un échoue vous savez lequel. Utilisateurs "
                            "enregistrés seulement — il n'y a pas de champ pour "
                            "des adresses libres ici, exprès.",
        "adm_cfg_preview_btn": "Voir qui reçoit, puis confirmer",
        "adm_cfg_traps_b": "Deux pièges connus.",
        "adm_cfg_traps": "Gmail exige l'authentification à deux facteurs sur le "
                         "compte plus un <em>mot de passe d'application</em> "
                         "(<code>smtp.gmail.com:587</code>, STARTTLS) : le mot "
                         "de passe normal est refusé. Sur Microsoft 365 beaucoup"
                         " de tenants ont <strong>SMTP AUTH désactivé par "
                         "défaut</strong>, et il faut alors l'administrateur du "
                         "tenant : aucune configuration ici ne peut le "
                         "contourner.<br><br>Dans tous les cas le courrier reste"
                         " une dépendance <em>dégradable</em> : si le relais est"
                         " à terre, les invitations affichent le lien à copier à"
                         " la main au lieu d'échouer.",
        "adm_cfg_msg_saved": "Configuration enregistrée",
        "adm_cfg_msg_test": "E-mail de test envoyé à %(to)s",
        "adm_apps_title": "Outils et policies",
        "adm_apps_sub": "Ici on décide <em>quel niveau exige quel chemin</em>. "
                        "Qu'un chemin passe par le gate ou reste public, c'est "
                        "Caddy qui le décide, pas cette page : deux questions "
                        "avec deux propriétaires.",
        "adm_apps_nav_register": "Enregistrer",
        "adm_apps_h_register": "Enregistrer un outil",
        "adm_apps_slug": "Slug",
        "adm_apps_access": "Accès",
        "adm_apps_acc_grant": "seulement ceux qui ont un grant",
        "adm_apps_acc_any": "toute personne authentifiée",
        "adm_apps_desc": "Description",
        "adm_apps_roles_l": "Rôles utilisés par cet outil (séparés par des "
                            "virgules, facultatif)",
        "adm_apps_roles_ph": "ex. free, full, admin",
        "adm_apps_h_list": "Outils enregistrés",
        "adm_apps_off": "désactivé",
        "adm_apps_open_all": "ouvert à toute personne authentifiée",
        "adm_apps_2f_paths": "%(n)s chemins à deux facteurs",
        "adm_apps_require_grant": "Exiger un grant",
        "adm_apps_open_all_btn": "Ouvrir à tous",
        "adm_apps_h_roles": "Rôles",
        "adm_apps_roles_ph2": "vide = cet outil n'a pas de rôles, et le champ "
                              "disparaît des formulaires",
        "adm_apps_save_roles": "Enregistrer les rôles",
        "adm_apps_roles_note": "Cela remplit le menu du champ «rôle suggéré» "
                               "dans les formulaires d'invitation et de grant, "
                               "rien d'autre : le gate ne les interprète pas et "
                               "ne les impose pas, car le vocabulaire métier "
                               "appartient à l'outil. <strong>Vide est une "
                               "réponse</strong>, pas un oubli — pour les outils"
                               " qui ont un booléen au lieu de rôles, le champ "
                               "n'apparaît pas du tout, il n'y a donc rien à "
                               "retenir et rien à se tromper. On le remplit au "
                               "moment de gater l'outil, en lisant le vrai "
                               "vocabulaire dans son code.",
        "adm_apps_h_policy": "Policies par chemin",
        "adm_apps_remove": "Retirer",
        "adm_apps_maxage_ph": "vide = toute la session",
        "adm_apps_save_policy": "Enregistrer la policy",
        "adm_apps_policy_note": "Le préfixe correspondant le plus long "
                                "l'emporte, comparé sur un chemin normalisé et "
                                "en minuscules.",
        "adm_users_sub": "Qui existe, et dans quels outils cette personne peut "
                         "entrer.",
        "adm_users_nav_requests": "Demandes",
        "adm_users_nav_invite": "Inviter",
        "adm_users_nav_batch": "En lot",
        "adm_users_nav_pending": "Invitations ouvertes",
        "adm_users_nav_people": "Personnes",
        "adm_users_mailfail_b": "L'e-mail n'est pas parti :",
        "adm_users_mailfail": "Le lien d'invitation reste valable — transmettez-"
                              "le à la main :",
        "adm_users_pwok": "Mot de passe de <strong>%(who)s</strong> changé. Ses "
                          "sessions ouvertes ont été fermées, et nous le lui "
                          "avons écrit.",
        "adm_users_pwerr": "Mot de passe de <strong>%(who)s</strong> "
                           "<strong>non</strong> changé : il en faut au moins "
                           "dix caractères.",
        "adm_users_h_requests": "Demandes d'accès (%(n)s)",
        "adm_users_unverified": "adresse non confirmée",
        "adm_users_approve": "Approuver",
        "adm_users_deny": "Refuser",
        "adm_users_req_note": "Le rôle se choisit <strong>ici</strong>, en "
                              "approuvant, pas au moment où la demande est faite"
                              " : c'est le seul moment où l'on sait quoi "
                              "accorder. Pour un outil qui dépense — ArguMap "
                              "paie les appels LLM sur la clé du serveur — "
                              "accorder par inertie un rôle qui débloque la "
                              "pipeline ouvre un robinet.",
        "adm_users_orcid_hint": "ORCID attendu (facultatif)",
        "adm_users_is_admin": "administrateur",
        "adm_users_h_apps": "Accès aux outils",
        "adm_users_role_hint": "Rôle suggéré (X-Borant-Hint)",
        "adm_users_role_hint2": "Rôle suggéré",
        "adm_users_noroles": "— cet outil n'a pas de rôles",
        "adm_users_invite_btn": "Envoyer l'invitation",
        "adm_users_people_l": "Une personne par ligne — <span "
                              "class=\"mono\">e-mail</span> ou <span "
                              "class=\"mono\">e-mail, Prénom Nom</span>",
        "adm_users_batch_note": "Les points-virgules et les tabulations passent "
                                "aussi, car c'est ainsi que sortent les listes "
                                "collées depuis un tableur. Les lignes vides et "
                                "celles qui commencent par <span "
                                "class=\"mono\">#</span> sont sautées, les "
                                "doublons aussi. Qui a déjà un compte n'est pas "
                                "touché : on ajoute seulement les grants "
                                "manquants, ainsi un lot relancé par erreur ne "
                                "remet rien à zéro.",
        "adm_users_h_how": "Comment",
        "adm_users_mode_invite": "envoyer une invitation : ils choisissent le "
                                 "mot de passe eux-mêmes, et l'adresse ressort "
                                 "vérifiée",
        "adm_users_mode_create": "créer tout de suite avec des mots de passe "
                                 "générés : ils apparaissent une seule fois, à "
                                 "copier",
        "adm_users_batch_btn": "Traiter",
        "adm_users_h_pending": "Invitations en attente",
        "adm_users_deleted": "Utilisateur supprimé. Rappelez-vous que "
                             "<strong>les outils n'ont pas été touchés</strong> "
                             ": le profil local est toujours là où cette "
                             "personne s'était déjà connectée.",
        "adm_users_people_sub": "<strong>Désactiver</strong> est réversible et "
                                "conserve tout — c'est presque toujours ce qu'il"
                                " faut. <strong>Supprimer</strong> est définitif"
                                " et ne touche pas aux outils. "
                                "<strong>Définir</strong> un mot de passe sert "
                                "quand la réinitialisation par courrier n'est "
                                "pas une route : un compte partagé dont personne"
                                " ne lit la boîte, une adresse qui rebondit, un "
                                "mot de passe généré puis perdu. Cela ferme "
                                "toutes les sessions de cette personne et le lui"
                                " fait savoir.",
        "adm_users_badge_admin": "admin",
        "adm_users_badge_off": "désactivé",
        "adm_users_badge_everywhere": "entre partout",
        "adm_users_badge_napps": "%(n)s outils",
        "adm_users_badge_noaccess": "aucun accès",
        "adm_users_admin_off": "Retirer admin",
        "adm_users_admin_on": "Rendre admin",
        "adm_users_pw_confirm": "Changer le mot de passe de %(email)s ? Ses "
                                "sessions ouvertes seront fermées et elle "
                                "recevra un e-mail.",
        "adm_users_pw_ph": "nouveau mot de passe",
        "adm_users_pw_btn": "Définir",
        "adm_users_reset2fa": "Réinitialiser la 2FA",
        "adm_users_delete_link": "Supprimer…",
        "adm_users_open_all": "ouvert à tous",
        "adm_users_offlist": "hors liste",
        "adm_users_offlist_title": "Ne fait pas partie des rôles déclarés pour "
                                   "cet outil",
        "adm_users_norole": "aucun rôle déclaré",
        "adm_users_update": "Mettre à jour",
        "adm_users_give": "Accorder",
        "adm_users_revoke": "Révoquer",
        "plural_zero_singular": "1",
        "adm_batch_sub_one": "%(n)s ligne traitée, mode",
        "adm_del_l1_one": "Le compte disparaît, et avec lui "
                          "<strong>%(n)s</strong> grant, les codes de secours "
                          "et le second facteur.",
        "adm_del_l3_one": "<strong>%(n)s</strong> ligne de journal "
                          "<strong>reste</strong>, détachée du compte et "
                          "nettoyée de l'adresse. Un journal qui disparaît "
                          "avec celui qui a agi n'est pas un journal.",
        "adm_users_badge_napps_one": "%(n)s outil",
        "adm_apps_2f_paths_one": "%(n)s chemin à deux facteurs",
    },
}


def normalize(code: str | None) -> str:
    """'de-CH', 'DE', 'de' → 'de'. Sconosciuto → DEFAULT."""
    if not code:
        return DEFAULT
    base = code.strip().lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED else DEFAULT


def from_accept_language(header: str | None) -> str:
    """Prima lingua supportata in Accept-Language, in ordine di q decrescente."""
    if not header:
        return DEFAULT
    candidates = []
    for part in header.split(","):
        piece = part.strip()
        if not piece:
            continue
        tag, _, params = piece.partition(";")
        q = 1.0
        if params.startswith("q="):
            try:
                q = float(params[2:])
            except ValueError:
                q = 0.0
        base = tag.strip().lower().split("-")[0]
        if base in SUPPORTED:
            candidates.append((q, base))
    if not candidates:
        return DEFAULT
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def singular(n: int, t: dict[str, str]) -> bool:
    """Se questo numero vuole la forma singolare, nella lingua di chi legge.

    Italiano, inglese e tedesco dicono «0 sessioni»; il francese dice «0
    session». È l'unica differenza di plurale che queste quattro lingue hanno
    fra loro, quindi vale una riga di regola e non un motore di plurali.
    """
    return n == 1 or (n == 0 and t.get("plural_zero_singular") == "1")


def mail_error(err: str, t: dict[str, str]) -> str:
    """La frase per un errore di `mailer.send`, nella lingua di chi guarda.

    I fallimenti che il mailer sa nominare arrivano come codice (`smtp_off`,
    `auth_refused 535`); tutto il resto è il testo grezzo di una libreria, che
    resta com'è. Tradurre `ConnectError: [Errno 111]` non aiuterebbe nessuno e
    renderebbe l'errore impossibile da cercare.
    """
    if not err:
        return ""
    code, _, detail = err.partition(" ")
    text = t.get(f"adm_mail_{code}")
    if not text:
        return err
    return f"{text} ({detail})" if detail else text


def get_t(lang: str) -> dict[str, str]:
    """Dizionario della lingua, con l'italiano come rete di sicurezza per le
    chiavi che qualcuno ha dimenticato di tradurre."""
    chosen = normalize(lang)
    if chosen == DEFAULT:
        return TRANSLATIONS[DEFAULT]
    return {**TRANSLATIONS[DEFAULT], **TRANSLATIONS[chosen]}
