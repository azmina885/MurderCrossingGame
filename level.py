from entities import Character, Evidence


# ── Colour palette ─────────────────────────────────────────────────────────
C_DETECTIVE = (40,  70,  130)
C_BUTLER    = (80,  50,  100)
C_MAID      = (130, 55,  80)
C_DOCTOR    = (40,  100, 90)
C_NEPHEW    = (140, 80,  30)
C_KNIFE     = (110, 30,  30)
C_LETTER    = (60,  90,  40)
C_KEY       = (100, 85,  20)


def create_level(number, sw, sh):
    """Factory — returns the correct Level instance."""
    levels = {1: Level1, 2: Level2, 3: Level3}
    return levels[number](sw, sh)


class Level:
    """Base level class."""

    def __init__(self, sw, sh):
        self.sw = sw
        self.sh = sh
        self.level_number = 0
        self.title        = ""
        self.subtitle     = ""
        self.time_limit   = 60
        self.base_score   = 100

        self.characters = []
        self.evidence   = []
        self.rules      = []

        self.opening_lines = []
        self.ending_lines  = []
        self.lose_reasons  = {}

        self.setup()

    @property
    def all_entities(self):
        return self.characters + self.evidence

    def setup(self):
        pass

    # ── Position helpers ───────────────────────────────────────────────────

    def _left_positions(self, count):
        start = 110
        gap   = min(95, (self.sh - start - 60) // max(count, 1))
        return [(55, start + i * gap) for i in range(count)]

    # ── Rule checking ──────────────────────────────────────────────────────

    def check_rules(self, bank_entities, detective_present):
        """
        Returns (violated: bool, message: str).
        Only checks if detective is NOT present on this bank.
        Forbidden pair triggers whenever BOTH are on the same bank
        without Detective — regardless of who else is there.
        """
        if detective_present:
            return False, ""
        names = {e.name for e in bank_entities}
        for (a, b, reason) in self.rules:
            if a in names and b in names:
                return True, reason
        return False, ""

    def check_win(self):
        return all(e.side == "right" for e in self.all_entities)

    def validate_banks(self, boat_side):
        """
        Only checks the LEFT bank (Blackwood Mansion).
        Right bank = Police HQ — suspects are under custody there,
        so no rules apply once they cross the river.
        """
        left_entities = [e for e in self.all_entities if e.side == "left"]
        detective_left = any(e.name == "Detective James" for e in left_entities)
        return self.check_rules(left_entities, detective_left)


# ── LEVEL 1 ────────────────────────────────────────────────────────────────

class Level1(Level):
    """The First Clue — Easy (3 chars + 1 evidence)."""

    def setup(self):
        self.level_number = 1
        self.title        = "Level 1 — The First Clue"
        self.subtitle     = "Easy"
        self.time_limit   = 60
        self.base_score   = 100

        self.opening_lines = [
            "BLACKWOOD MANSION — 10:43 PM",
            "",
            "A scream echoes through the mansion.",
            "Mr. Blackwood is found dead in his study.",
            "The bridge to town has collapsed.",
            "",
            "Detective James must transport",
            "all suspects and evidence across the river.",
            "",
            "Be careful... someone is hiding the truth.",
        ]

        self.ending_lines = [
            "The knife is secured.",
            "",
            "The butler appears nervous.",
            "",
            "A new witness comes forward...",
        ]

        pos = self._left_positions(4)

        detective = Character("Detective James", "DET", C_DETECTIVE, *pos[0])
        detective.set_description("Detective James — Investigator\nMust be on the boat to sail.")

        butler = Character("Butler",  "BUT", C_BUTLER,  *pos[1])
        butler.set_description("Butler — Suspect\nHis fingerprints were found on the knife.")

        maid = Character("Maid", "MAID", C_MAID, *pos[2])
        maid.set_description("Maid — Suspect\nFound near the study door at midnight.")

        knife = Evidence("Knife", "KNF", C_KNIFE, *pos[3])
        knife.set_description("Knife — Evidence\nBelieved to be the murder weapon.")

        self.characters = [detective, butler, maid]
        self.evidence   = [knife]

        self.rules = [
            ("Butler", "Knife",
             "Butler threw the Knife into the river!"),
        ]


# ── LEVEL 2 ────────────────────────────────────────────────────────────────

class Level2(Level):
    """Hidden Secrets — Medium (4 chars + 2 evidence)."""

    def setup(self):
        self.level_number = 2
        self.title        = "Level 2 — Hidden Secrets"
        self.subtitle     = "Medium"
        self.time_limit   = 90
        self.base_score   = 200

        self.opening_lines = [
            "A secret letter has been discovered",
            "inside Mr. Blackwood's desk.",
            "",
            "The maid knows its contents.",
            "If left alone with it, she may destroy it.",
            "",
            "A doctor arrives as a new suspect.",
            "",
            "Transport everyone safely — time is short!",
        ]

        self.ending_lines = [
            "The letter reveals a dispute",
            "over inheritance.",
            "",
            "Mr. Blackwood planned to remove",
            "someone from his will.",
            "",
            "The suspect list grows...",
        ]

        pos = self._left_positions(6)

        detective = Character("Detective James", "DET", C_DETECTIVE, *pos[0])
        detective.set_description("Detective James — Investigator\nMust be on the boat to sail.")

        butler = Character("Butler",  "BUT", C_BUTLER,  *pos[1])
        butler.set_description("Butler — Suspect\nFingerprints found on the knife.")

        maid = Character("Maid", "MAID", C_MAID, *pos[2])
        maid.set_description("Maid — Suspect\nKnows what is in the secret letter.")

        doctor = Character("Doctor", "DOC", C_DOCTOR, *pos[3])
        doctor.set_description("Doctor — Suspect\nArrived at the mansion late at night.")

        knife  = Evidence("Knife",         "KNF", C_KNIFE,  *pos[4])
        letter = Evidence("Secret Letter", "LTR", C_LETTER, *pos[5])

        knife.set_description("Knife — Evidence\nThe murder weapon.")
        letter.set_description("Secret Letter — Evidence\nReveals a change in the will.")

        self.characters = [detective, butler, maid, doctor]
        self.evidence   = [knife, letter]

        self.rules = [
            ("Butler", "Knife",
             "Butler threw the Knife into the river!"),
            ("Maid",   "Secret Letter",
             "Maid destroyed the Secret Letter!"),
        ]


# ── LEVEL 3 ────────────────────────────────────────────────────────────────

class Level3(Level):
    """The Truth Emerges — Hard (5 chars + 3 evidence)."""

    def setup(self):
        self.level_number = 3
        self.title        = "Level 3 — The Truth Emerges"
        self.subtitle     = "Hard"
        self.time_limit   = 120
        self.base_score   = 300

        self.opening_lines = [
            "The safe key unlocks Blackwood's vault.",
            "",
            "The Nephew desperately wants access.",
            "The Maid still threatens to destroy",
            "the Secret Letter.",
            "",
            "Three rules now stand between",
            "justice and a killer's escape.",
            "",
            "This is your final chance.",
            "Transport everyone — or fail.",
        ]

        self.ending_lines = [
            "POLICE HEADQUARTERS",
            "",
            "All suspects have been questioned.",
            "All evidence has been preserved.",
            "",
            "The Secret Letter reveals",
            "Mr. Blackwood changed his will.",
            "",
            "Fingerprints on the Knife match...",
            "",
            "DR. WILLIAM CARTER",
            "",
            "The Doctor murdered Mr. Blackwood",
            "to hide years of medical fraud.",
            "",
            "CASE CLOSED.",
        ]

        pos = self._left_positions(8)

        detective = Character("Detective James", "DET", C_DETECTIVE, *pos[0])
        detective.set_description("Detective James — Investigator\nMust be on the boat to sail.")

        butler = Character("Butler",  "BUT", C_BUTLER,  *pos[1])
        butler.set_description("Butler — Suspect\nFingerprints on the knife.")

        maid = Character("Maid", "MAID", C_MAID, *pos[2])
        maid.set_description("Maid — Suspect\nKnows the letter's contents.")

        doctor = Character("Doctor",  "DOC", C_DOCTOR,  *pos[3])
        doctor.set_description("Doctor — Suspect\nArrived late. The real killer.")

        nephew = Character("Nephew",  "NEP", C_NEPHEW,  *pos[4])
        nephew.set_description("Nephew — Suspect\nDesperate to access the vault.")

        knife  = Evidence("Knife",         "KNF", C_KNIFE,  *pos[5])
        letter = Evidence("Secret Letter", "LTR", C_LETTER, *pos[6])
        key    = Evidence("Safe Key",      "KEY", C_KEY,    *pos[7])

        knife.set_description("Knife — Evidence\nThe murder weapon.")
        letter.set_description("Secret Letter — Evidence\nReveals change in will.")
        key.set_description("Safe Key — Evidence\nUnlocks Blackwood's private vault.")

        self.characters = [detective, butler, maid, doctor, nephew]
        self.evidence   = [knife, letter, key]

        self.rules = [
            ("Butler", "Knife",
             "Butler threw the Knife into the river!"),
            ("Maid",   "Secret Letter",
             "Maid destroyed the Secret Letter!"),
            ("Nephew", "Safe Key",
             "Nephew stole the Safe Key and escaped!"),
        ]