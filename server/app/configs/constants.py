from enum import Enum


class WS_MESSAGES(str, Enum):
    CONNECTED = "CONNECTED"
    INBOX = "INBOX"
    TEST_CHAT = "TEST_CHAT"


class CHAT_SIDES(str, Enum):
    CLIENT = "client"
    STAFF = "staff"


class PROVIDERS(str, Enum):
    MESSENGER = "messenger"


class CHAT_ASSIGNMENT(str, Enum):
    AI = "ai"
    ME = "me"
