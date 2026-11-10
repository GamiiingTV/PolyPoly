"""Tests sans matériel audio ni appel réseau :  python -m pytest tests"""
import numpy as np

from souffleur.audio import TAUX, Segmenteur, reechantillonner
from souffleur.conseiller import analyser
from souffleur.memoire import Memoire, Personne, Replique
from souffleur.voix import RegistreVoix

rng = np.random.default_rng(0)


def _voix(freq, secondes):
    t = np.arange(int(TAUX * secondes)) / TAUX
    harm = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 8))
    vibrato = 1 + 0.3 * np.sin(2 * np.pi * 4 * t)
    return (0.2 * harm * vibrato / 3).astype(np.float32)


def _bruit(secondes, niveau=0.002):
    return (rng.standard_normal(int(TAUX * secondes)) * niveau).astype(np.float32)


def test_segmenteur_decoupe_deux_repliques():
    seg = Segmenteur(silence_fin_ms=500, duree_min_ms=300)
    flux = np.concatenate([_bruit(1), _voix(140, 1.2), _bruit(0.9), _voix(220, 0.8), _bruit(1)])
    morceaux = []
    for i in range(0, flux.size, 480):
        morceaux += seg.pousser(flux[i:i + 480])
    assert [g for g, _ in morceaux] == ["fin", "fin"]
    assert 1.0 < morceaux[0][1].size / TAUX < 1.9
    assert 0.6 < morceaux[1][1].size / TAUX < 1.5


def test_segmenteur_ignore_les_bruits_courts():
    seg = Segmenteur(silence_fin_ms=500, duree_min_ms=400)
    flux = np.concatenate([_bruit(1), _voix(150, 0.15), _bruit(1)])
    assert seg.pousser(flux) == []


def test_reechantillonnage():
    assert reechantillonner(np.ones(48000, np.float32), 48000).size == 16000
    assert abs(reechantillonner(np.ones(44100, np.float32), 44100).size - 16000) <= 1


def test_voix_distinctes():
    reg = RegistreVoix()
    a1 = reg.identifier(_voix(110, 2) + _bruit(2))
    b1 = reg.identifier(_voix(260, 2) + _bruit(2))
    a2 = reg.identifier(_voix(112, 2) + _bruit(2))
    assert a1 == a2 and a1 != b1
    reg.nommer(a1, "Kuno le forgeron")
    assert reg.nom(a1) == "Kuno le forgeron"


def test_analyse_reponse():
    texte = """SITUATION: Marchandage — un drapier veut vendre cher
QUI: le drapier de Kuttenberg
1. [Courtois] Votre drap est beau, maître, mais point à ce prix.
2. [Ferme] « Douze groschen, ou je vais voir ailleurs. »
3) [Rusé] On m'a dit qu'à Sasau, le même drap se vend moitié moins.
4. Je vous en sais gré, mais je dois y songer.
CONSEIL: Une aune de bon drap vaut quelques groschen, pas une soixantaine."""
    p = analyser(texte)
    assert p.situation.startswith("Marchandage")
    assert p.qui == "le drapier de Kuttenberg"
    assert [c.numero for c in p.choix] == [1, 2, 3, 4]
    assert p.choix[1].texte == "Douze groschen, ou je vais voir ailleurs."
    assert p.choix[3].ton == ""
    assert p.conseil.startswith("Une aune")


def test_memoire(tmp_path):
    m = Memoire(tmp_path)
    m.noter_scene("taverne · soir")
    assert "taverne" in m.texte_scenes()
    m.ajouter(Replique("interlocuteur", "Voix A", "Dieu vous garde, messire."))
    m.ajouter(Replique("moi", "Dalibor", "Et vous de même."))
    m.renommer("Voix A", "Kuno")
    assert "Kuno : Dieu vous garde" in m.texte_fil()
    m.fusionner([Personne("Kuno", "forgeron de Suchdol", "sujet")], ["Kuno doit 3 groschen."], "Début.")
    m2 = Memoire(tmp_path)
    assert "kuno" in m2.personnes and m2.faits == ["Kuno doit 3 groschen."]
    assert "forgeron de Suchdol" in m2.texte_registre()


def test_analyse_ligne_vu():
    p = analyser("SITUATION: Rixe — un ivrogne s'emporte\nVU: il tient une dague, deux gardes au fond\n1. [Calme] Rengainez, l'ami.")
    assert p.vu.startswith("il tient une dague") and len(p.choix) == 1


def test_image_difference():
    from souffleur.vision import Image
    a = Image(b"", np.zeros((27, 48), np.float32), 0)
    b = Image(b"", np.full((27, 48), 40, np.float32), 0)
    assert a.difference(None) > 100 and a.difference(a) == 0 and a.difference(b) == 40


def test_capture_ecran():
    import os
    import pytest
    if not os.environ.get("DISPLAY") and os.name != "nt":
        pytest.skip("pas d'écran")
    pytest.importorskip("mss")
    from souffleur.config import ConfigVision
    from souffleur.vision import Oeil
    img = Oeil(ConfigVision(largeur_max=640), print).capturer()
    assert img is not None and img.jpeg[:2] == b"\xff\xd8"
    assert img.bloc()["source"]["media_type"] == "image/jpeg"


def _decouper(seg, flux):
    sortie = []
    for i in range(0, flux.size, 480):
        sortie += seg.pousser(flux[i:i + 480])
    return sortie


def test_anticipation_simple():
    # Une phrase suivie d'un long silence : une seule réplique, envoyée dès 300 ms de silence.
    seg = Segmenteur(silence_fin_ms=700, duree_min_ms=300, anticipation_ms=300)
    flux = np.concatenate([_bruit(1), _voix(140, 1.0), _bruit(1.5)])
    sortie = _decouper(seg, flux)
    assert [g for g, _ in sortie] == ["fin"]


def test_anticipation_avec_reprise():
    # Pause de 450 ms au milieu de la phrase : envoi anticipé, puis « suite » avec le tout.
    seg = Segmenteur(silence_fin_ms=700, duree_min_ms=300, anticipation_ms=300)
    flux = np.concatenate([_bruit(1), _voix(140, 1.0), _bruit(0.45), _voix(140, 0.8), _bruit(1.5)])
    sortie = _decouper(seg, flux)
    assert [g for g, _ in sortie] == ["fin", "suite"]
    assert sortie[1][1].size > sortie[0][1].size + TAUX // 2


def test_profils():
    from souffleur.profil import Profil, lister
    from souffleur import prompts
    assert "dalibor" in lister() and "_modele" not in lister()
    p = Profil.charger("dalibor", "boheme_1403")
    assert p.nom == "Dalibor" and "1403" in p.cadre and "Suchdol" in p.vocabulaire
    systeme = prompts.systeme_souffleur(p)
    assert "{" not in systeme.split("=== FICHE")[0]          # gabarit entièrement rempli
    assert "Dalibor" in systeme and "anachronisme" in systeme


def test_images_pour_replique():
    from souffleur.config import ConfigVision
    from souffleur.vision import Image, Oeil
    import time as _t
    pytest = __import__("pytest")
    pytest.importorskip("mss")
    pytest.importorskip("PIL")
    oeil = Oeil(ConfigVision(), lambda t: None)
    maintenant = _t.monotonic()
    calme = Image(b"a", np.zeros((27, 48), np.float32), maintenant - 4)
    epee = Image(b"b", np.full((27, 48), 60, np.float32), maintenant - 0.1)
    oeil.images.extend([calme, epee])
    oeil._debut_parole = maintenant - 3.9
    images = oeil.pour_replique()
    assert [i for _, i in images] == [calme, epee]
    assert "commencé à parler" in images[0][0]
