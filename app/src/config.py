import os

REDIS_URL = os.getenv("REDIS_URL")

EVENT_BROKER_HOST = os.getenv("EVENT_BROKER_HOST")
EVENT_BROKER_PORT = int(os.getenv("EVENT_BROKER_PORT", 0))

API_TARGETS_DIR = "/targets"
FUNCTIONS = {
    "windows": [
        "amcache",
        "services",
        "bam",
        "ual",
        "browser.history",
        "browser.downloads",
        "browser.extensions",
        "anydesk",
        "powershell_history",
        "ssh",
        "webserver",
        "adpolicy",
        "defender.quarantine",
        "defender.mplog",
        "defender.exclusions",
        "sam",
        "jumplist",
        "lnk",
        "prefetch",
        "recyclebin",
        "mru",
        "runkeys",
        "shellbags",
        "shimcache",
        "userassist",
        "sru",
        "tasks",
        "evtx",
        "regf",
        "usnjrnl",
    ],
    "linux": [

    ]
}
