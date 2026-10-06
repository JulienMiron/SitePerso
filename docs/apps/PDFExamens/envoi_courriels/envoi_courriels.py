#!/usr/bin/env python3
"""
Envoi automatique des courriels de places d'examen .

Lit  Recapitulatif_etudiants.xlsx  (généré par l'app PDFExamens), remplit le gabarit
gabarit.txt et envoie un courriel par étudiant via Outlook (ou Apple Mail), 

Aucune dépendance à installer : Python 3 standard (macOS) seulement.

Usage typique (voir LISEZMOI.md) :
    python3 envoi_courriels.py                                  # essai à blanc : rien n'est envoyé
    python3 envoi_courriels.py --envoyer --vers moi@ulaval.ca --limite 3   # test sur toi-même
    python3 envoi_courriels.py --envoyer                        # envoi réel
"""
import argparse
import csv
import datetime as dt
import re
import subprocess
import sys
import time
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ICI = Path(__file__).resolve().parent
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
COLONNES = ["PrénomNom", "NI", "Place", "Local", "Section", "ACC", "Cours", "Examen",
            "Heure début", "Heure fin", "Courriel", "Hors campus"]


# ----------------------------------------------------------------------------- lecture xlsx
def _col_index(ref):
    lettres = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for c in lettres:
        n = n * 26 + ord(c) - 64
    return n - 1


def lire_xlsx(chemin):
    """Retourne la première feuille sous forme de liste de lignes (listes de chaînes)."""
    with zipfile.ZipFile(chemin) as z:
        partages = []
        if "xl/sharedStrings.xml" in z.namelist():
            racine = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in racine.findall("m:si", NS):
                partages.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        noms = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        feuille = ET.fromstring(z.read(noms[0]))
    lignes = []
    for row in feuille.iter("{%s}row" % NS["m"]):
        valeurs = {}
        for c in row.findall("m:c", NS):
            t = c.get("t")
            v = c.find("m:v", NS)
            if t == "inlineStr":
                txt = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is None or v.text is None:
                txt = ""
            elif t == "s":
                txt = partages[int(v.text)]
            else:
                txt = v.text
            valeurs[_col_index(c.get("r"))] = txt
        if valeurs:
            lignes.append([valeurs.get(i, "") for i in range(max(valeurs) + 1)])
    return lignes


def heure_hhmm(v):
    """Accepte « 09:00 », « 9h00 » ou une fraction de jour Excel (0.375)."""
    v = (v or "").strip()
    try:
        f = float(v)
        if 0 <= f < 1:
            m = round(f * 24 * 60)
            return f"{m // 60:02d}h{m % 60:02d}"
    except ValueError:
        pass
    m = re.match(r"^(\d{1,2})[:h](\d{2})", v)
    return f"{int(m.group(1)):02d}h{m.group(2)}" if m else v


def charger_etudiants(chemin):
    lignes = lire_xlsx(chemin)
    entete = [h.strip() for h in lignes[0]]
    manquantes = [c for c in COLONNES if c not in entete]
    if manquantes:
        sys.exit(f"Colonnes introuvables dans le récapitulatif : {manquantes}\nTrouvé : {entete}")
    idx = {c: entete.index(c) for c in COLONNES}
    etudiants = []
    for l in lignes[1:]:
        l = l + [""] * (len(entete) - len(l))
        e = {c: l[idx[c]].strip() for c in COLONNES}
        if not (e["NI"] or e["PrénomNom"]):
            continue
        e["Heure début"] = heure_hhmm(e["Heure début"])
        e["Heure fin"] = heure_hhmm(e["Heure fin"])
        etudiants.append(e)
    return etudiants


# ----------------------------------------------------------------------------- gabarit
def charger_gabarit(chemin):
    """Sections [NORMAL], [HORS_CAMPUS], [BLOC_ACC]. La 1re ligne de NORMAL/HORS_CAMPUS : « Sujet: ... »."""
    sections, courante = {}, None
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[([A-Z_]+)\]\s*$", ligne)
        if m:
            courante = m.group(1)
            sections[courante] = []
        elif courante:
            sections[courante].append(ligne)
    out = {}
    for nom, lignes in sections.items():
        texte = "\n".join(lignes).strip("\n")
        if nom in ("NORMAL", "HORS_CAMPUS"):
            m = re.match(r"^Sujet:\s*(.*)\n+", texte + "\n")
            if not m:
                sys.exit(f"Le gabarit [{nom}] doit commencer par une ligne « Sujet: ... »")
            out[nom] = (m.group(1).strip(), texte[m.end():].strip("\n") if "\n" in texte else "")
        else:
            out[nom] = texte
    for requis in ("NORMAL", "HORS_CAMPUS", "BLOC_ACC"):
        if requis not in out:
            sys.exit(f"Section [{requis}] absente de {chemin.name}")
    return out


class _Defaut(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def composer(e, gabarit):
    hors = e["Hors campus"].upper() == "OUI"
    acc = e["ACC"].upper() == "ACC"
    sujet, corps = gabarit["HORS_CAMPUS" if hors else "NORMAL"]
    champs = _Defaut(
        prenom_nom=e["PrénomNom"], ni=e["NI"], place=e["Place"], local=e["Local"],
        section=e["Section"], cours=e["Cours"], examen=e["Examen"],
        heure_debut=e["Heure début"], heure_fin=e["Heure fin"], courriel=e["Courriel"],
        bloc_acc="", bloc_copie="",
    )
    champs["bloc_acc"] = gabarit["BLOC_ACC"].format_map(champs) if (acc and not hors) else ""
    # [BLOC_COPIE] : paragraphe sur la copie jointe, omis pour les ACC
    champs["bloc_copie"] = gabarit.get("BLOC_COPIE", "").format_map(champs) if not acc else ""
    corps = corps.format_map(champs)
    corps = re.sub(r"\n{3,}", "\n\n", corps).strip() + "\n"   # un bloc vide ne laisse pas de trou
    return sujet.format_map(champs), corps


# ----------------------------------------------------------------------------- envoi (AppleScript)
APPLESCRIPT = {
    "outlook": '''
on run argv
    set {sujet, corps, adresse, mode} to {item 1 of argv, item 2 of argv, item 3 of argv, item 4 of argv}
    tell application "Microsoft Outlook"
        set m to make new outgoing message with properties {subject:sujet, plain text content:corps}
        make new recipient at m with properties {email address:{address:adresse}}
        if mode is "envoyer" then
            send m
        else
            open m
        end if
    end tell
end run
''',
    "mail": '''
on run argv
    set {sujet, corps, adresse, mode} to {item 1 of argv, item 2 of argv, item 3 of argv, item 4 of argv}
    tell application "Mail"
        set m to make new outgoing message with properties {subject:sujet, content:corps & return & return, visible:(mode is not "envoyer")}
        tell m to make new to recipient at end of to recipients with properties {address:adresse}
        if mode is "envoyer" then send m
    end tell
end run
''',
}


def envoyer(backend, mode, sujet, corps, adresse):
    r = subprocess.run(
        ["osascript", "-e", APPLESCRIPT[backend], sujet, corps, adresse, mode],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "osascript a échoué")


# ----------------------------------------------------------------------------- choix du fichier
DERNIER = ICI / ".dernier_dossier"


def choisir_recap():
    """Ouvre la fenêtre macOS « Choisir un fichier » (dans le dernier dossier utilisé)."""
    debut = ""
    if DERNIER.exists():
        d = DERNIER.read_text(encoding="utf-8").strip()
        if Path(d).is_dir():
            debut = f' default location (POSIX file "{d}" as alias)'
    script = ('POSIX path of (choose file with prompt "Choisir Recapitulatif_etudiants.xlsx"'
              f'{debut})')
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("Aucun fichier choisi." if "-128" in r.stderr else f"Sélecteur de fichier impossible : {r.stderr.strip()}")
    chemin = Path(r.stdout.strip())
    DERNIER.write_text(str(chemin.parent), encoding="utf-8")
    return chemin


# ----------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recap", type=Path, default=None,
                    help="Recapitulatif_etudiants.xlsx (défaut : une fenêtre te laisse choisir le fichier)")
    ap.add_argument("--gabarit", type=Path, default=ICI / "gabarit.txt")
    ap.add_argument("--log", type=Path, default=ICI / "envois_log.csv")
    ap.add_argument("--backend", choices=["outlook", "mail"], default="outlook")
    ap.add_argument("--envoyer", action="store_true", help="envoie réellement (sinon : essai à blanc)")
    ap.add_argument("--brouillons", action="store_true", help="ouvre chaque courriel dans Outlook sans l'envoyer")
    ap.add_argument("--vers", help="adresse de test : tous les courriels vont à cette adresse")
    ap.add_argument("--limite", type=int, help="n'traiter que les N premiers étudiants")
    ap.add_argument("--ni", action="append", help="ne traiter que ce NI (répétable)")
    ap.add_argument("--pause", type=float, default=2.0, help="secondes entre deux envois (défaut 2)")
    a = ap.parse_args()

    # récapitulatif : option --recap, sinon fenêtre de sélection de fichier
    recap = a.recap or choisir_recap()
    if not recap.exists():
        sys.exit(f"Fichier introuvable : {recap}")
    try:
        with recap.open("rb") as f:
            f.read(4)
    except OSError as ex:
        sys.exit(f"Impossible de lire {recap.name} ({ex}).\n"
                 "Si le fichier est dans OneDrive : ouvre OneDrive, clic droit sur le fichier > "
                 "« Toujours conserver sur cet appareil », attends la fin du téléchargement, puis relance.")

    etudiants = charger_etudiants(recap)
    gabarit = charger_gabarit(a.gabarit)
    if a.ni:
        etudiants = [e for e in etudiants if e["NI"] in a.ni]

    deja = set()
    if a.log.exists() and not a.vers:      # les envois de test n'empêchent pas l'envoi réel
        with a.log.open(encoding="utf-8") as f:
            deja = {r["NI"] for r in csv.DictReader(f) if r["statut"] == "envoyé"}

    reel = a.envoyer or a.brouillons
    mode = "envoyer" if a.envoyer else "brouillon"
    print(f"Récapitulatif : {recap}\n"
          f"{len(etudiants)} étudiants — mode : "
          f"{'ENVOI RÉEL' if a.envoyer else 'brouillons' if a.brouillons else 'essai à blanc (rien envoyé)'}"
          f"{' — vers ' + a.vers if a.vers else ''}\n")

    nouveau_log = not a.log.exists()
    f_log = a.log.open("a", newline="", encoding="utf-8") if (reel and not a.vers) else None
    w = csv.writer(f_log) if f_log else None
    if w and nouveau_log:
        w.writerow(["horodatage", "NI", "nom", "courriel", "statut", "détail"])

    stats = {"envoyé": 0, "sauté": 0, "erreur": 0}
    traites = 0
    for e in etudiants:
        if a.limite and traites >= a.limite:
            break
        hors = e["Hors campus"].upper() == "OUI"
        adresse = a.vers or e["Courriel"]

        def noter(statut, detail=""):
            stats["envoyé" if statut == "envoyé" else "erreur" if statut == "erreur" else "sauté"] += 1
            print(f"  [{statut}] {e['PrénomNom']} ({e['NI']}) {detail}")
            if w:
                w.writerow([dt.datetime.now().isoformat(timespec="seconds"), e["NI"], e["PrénomNom"],
                            adresse, statut, detail])
                f_log.flush()

        if e["NI"] in deja:
            noter("déjà envoyé"); continue
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", adresse or ""):
            noter("erreur", f"adresse invalide : « {adresse} »"); continue
        sujet, corps = composer(e, gabarit)
        traites += 1
        if not reel:
            if traites == 1:
                print("=" * 70, f"\nÀ : {adresse}\nSujet : {sujet}\n\n{corps}" + "=" * 70)
            noter("à blanc", f"→ {adresse}")
            continue
        try:
            envoyer(a.backend, mode, sujet, corps, adresse)
            noter("envoyé" if a.envoyer else "brouillon", f"→ {adresse}")
            if a.envoyer:
                time.sleep(a.pause)
        except Exception as ex:
            noter("erreur", str(ex))

    if f_log:
        f_log.close()
    print(f"\nTerminé : {stats['envoyé']} envoyé(s), {stats['sauté']} traité(s) à blanc/sauté(s), {stats['erreur']} erreur(s).")
    if not reel:
        print("Rien n'a été envoyé. Ajoute --envoyer quand tout est correct.")


if __name__ == "__main__":
    main()
