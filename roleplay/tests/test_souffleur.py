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
    assert len(morceaux) == 2
    assert 1.0 < morceaux[0].size / TAUX < 1.9
    assert 0.6 < morceaux[1].size / TAUX < 1.5


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
