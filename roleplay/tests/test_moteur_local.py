"""Le moteur local face à un faux serveur Ollama (même protocole HTTP que le vrai)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pydantic import BaseModel

from souffleur.config import ConfigLocal
from souffleur.moteurs import ErreurMoteur, MoteurLocal

REPONSE = "SITUATION: Taverne — un ivrogne cherche querelle\n1. [Calme] Paix, l'ami.\n2. [Ferme] Assez.\n"
recu = []


class Faux(BaseHTTPRequestHandler):
    modeles = ["gemma3:12b"]

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        corps = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        self._json({"models": [{"name": n} for n in self.modeles]})

    def do_POST(self):
        corps = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        recu.append((self.path, corps))
        if self.path == "/api/pull":
            Faux.modeles.append(corps["model"])
            lignes = [{"status": "pulling", "total": 100, "completed": c} for c in (0, 50, 100)]
            lignes.append({"status": "success"})
        elif corps.get("format"):
            self._json({"message": {"role": "assistant",
                                    "content": json.dumps({"lieu": "taverne", "tension": "vive"})}, "done": True})
            return
        else:
            morceaux = [REPONSE[i:i + 7] for i in range(0, len(REPONSE), 7)]
            lignes = [{"message": {"role": "assistant", "content": m}, "done": False} for m in morceaux]
            lignes.append({"message": {"role": "assistant", "content": ""}, "done": True})
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for l in lignes:
            self.wfile.write((json.dumps(l) + "\n").encode())


@pytest.fixture
def serveur():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Faux)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    recu.clear()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


class Scene(BaseModel):
    lieu: str
    tension: str


def test_flux_et_images(serveur):
    m = MoteurLocal(ConfigLocal(adresse=serveur), print)
    contenu = [{"type": "text", "text": "Image 1"},
               {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "QUJD"}},
               {"type": "text", "text": "Que dire ?"}]
    texte = "".join(m.flux("consignes", contenu))
    assert texte == REPONSE
    chemin, corps = recu[-1]
    assert chemin == "/api/chat" and corps["stream"] is True
    assert corps["messages"][0] == {"role": "system", "content": "consignes"}
    assert corps["messages"][1]["images"] == ["QUJD"]
    assert "Image 1" in corps["messages"][1]["content"] and corps["options"]["num_ctx"] >= 12000


def test_structure(serveur):
    m = MoteurLocal(ConfigLocal(adresse=serveur), print)
    s = m.structure("regard", "consignes", [{"type": "text", "text": "x"}], Scene)
    assert s == Scene(lieu="taverne", tension="vive")
    assert recu[-1][1]["format"]["properties"]["lieu"]["type"] == "string"
    m._repliques_en_cours = 1          # une réplique est en cours : la tâche de fond s'efface
    assert m.structure("regard", "c", [{"type": "text", "text": "x"}], Scene) is None


def test_preparer_telecharge_le_modele(serveur):
    journal = []
    m = MoteurLocal(ConfigLocal(adresse=serveur, modele="gemma3:4b"), journal.append)
    assert m.preparer()
    assert ("/api/pull", {"model": "gemma3:4b", "stream": True}) in recu
    assert any("100 %" in j for j in journal)


def test_ollama_absent():
    m = MoteurLocal(ConfigLocal(adresse="http://127.0.0.1:9"), print)
    with pytest.raises(ErreurMoteur, match="Ollama ne répond pas"):
        list(m.flux("s", [{"type": "text", "text": "x"}]))
    assert m.preparer() is False


def test_conseiller_avec_moteur_local(serveur):
    from souffleur.conseiller import Conseiller
    from souffleur.memoire import Memoire, Replique
    from souffleur.profil import Profil
    import tempfile, pathlib
    mem = Memoire(pathlib.Path(tempfile.mkdtemp()))
    mem.ajouter(Replique("interlocuteur", "Voix A", "Tu me regardes de travers, l'ami ?"))
    ev = []
    c = Conseiller(MoteurLocal(ConfigLocal(adresse=serveur), print), Profil.charger("dalibor", "boheme_1403"),
                   mem, 4, lambda t, d: ev.append((t, d)))
    c._generation = 1
    c._generer(1, "")
    assert ev[-1][0] == "fini"
    prop = ev[-1][1][0]
    assert prop.situation.startswith("Taverne") and [ch.ton for ch in prop.choix] == ["Calme", "Ferme"]


def test_choix_automatique_du_modele():
    from souffleur.moteurs import choisir_modele
    assert choisir_modele(32, 9) == "mistral-small3.1"     # RTX 5090
    assert choisir_modele(24, 9) == "gemma3:12b"           # RTX 4090 / 3090
    assert choisir_modele(16, 9) == "gemma3:4b"            # RTX 4080 / 4070 Ti Super
    assert choisir_modele(8, 9) == "gemma3:4b"
    assert choisir_modele(None, 9) == "gemma3:12b"
    assert choisir_modele(24, 4) == "mistral-small3.1"     # jeu en qualité réduite
