"""Tests MemeCrawler (hors ligne) : python -m pytest memecrawler/tests -q"""

import base64
import time

import httpx
import pytest

from memecrawler import settings
from memecrawler.filters import chain_kill, free_kill, soft_kill, trade_kill
from memecrawler.jev import JevAnswer
from memecrawler.models import Candidate, ChainReport
from memecrawler.sources import DexScreener, parse_pair, parse_report
from memecrawler.strategy import Position, Watch, entry_signal, exit_signal

NOW = int(time.time() * 1000)


def coin(**kw) -> Candidate:
    base = dict(mint="HIGGSmint", symbol="HIGGS", created_at_ms=NOW - 9 * 3600_000,
                price_usd=0.002, liquidity_usd=80_000, mcap_usd=2_000_000,
                volume_h24=500_000, trades_h24=4_000, buys_m5=30, sells_m5=10)
    base.update(kw)
    return Candidate(**base)


GOOD_SCORES = dict(concentration_is_exit_risk=0.2, momentum_already_spent=0.3,
                   liquidity_fits_ticket=0.9, account_is_the_project=0.85,
                   recycled_account=0.1, dev_still_loaded=0.1)


# ---------------- Parsing ----------------
def test_parse_pair():
    c = parse_pair({
        "dexId": "raydium", "pairAddress": "PAIR", "pairCreatedAt": NOW,
        "baseToken": {"address": "MINT", "symbol": "XEET", "name": "Xeet"},
        "quoteToken": {"symbol": "SOL"}, "priceUsd": "0.00017", "priceNative": "0.000001",
        "txns": {"m5": {"buys": 5, "sells": 2}, "h24": {"buys": 100, "sells": 90}},
        "volume": {"h24": 45000}, "priceChange": {"h1": -12.5},
        "liquidity": {"usd": 36000}, "marketCap": 165300,
        "info": {"socials": [{"type": "twitter", "url": "https://x.com/xeet"}]},
    })
    assert (c.mint, c.trades_h24, c.buys_m5, c.change_h1) == ("MINT", 190, 5, -12.5)
    assert c.mcap_usd == 165300 and c.socials[0]["type"] == "twitter"


def test_parse_report_excludes_pool():
    r = parse_report({
        "markets": [{"pubkey": "POOL", "liquidityA": "POOL_VAULT"}],
        "topHolders": [{"address": "POOL_VAULT", "pct": 40}, {"address": "W1", "pct": 4},
                       {"address": "W2", "pct": 3}],
        "token": {"supply": 1_000_000, "mintAuthority": None},
        "creatorBalance": 20_000, "totalHolders": 7000,
        "risks": [{"name": "Low liquidity", "level": "warn"}],
    })
    assert r.top_wallet == pytest.approx(0.04)
    assert r.top_10 == pytest.approx(0.07)
    assert r.creator_pct == pytest.approx(0.02)
    assert r.warn_risks == ["Low liquidity"] and not r.danger_risks


def test_dexscreener_latest_filters_solana():
    def handler(req: httpx.Request):
        if "profiles" in req.url.path:
            return httpx.Response(200, json=[{"chainId": "solana", "tokenAddress": "A"},
                                             {"chainId": "base", "tokenAddress": "B"}])
        return httpx.Response(200, json=[{"chainId": "solana", "tokenAddress": "A"},
                                         {"chainId": "solana", "tokenAddress": "C"}])
    dex = DexScreener(httpx.Client(transport=httpx.MockTransport(handler)))
    assert sorted(t["tokenAddress"] for t in dex.latest_solana_mints()) == ["A", "C"]


# ---------------- Filtre ----------------
def test_free_kill_young_coin_is_retried():
    v = free_kill(coin(created_at_ms=NOW - 5 * 60_000), NOW)
    assert v.stage == "free_kill" and v.retry


def test_hard_filters_pass_good_coin():
    assert free_kill(coin(), NOW) is None and trade_kill(coin()) is None


def test_trade_kill_low_trades():
    assert trade_kill(coin(trades_h24=100)).stage == "trade_kill"


@pytest.mark.parametrize("report,expected", [
    (ChainReport(top_wallet=0.08, top_10=0.3), "top wallet"),
    (ChainReport(top_wallet=0.04, top_10=0.65), "top 10"),
    (ChainReport(mint_authority="DEV"), "minter"),
    (ChainReport(danger_risks=["Single holder ownership"]), "risque"),
    (ChainReport(rugged=True), "rug"),
])
def test_chain_kill(report, expected):
    v = chain_kill(report)
    assert v.stage == "chain_kill" and expected in v.reason and not v.retry


def test_chain_pass():
    assert chain_kill(ChainReport(top_wallet=0.03, top_10=0.25)) is None


def test_soft_kill():
    assert soft_kill(GOOD_SCORES) is None
    assert "account_is_the_project" in soft_kill({**GOOD_SCORES, "account_is_the_project": 0.4}).reason
    assert "dev_still_loaded" in soft_kill({**GOOD_SCORES, "dev_still_loaded": 0.7}).reason


# ---------------- Stratégie ----------------
def test_no_entry_without_flush_then_entry_on_rebound():
    w = Watch("M", "HIGGS", time.time(), peak=2.23)
    assert entry_signal(w, coin(price_usd=2.10)) is None           # petite baisse : rien
    assert entry_signal(w, coin(price_usd=1.60)) is None           # flush -28 % : on attend
    assert w.flushed
    assert entry_signal(w, coin(price_usd=1.62, buys_m5=5, sells_m5=20)) is None  # vendeurs dominent
    assert entry_signal(w, coin(price_usd=1.70, buys_m5=25, sells_m5=10))          # rebond + acheteurs


def test_no_entry_when_halving_on_the_hour():
    w = Watch("M", "X", time.time(), peak=1.0, trough=0.4, flushed=True)
    assert entry_signal(w, coin(price_usd=0.45, change_h1=-55)) is None


def test_exits():
    now = time.time()
    pos = lambda: Position("M", "X", 1.0, 100, 100, now, 80_000, 1.0)
    assert "stop loss" in exit_signal(pos(), coin(price_usd=0.85), now)
    p = pos()
    assert exit_signal(p, coin(price_usd=1.40), now) is None
    assert "trailing" in exit_signal(p, coin(price_usd=1.20), now)
    assert "liquidité" in exit_signal(pos(), coin(price_usd=1.0, liquidity_usd=30_000), now)
    assert "durée" in exit_signal(pos(), coin(price_usd=1.05), now + 5 * 3600)


# ---------------- Bot complet (paper) ----------------
class FakeDex:
    def __init__(self):
        self.price = 0.002

    def latest_solana_mints(self):
        return [{"tokenAddress": "HIGGSmint", "description": "Higgs boson coin",
                 "links": [{"type": "twitter", "url": "https://x.com/higgs"}]}]

    def candidates(self, mints):
        return {m: coin(price_usd=self.price) for m in mints}

    def sol_usd(self):
        return 150.0


class FakeRug:
    def report(self, mint):
        return ChainReport(top_wallet=0.03, top_10=0.3, holders=7000)


class FakeJev:
    def __init__(self, verdict=True):
        self.verdict = verdict
        self.calls = 0

    def judge(self, c, ticket, now):
        self.calls += 1
        return JevAnswer(**GOOD_SCORES, verdict=self.verdict, reason="dev vide, holders sains")


@pytest.fixture
def bot(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    from memecrawler.bot import Bot
    b = Bot.__new__(Bot)
    b.http = None
    b.dex, b.rug, b.jev = FakeDex(), FakeRug(), FakeJev()
    b.notify = type("N", (), {"send": lambda self, t: None})()
    from memecrawler.executor import PaperExecutor
    from memecrawler.state import State
    b.exe, b.dry, b.state, b.sol_usd, b._last_crawl = PaperExecutor(), False, State(bank_usd=100.0), 150.0, 0
    return b


def test_full_cycle_paper(bot):
    bot.crawl()
    assert "HIGGSmint" in bot.state.watches and bot.state.stats["picks"] == 1
    bot.crawl()
    assert bot.jev.calls == 1                       # déjà vu : Jev n'est pas rappelé

    for price in (0.0021, 0.0015, 0.0016):          # sommet, flush, rebond
        bot.dex.price = price
        bot.tick()
    pos = bot.state.position
    assert pos is not None and pos.cost_usd == pytest.approx(20.0)
    assert bot.state.bank_usd == pytest.approx(80.0)

    for price in (0.0022, 0.0019):                  # +37 % puis repli -14 % → trailing
        bot.dex.price = price
        bot.tick()
    assert bot.state.position is None
    t = bot.state.trades[-1]
    assert "trailing" in t["reason"] and t["pnl"] > 0
    assert not bot.state.watches["HIGGSmint"].flushed   # il faudra un nouveau flush


def test_jev_says_no(bot):
    bot.jev = FakeJev(verdict=False)
    bot.crawl()
    assert not bot.state.watches and bot.state.stats["killed"]["soft_kill"] == 1


def test_stop_file_blocks_buys(bot):
    bot.crawl()
    settings.STOP_FILE.write_text("")
    for price in (0.0021, 0.0015, 0.0016):
        bot.dex.price = price
        bot.tick()
    assert bot.state.position is None


# ---------------- Signature live ----------------
def test_sign_transaction():
    from solders.hash import Hash
    from solders.keypair import Keypair
    from solders.message import MessageV0
    from solders.system_program import TransferParams, transfer
    from solders.transaction import VersionedTransaction
    from memecrawler.executor import sign_transaction

    kp = Keypair()
    ix = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=Keypair().pubkey(), lamports=1))
    msg = MessageV0.try_compile(kp.pubkey(), [ix], [], Hash.default())
    from solders.signature import Signature
    unsigned = VersionedTransaction.populate(msg, [Signature.default()])
    out = VersionedTransaction.from_bytes(base64.b64decode(
        sign_transaction(base64.b64encode(bytes(unsigned)).decode(), kp)))
    assert out.verify_with_results() == [True]
