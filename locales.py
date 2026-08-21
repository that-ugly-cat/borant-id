"""
Stringhe UI di Borant ID — it, en, de, fr.

Pattern allineato a `roompulse/app/locales.py` e a quello di ArguMap: un'unica
sorgente per tutte le stringhe, e ogni chiave va aggiunta in **tutte e quattro**
le lingue insieme. Una chiave mancante ricade sull'italiano invece di esplodere,
ma quello è un paracadute, non un permesso.

**Cosa è tradotto e cosa no.** Le superfici che vede una persona invitata:
login, secondo fattore, arruolamento, codici di backup, profilo, invito, reset,
la pagina «non hai accesso», l'elenco delle app. I pannelli `/admin` restano in
italiano: li usa una persona sola, e quattro lingue per quattro pagine
amministrative sarebbero righe da mantenere in cambio di niente. Stessa scelta
fatta a suo tempo per RoomPulse.

La lingua si sceglie con `/lang/{code}`, si ricorda in un cookie di un anno, e
al primo arrivo si indovina da `Accept-Language`.
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
        "tagline": "Accesso unico agli strumenti di ricerca",

        # comune
        "email": "Email",
        "password": "Password",
        "back": "Torna indietro",
        "save": "Salva",
        "cancel": "Annulla",

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
        "orcid_unknown_title": "Nessun account collegato",
        "orcid_unknown_body": "Quell'ORCID iD non è collegato a nessun account qui. Chiedi un "
                              "invito, e potrai accettarlo proprio con ORCID.",
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
        "tagline": "Single sign-on for the research tools",

        "email": "Email",
        "password": "Password",
        "back": "Go back",
        "save": "Save",
        "cancel": "Cancel",

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
        "orcid_unknown_title": "No account linked",
        "orcid_unknown_body": "That ORCID iD is not linked to any account here. Ask for an "
                              "invitation — you will be able to accept it with ORCID.",
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
        "tagline": "Einheitlicher Zugang zu den Forschungswerkzeugen",

        "email": "E-Mail",
        "password": "Passwort",
        "back": "Zurück",
        "save": "Speichern",
        "cancel": "Abbrechen",

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
        "forbidden_ask": "Zugriff anfragen",
        "forbidden_mine": "Meine Werkzeuge",
        "forbidden_sent_title": "Anfrage gesendet",
        "forbidden_sent_body": "Die Administration wurde benachrichtigt.",

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
        "profile_orcid_note": "Verknüpft können Sie sich mit ORCID statt mit einem Passwort "
                              "anmelden.",
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
        "orcid_unknown_title": "Kein Konto verknüpft",
        "orcid_unknown_body": "Diese ORCID iD ist hier mit keinem Konto verknüpft. Bitten Sie um "
                              "eine Einladung — Sie können sie mit ORCID annehmen.",
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
        "tagline": "Accès unique aux outils de recherche",

        "email": "Courriel",
        "password": "Mot de passe",
        "back": "Retour",
        "save": "Enregistrer",
        "cancel": "Annuler",

        "login_title": "Connexion",
        "login_sub": "Une seule entrée pour tous les outils sur borant.eu.",
        "login_enter": "Se connecter",
        "login_forgot": "Mot de passe oublié",
        "login_err": "Courriel ou mot de passe invalide.",
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
        "reset_sent": "Si cette adresse a un compte ici, un courriel avec le lien est parti. Il "
                      "expire dans une heure et ne sert qu'une fois.",
        "reset_privacy": "Nous ne vous disons pas si l'adresse existe : ce n'est pas à un "
                         "formulaire de le révéler. Si le courriel n'arrive pas, demandez à un "
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
        "orcid_unknown_title": "Aucun compte lié",
        "orcid_unknown_body": "Cet identifiant ORCID n'est lié à aucun compte ici. Demandez une "
                              "invitation — vous pourrez l'accepter avec ORCID.",
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


def get_t(lang: str) -> dict[str, str]:
    """Dizionario della lingua, con l'italiano come rete di sicurezza per le
    chiavi che qualcuno ha dimenticato di tradurre."""
    chosen = normalize(lang)
    if chosen == DEFAULT:
        return TRANSLATIONS[DEFAULT]
    return {**TRANSLATIONS[DEFAULT], **TRANSLATIONS[chosen]}
