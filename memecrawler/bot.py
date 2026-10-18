"""
MemeCrawler — La boucle : le crawler lit, Jev juge, les bots achètent et vendent.

CRAWLER : trouve les nouveaux coins et les passe dans le filtre.
CHIEF   : ne prend jamais de position, il choisit les picks (watchlist).
FILLS   : une seule position à la fois, jamais deux.
RISK    : stop loss, trailing, limite de perte journalière, fichier STOP.
"""

import time
from typing import Optional

import httpx
from loguru import logger

from . import settings
from .executor import LiveExecutor, PaperExecutor
from .filters import chain_kill, free_kill, soft_kill, trade_kill
from .jev import Jev
from .models import Candidate, Verdict
from .sources import DexScreener, RugCheck
from .state import State
from .strategy import Position, Watch, entry_signal, exit_signal, reset_after_exit


def now_ms() -> int:
    return int(time.time() * 1000)


class Notifier:
    def __init__(self, http: httpx.Client):
        self.http = http
        self.enabled = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)

    def send(self, text: str):
        logger.info(text)
        if not self.enabled:
            return
        try:
            self.http.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text})
        except Exception as e:
            logger.warning(f"Telegram : {e}")


class Bot:
    def __init__(self, live: bool, dry: bool = False):
        self.http = httpx.Client(timeout=20, headers={"User-Agent": "memecrawler/1.0"})
        self.dex = DexScreener(self.http)
        self.rug = RugCheck(self.http)
        self.jev = Jev()
        self.notify = Notifier(self.http)
        self.exe = LiveExecutor(self.http) if live else PaperExecutor()
        self.dry = dry           # True = crawl + juge seulement, aucun ordre
        self.state = State.load()
        self.sol_usd = 0.0
        self._last_crawl = 0.0

    # ================= Taille =================
    def bank_usd(self) -> float:
        if self.exe.live:
            return max(0.0, self.exe.sol_balance() - settings.SOL_RESERVE) * self.sol_usd
        return self.state.bank_usd

    def ticket_usd(self, bank: float, c: Optional[Candidate] = None) -> float:
        t = min(bank * settings.TICKET_PCT, settings.MAX_TICKET_USD)
        if c is not None and c.liquidity_usd:
            t = min(t, c.liquidity_usd * settings.MAX_TICKET_LIQ_PCT)
        return t

    # ================= Crawler + filtre =================
    def crawl(self):
        now = time.time()
        for m in [m for m, s in self.state.seen.items() if now - s["first"] > 86_400]:
            del self.state.seen[m]
        profiles = {p["tokenAddress"]: p for p in self.dex.latest_solana_mints()}
        due = [m for m in profiles if self._due(m, now)]
        due += [m for m, s in self.state.seen.items()
                if m not in profiles and s.get("next") and s["next"] <= now
                and now - s["first"] < settings.RETRY_WINDOW_H * 3600]
        if not due:
            return
        cands = self.dex.candidates(due)
        bank = self.bank_usd()
        for mint in due:
            c = cands.get(mint)
            if c is None:
                self._mark(mint, Verdict(False, "free_kill", "aucune paire", retry=True))
                continue
            p = profiles.get(mint) or {}
            c.description = p.get("description", "") or c.description
            for link in p.get("links") or []:
                if link.get("url") and link not in c.socials:
                    c.socials.append({"type": link.get("type") or link.get("label"), "url": link["url"]})
            self.state.stats["scanned"] += 1
            v = self.evaluate(c, self.ticket_usd(bank, c))
            self._mark(mint, v)
            if v.passed:
                self.state.stats["picks"] += 1
                self.state.watches[mint] = Watch(mint, c.symbol, now, peak=c.price_usd)
                self.notify.send(f"🕷️ PICK {c.symbol} — mcap {c.mcap_usd:,.0f} $, "
                                 f"liq {c.liquidity_usd:,.0f} $ — {v.reason}\n"
                                 f"https://dexscreener.com/solana/{c.pair_address}")
        self.state.save()

    def evaluate(self, c: Candidate, ticket: float) -> Verdict:
        n = now_ms()
        v = free_kill(c, n) or trade_kill(c)
        if v:
            return v
        c.chain = self.rug.report(c.mint)
        v = chain_kill(c.chain)
        if v:
            return v
        a = self.jev.judge(c, ticket, n)
        if a is None:
            return Verdict(False, "soft_kill", "Jev indisponible", retry=True)
        v = soft_kill(a.model_dump())
        if v:
            return v
        if not a.verdict:
            return Verdict(False, "soft_kill", f"Jev a dit non : {a.reason}")
        return Verdict(True, "pick", f"Jev a dit oui : {a.reason}")

    def _due(self, mint: str, now: float) -> bool:
        s = self.state.seen.get(mint)
        return s is None or bool(s.get("next") and s["next"] <= now)

    def _mark(self, mint: str, v: Verdict):
        now = time.time()
        s = self.state.seen.setdefault(mint, {"first": now})
        s["next"] = now + settings.RETRY_AFTER_MIN * 60 if v.retry else None
        if not v.passed:
            self.state.record_kill(v.stage)
            logger.debug(f"✗ {mint[:8]} {v.stage} : {v.reason}")

    # ================= Trading =================
    def tick(self):
        st = self.state
        st.roll_day()
        now = time.time()
        for m in [m for m, w in st.watches.items() if now - w.picked_at > settings.WATCH_HOURS * 3600]:
            if not (st.position and st.position.mint == m):
                del st.watches[m]
        mints = list(st.watches) + ([st.position.mint] if st.position else [])
        if not mints:
            return
        data = self.dex.candidates(list(dict.fromkeys(mints)))

        if st.position:
            c = data.get(st.position.mint)
            if c:
                reason = exit_signal(st.position, c, now)
                if reason:
                    self.close(c, reason)
            st.save()
            return

        if self.dry or settings.STOP_FILE.exists():
            return
        if st.day_pnl <= -settings.DAILY_LOSS_LIMIT_USD:
            return
        for mint, w in st.watches.items():
            c = data.get(mint)
            if not c:
                continue
            reason = entry_signal(w, c)
            if reason and self.open(c, reason):
                break
        st.save()

    def open(self, c: Candidate, reason: str) -> bool:
        ticket = self.ticket_usd(self.bank_usd(), c)
        if ticket < 1:
            logger.warning("Ticket < 1 $, bank trop faible")
            return False
        fill = self.exe.buy(c, ticket, self.sol_usd)
        if not fill:
            return False
        if not self.exe.live:
            self.state.bank_usd -= fill.usd
        self.state.position = Position(
            mint=c.mint, symbol=c.symbol, entry_price=fill.price, qty=fill.qty,
            cost_usd=fill.usd, opened_at=time.time(), entry_liquidity=c.liquidity_usd,
            high=fill.price, qty_raw=fill.qty_raw)
        self.notify.send(f"🟢 ACHAT {c.symbol} {fill.usd:.2f} $ à mcap {c.mcap_usd:,.0f} $ — {reason}")
        return True

    def close(self, c: Candidate, reason: str):
        pos = self.state.position
        fill = self.exe.sell(pos, c, self.sol_usd)
        if not fill:
            return   # on réessaiera au prochain tick
        pnl = fill.usd - pos.cost_usd
        if not self.exe.live:
            self.state.bank_usd += fill.usd
        self.state.day_pnl += pnl
        self.state.trades.append({
            "symbol": pos.symbol, "mint": pos.mint, "opened": pos.opened_at, "closed": time.time(),
            "cost": round(pos.cost_usd, 2), "out": round(fill.usd, 2), "pnl": round(pnl, 2),
            "reason": reason, "sig": fill.signature})
        self.state.position = None
        if c.mint in self.state.watches:
            reset_after_exit(self.state.watches[c.mint], c.price_usd)
        self.notify.send(f"{'🟢' if pnl >= 0 else '🔴'} VENTE {pos.symbol} {pnl:+.2f} $ "
                         f"({pnl / pos.cost_usd:+.1%}) — {reason}")

    # ================= Boucle =================
    def status(self) -> str:
        st = self.state
        k = st.stats.get("killed", {})
        pos = f"{st.position.symbol}" if st.position else "aucune"
        return (f"bank {self.bank_usd():.2f} $ | jour {st.day_pnl:+.2f} $ | position {pos} | "
                f"picks suivis {len(st.watches)} | scannés {st.stats['scanned']} | "
                f"tués free {k.get('free_kill', 0)} trade {k.get('trade_kill', 0)} "
                f"chain {k.get('chain_kill', 0)} soft {k.get('soft_kill', 0)}")

    def run(self, once: bool = False):
        mode = "LIVE 💸" if self.exe.live else "PAPER"
        logger.info(f"MemeCrawler démarré — mode {mode}{' (dry : aucun ordre)' if self.dry else ''}")
        if self.exe.live:
            logger.info(f"Wallet {self.exe.pubkey}")
        while True:
            try:
                self.sol_usd = self.dex.sol_usd() or self.sol_usd
                if time.time() - self._last_crawl >= settings.CRAWL_INTERVAL_S:
                    self._last_crawl = time.time()
                    self.crawl()
                    logger.info(self.status())
                self.tick()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.exception(f"Erreur de boucle : {e}")
            if once:
                return
            time.sleep(settings.TICK_INTERVAL_S)
