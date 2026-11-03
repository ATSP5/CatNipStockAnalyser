"""Draws one theme's top picks as a horizontal bar chart of their scores."""

import os
import re
import unicodedata

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


class ScreenerChart:
    """[RankedPick] of one theme -> PNG in the screener output folder."""

    BAR = "#1e88e5"
    BAR_TOP = "#1b7f3b"
    INK = "#2b2b2b"
    MUTED = "#6d6d6d"
    GRID_COLOUR = "#9e9e9e"

    def __init__(self, screener_settings):
        self.screener_settings = screener_settings

    def screener_chart(self):
        return self

    def draw(self, theme, picks):
        """Render and save; returns the file path, or None for no picks."""
        if not picks or not self.screener_settings.draw_chart:
            return None
        ordered = list(reversed(picks))            # best at the top
        height = 1.2 + 0.48 * len(ordered)
        figure, axis = plt.subplots(figsize=(12, height))
        positions = range(len(ordered))
        colours = [self.BAR_TOP if p.rank <= 3 else self.BAR for p in ordered]
        axis.barh(list(positions), [p.score for p in ordered], color=colours,
                  height=0.62, zorder=3)
        axis.set_yticks(list(positions))
        axis.set_yticklabels(["%d. %s  %s" % (p.rank, p.ticker, p.candidate.name[:28])
                              for p in ordered], fontsize=9)
        for y, pick in zip(positions, ordered):
            axis.text(pick.score + 0.8, y, self._annotation(pick), va="center",
                      fontsize=8, color=self.MUTED, zorder=4)
        axis.set_xlim(0, 128)
        axis.set_xticks(range(0, 101, 10))
        axis.set_xlabel("wynik 0-100 (średnia ważona percentyli w temacie)", fontsize=9)
        axis.grid(True, axis="x", which="major", color=self.GRID_COLOUR,
                  alpha=0.55, linewidth=0.8)
        axis.set_axisbelow(True)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        axis.set_title("%s -- top %d na 1-6 mies." % (theme, len(picks)),
                       loc="left", fontsize=12, fontweight="bold", color=self.INK)
        figure.tight_layout()
        return self._save(figure, theme)

    def _annotation(self, pick):
        factors = pick.candidate.factors
        parts = ["%.0f" % pick.score]
        momentum = factors.get("momentum_6_1")
        if momentum is not None:
            parts.append("6M %+.0f%%" % (100 * momentum))
        upside = factors.get("analyst_upside")
        if upside is not None:
            parts.append("cel %+.0f%%" % (100 * upside))
        if pick.candidate.forecast_change_pct is not None:
            parts.append("AI %+.0f%%" % pick.candidate.forecast_change_pct)
        return "  ".join(parts)

    def _save(self, figure, theme):
        directory = self.screener_settings.ensure_output_dir()
        plain = unicodedata.normalize("NFKD", theme.replace("ł", "l").replace("Ł", "L"))
        slug = re.sub(r"[^A-Za-z0-9]+", "_", plain.encode("ascii", "ignore")
                      .decode()).strip("_") or "theme"
        path = os.path.join(directory, "top_%s.png" % slug)
        figure.savefig(path, dpi=110, facecolor="white")
        if getattr(plt.show, "__module__", "") != "matplotlib.pyplot":
            plt.show()
        plt.close(figure)
        return path
