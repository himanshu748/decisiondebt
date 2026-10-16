import json
import re
from backend.app.settings import ROOT


class Catalog:
    def __init__(self, path=None):
        self.entities = json.loads(
            (path or ROOT / "data/synthetic/catalog.json").read_text()
        )["entities"]
        self.by_id = {e["id"]: e for e in self.entities}
        self.aliases = {}
        for e in self.entities:
            for alias in [e["id"], e["name"], *e.get("aliases", [])]:
                self.aliases.setdefault(alias.casefold(), set()).add(e["id"])
        self.pattern = re.compile(
            r"(?<!\w)("
            + "|".join(
                re.escape(a) for a in sorted(self.aliases, key=len, reverse=True)
            )
            + r")(?!\w)",
            re.I,
        )

    def mentions(self, text):
        return [(m, self.aliases[m[0].casefold()]) for m in self.pattern.finditer(text)]
