import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.core.benchmark import test_resolver
from src.core.switcher import apply_linux_dns, get_current_dns

logger = logging.getLogger("flashy-dns-daemon")


class DNSAutoManager:
    def __init__(
        self,
        candidates: Optional[List[str]] = None,
        interval_seconds: int = 300,
        domain: str = "example.com",
        hysteresis_margin: float = 0.20,
    ):
        self.candidates = candidates or [
            "1.1.1.1",
            "8.8.8.8",
            "9.9.9.9",
            "208.67.222.222",
            "94.140.14.14",
        ]
        self.interval = interval_seconds
        self.domain = domain
        self.hysteresis_margin = hysteresis_margin
        self.current_primary: Optional[str] = None
        self.last_results: List[Dict[str, Any]] = []
        self.enabled = False
        self._task: Optional[asyncio.Task] = None

    async def evaluate_and_switch(self) -> Dict[str, Any]:
        current_system_dns = get_current_dns()
        if current_system_dns:
            self.current_primary = current_system_dns[0]
        elif not self.current_primary:
            self.current_primary = self.candidates[0]

        tasks = [
            test_resolver(r, domain=self.domain, attempts=3)
            for r in self.candidates
        ]
        results = await asyncio.gather(*tasks)
        self.last_results = results

        valid = [r for r in results if r["success"] > 0 and r["avg_latency"] is not None]
        if not valid:
            logger.warning("All candidate DNS benchmarks failed. Keeping current setup.")
            return {"status": "unchanged", "reason": "all_failed"}

        valid.sort(key=lambda x: x["avg_latency"])
        best = valid[0]

        current_entry = next(
            (r for r in valid if r["resolver"] == self.current_primary), None
        )

        should_switch = False
        reason = ""

        if not current_entry:
            should_switch = True
            reason = "Current resolver failed benchmark"
        elif best["resolver"] != self.current_primary:
            current_lat = current_entry["avg_latency"]
            best_lat = best["avg_latency"]
            threshold = current_lat * (1.0 - self.hysteresis_margin)

            if best_lat < threshold:
                gain_ms = round(current_lat - best_lat, 2)
                should_switch = True
                reason = f"Significantly faster: -{gain_ms}ms (>20% gain)"
            else:
                reason = "Best resolver is within hysteresis tolerance margin"
        else:
            reason = "Current resolver is already the fastest"

        action_result = {
            "status": "unchanged",
            "current": self.current_primary,
            "best": best["resolver"],
            "reason": reason,
        }

        if should_switch and best["resolver"] != self.current_primary:
            success, msg = apply_linux_dns(best["resolver"])
            if success:
                logger.info(f"Switched DNS: {self.current_primary} -> {best['resolver']} ({reason})")
                self.current_primary = best["resolver"]
                action_result["status"] = "switched"
                action_result["message"] = msg
            else:
                logger.error(f"Switch failed: {msg}")
                action_result["status"] = "error"
                action_result["message"] = msg

        return action_result

    async def _loop(self) -> None:
        while self.enabled:
            try:
                await self.evaluate_and_switch()
            except Exception as exc:
                logger.error(f"Error in daemon loop: {exc}")
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        if not self.enabled:
            self.enabled = True
            self._task = asyncio.create_task(self._loop())
            logger.info(f"DNS daemon started (Interval: {self.interval}s)")

    def stop(self) -> None:
        self.enabled = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("DNS daemon stopped")

    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "interval": self.interval,
            "current_primary": self.current_primary or (get_current_dns()[:1] or [None])[0],
            "candidates": self.candidates,
            "last_results": self.last_results,
        }
