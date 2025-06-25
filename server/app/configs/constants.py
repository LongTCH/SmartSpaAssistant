from enum import Enum


class WS_MESSAGES(str, Enum):
    CONNECTED = "CONNECTED"
    INBOX = "INBOX"
    TEST_CHAT = "TEST_CHAT"
    ALERT = "ALERT"
    SEND_ACTION = "SEND_ACTION"


class CHAT_SIDES(str, Enum):
    CLIENT = "client"
    STAFF = "staff"


class PROVIDERS(str, Enum):
    MESSENGER = "messenger"
    WEB = "web"


class CHAT_ASSIGNMENT(str, Enum):
    AI = "ai"
    ME = "me"


class PARAM_VALIDATION(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"


DEFAULT_SETTING_ID = "fe25ab8b-59ea-4e5b-b9b8-6f3a4dfea98a"
