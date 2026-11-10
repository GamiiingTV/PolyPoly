# ✠ Le Souffleur

Comme le souffleur au théâtre : il **écoute** ce qu'on dit à ton personnage dans le chat vocal du jeu et te **propose des répliques d'époque**, dans une petite fenêtre posée par-dessus le jeu.

Fait pour **Dalibor Medved, seigneur de Suchdol**, en **Bohême, 1403** (mod multijoueur de *Kingdom Come: Deliverance II*).

![Aperçu](docs/apercu.png)

## Comment ça marche

```
Chat vocal du jeu ──► capture du son du PC ──► découpe en répliques ──► Whisper (sur ta carte graphique)
Ton micro ────────────► (ce que Dalibor répond) ┘                               │
                                                                               ▼
     Fenêtre par-dessus le jeu ◄── 3 à 6 répliques (en flux) ◄── Claude (fiche de Dalibor + guide 1403 + mémoire)
```

1. Il écoute **le son qui sort de ton PC**, donc le chat vocal du jeu. Il écoute aussi **ton micro**, pour savoir ce que Dalibor a répondu.
2. Dès que ton interlocuteur se tait (environ une demi-seconde de silence), la réplique est transcrite **sur ton PC** (Whisper, sur la carte graphique).
3. Claude propose **4 répliques** de tons différents, adaptées à la scène : marchand, menace, ennemi, clerc, supérieur ou paysan. Les choix apparaissent **un par un**, au fur et à mesure qu'ils sont écrits : tu peux lire le premier pendant que les autres arrivent.
4. Une **chronique** tourne en arrière-plan. Elle retient les personnes rencontrées, les promesses, les dettes et les menaces, et sert de mémoire d'une session à l'autre (fichier `memoire/registre.json`).

## Installation (Windows)

1. Installe **Python 3.12** depuis [python.org](https://www.python.org/downloads/) en cochant **« Add python.exe to PATH »**.
2. Crée une clé API sur [console.anthropic.com](https://console.anthropic.com) (rubrique *API Keys*) et approvisionne quelques euros de crédit.
3. Double-clique sur **`lancer.bat`**. La première fois, il installe tout (quelques minutes), puis il ouvre le Bloc-notes sur le fichier `.env` : remplace `sk-ant-...` par ta clé, enregistre, ferme, et relance `lancer.bat`.
4. Au premier lancement, le modèle de transcription (environ 1,6 Go) se télécharge tout seul.

> **Important** : mets le jeu en mode **« Fenêtré sans bordure »** (Borderless), sinon la fenêtre du Souffleur ne peut pas s'afficher par-dessus le jeu en plein écran exclusif.

### Essayer sans le jeu

`lancer.bat --simulation` ouvre la fenêtre sans écouter le son. Tape une réplique, par exemple *« Halte-là ! Qui va là ? »*, puis appuie sur Entrée.

## Utilisation en jeu

| Touche | Effet |
|---|---|
| **F8** | Afficher ou cacher la fenêtre |
| **F9** | Nouvelles répliques pour la même réplique entendue |
| **F10** | Pause ou reprise de l'écoute (pendant une scène hors RP, une pause, une vidéo…) |

- **Clic sur une réplique** : elle est copiée dans le presse-papiers.
- **La fenêtre se déplace** en la tirant par sa barre de titre.

Le **champ en bas** de la fenêtre sert à guider l'outil :

| Tu écris | Effet |
|---|---|
| `! Taverne de Kuttenberg, je cherche un forgeron` | Note la **situation** : Claude en tient compte pour toute la scène |
| `? plus menaçant` / `? en latin` / `? refuse poliment` | Redemande des répliques **dans un autre sens** |
| `Voix A = Kuno le forgeron` | Donne un **nom** à une voix reconnue |
| `moi: Je vous en sais gré, messire.` | Note ce que **Dalibor** a dit (si le micro n'est pas écouté) |
| n'importe quel autre texte | Ajoute une réplique **entendue**, par exemple quand la transcription a raté un mot |

## Personnaliser

- **`donnees/personnage.md`** : la fiche de Dalibor. **Complète-la** avec sa famille, ses armoiries, ses hommes, ses secrets et ce qui se passe dans ton RP. Plus elle est riche, plus les répliques te ressembleront. L'outil ne s'invente jamais de faits importants qui n'y figurent pas.
- **`donnees/boheme_1403.md`** : le guide historique, avec la situation politique, les formules de politesse, la monnaie, la liste d'anachronismes interdits et le vocabulaire d'époque. Si ton serveur a son propre lore, ajoute-le ici : c'est le serveur qui a raison.
- **`config.toml`** : le modèle, la vivacité, le nombre de choix et les touches. Les réglages utiles :
  - `silence_fin_ms` : baisse-le (par exemple à 450) pour plus de vivacité ; monte-le si l'outil coupe les gens qui hésitent.
  - `sensibilite` : monte-la (à 4 ou 5) si la musique ou l'ambiance du jeu déclenchent l'écoute.
  - `modele = "claude-haiku-5-5"` : beaucoup plus rapide et bien moins cher, mais un style moins fin. `rapide = true` garde Opus mais en plus rapide, pour un prix doublé.

## Écouter seulement le chat vocal (conseillé)

Par défaut, l'outil écoute **tout** le son du PC : la voix des autres joueurs, mais aussi les PNJ et la musique. Pour qu'il n'entende que les joueurs :

- **Si le mod permet de choisir la sortie du chat vocal** : installe [VB-CABLE](https://vb-audio.com/Cable/) (gratuit), envoie le chat vocal vers « CABLE Input », active « Écouter ce périphérique » dans les propriétés Windows de « CABLE Output » pour l'entendre toi aussi, puis mets `sortie = "CABLE"` dans `config.toml`.
- **Sinon** : baisse la musique et les voix des PNJ dans les options du jeu, et monte `sensibilite`.

`lancer.bat --peripheriques` affiche la liste des périphériques audio.

## Bon à savoir

- **Coût** : chaque série de répliques coûte environ 2 centimes avec Opus, et bien moins avec Haiku. Une soirée de RP animée (environ 200 répliques entendues) revient à quelques euros avec Opus. La chronique ne s'exécute que toutes les 8 répliques.
- **Reconnaissance des voix** : elle est approximative. Elle distingue bien des voix différentes, moins bien des voix proches. Nomme les voix (`Voix A = …`) ; Claude devine aussi qui parle d'après le contexte.
- **Vie privée** : le son ne quitte jamais ton PC. Seul le **texte** transcrit est envoyé à Claude. Les transcriptions de chaque session sont gardées dans `memoire/sessions/`.
- **Carte graphique** : la transcription fonctionne au mieux avec une carte NVIDIA. Sans elle, l'outil bascule tout seul sur le processeur, en plus lent.

## Pour les curieux (structure)

```
souffleur/
  audio.py          capture WASAPI (son du PC + micro) et découpe en répliques
  transcription.py  Whisper local (faster-whisper)
  voix.py           reconnaissance approximative de qui parle
  conseiller.py     appels à Claude : répliques en flux + chronique
  prompts.py        consignes données à Claude
  memoire.py        fil de la conversation, registre des personnes et des faits
  interface.py      fenêtre par-dessus le jeu
  app.py            assemble le tout
tests/              tests sans matériel :  python -m pytest tests
```
