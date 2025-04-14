from enum import Enum, auto


class WS_MESSAGES(str, Enum):
    CONNECTED = "CONNECTED"
    INBOX = "INBOX"


class CHAT_SIDES(str, Enum):
    CLIENT = "client"
    STAFF = "staff"


class PROVIDERS(str, Enum):
    MESSENGER = "messenger"
