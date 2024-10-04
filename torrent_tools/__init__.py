from appdirs import user_config_dir
from yarl import URL

BTN_ENDPOINT = URL("https://api.broadcasthe.net/")
MAM_ENDPOINT = URL("https://www.myanonamouse.net/")
ORPHEUS_ENDPOINT = URL("https://orpheus.network/")
REDACTED_ENDPOINT = URL("https://redacted.ch/")
USER_AGENT = "torrenttools/0.0.1"

DELUGE_PORT = 58846
DELUGE_USERNAME = "deluge"
FILTER = r".*"

CONFIG = user_config_dir("torrenttools")

RELEASE_TYPE_NAMES = {
    "flacsfor.me": {
        0: "Software",
        1: "Album",
        3: "Soundtrack",
        5: "EP",
        6: "Anthology",
        7: "Compilation",
        9: "Single",
        11: "Live Album",
        13: "Remix",
        14: "Bootleg",
        15: "Interview",
        16: "Mixtape",
        17: "Demo",
        18: "Concert Recording",
        19: "DJ Mix",
    },
    "opsfet.ch": {
        1: "Album",
        3: "Soundtrack",
        5: "EP",
        6: "Anthology",
        7: "Compilation",
        9: "Single",
        11: "Live Album",
        13: "Remix",
        14: "Bootleg",
        16: "Mixtape",
        17: "DJ Mix",
        18: "Concert Recording",
    },
    "myanonamouse.net": {},
}
