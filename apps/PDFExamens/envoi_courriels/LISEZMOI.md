# Envoi des courriels d'examen

0. Au lancement, une fenêtre s'ouvre pour choisir `Recapitulatif_etudiants.xlsx` (elle s'ouvre dans le dernier dossier utilisé ; `--recap fichier.xlsx` la remplace). Ce dossier est dans le dépôt SitePerso : `.gitignore` empêche de publier `envois_log.csv` (NI, courriels).
1. Ouvre OneDrive (le récapitulatif doit être téléchargé sur le Mac, pas « en ligne seulement »).
2. Relis `gabarit.txt` (texte, date, signature). Champs : {prenom_nom} {ni} {local} {place} {section} {cours} {examen} {heure_debut} {heure_fin} {bloc_acc}.
3. Dans Terminal, depuis ce dossier :

```
python3 envoi_courriels.py                                   # essai à blanc : affiche un exemple, n'envoie rien
python3 envoi_courriels.py --brouillons --vers julien.miron@mat.ulaval.ca --limite 3   # 3 brouillons Outlook adressés à toi
python3 envoi_courriels.py --envoyer --vers julien.miron@mat.ulaval.ca --limite 3      # 3 vrais envois de test, à toi
python3 envoi_courriels.py --envoyer                         # envoi réel
```

- `envois_log.csv` garde la trace : relancer la commande ne renvoie pas aux étudiants déjà traités.
- Un étudiant sans courriel valide est signalé et sauté. Aucune pièce jointe n'est envoyée.
- `--ni 12345678` cible un étudiant ; `--backend mail` utilise Apple Mail .

## Test complet (9 étudiants fictifs, adresses à toi)
```
python3 envoi_courriels.py --recap Recapitulatif_etudiants_TEST.xlsx --log test_log.csv
python3 envoi_courriels.py --recap Recapitulatif_etudiants_TEST.xlsx --log test_log.csv --envoyer
```
(3 réguliers, 3 accommodements, 3 hors campus ; `--limite 1` pour n'en envoyer qu'un.)
