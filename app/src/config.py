import os

REDIS_URL = os.getenv("REDIS_URL")
TASKIQ_BACKEND_POSTGRES_URL = os.getenv("BACKEND_POSTGRES_URL")
API_DB_POSTGRES_URL = os.getenv("API_DB_POSTGRES_URL")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 0))
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
        "defender",
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
        "evt",
        "regf",
        "mft",
        "usnjrnl",
    ],
    "linux": []
}