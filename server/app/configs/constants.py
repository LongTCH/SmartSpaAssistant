from enum import Enum


class WS_MESSAGES(str, Enum):
    CONNECTED = "CONNECTED"
    INBOX = "INBOX"
    UPDATE_SENTIMENT = "UPDATE_SENTIMENT"
    TEST_CHAT = "TEST_CHAT"


class CHAT_SIDES(str, Enum):
    CLIENT = "client"
    STAFF = "staff"


class PROVIDERS(str, Enum):
    MESSENGER = "messenger"


class SENTIMENTS(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class CHAT_ASSIGNMENT(str, Enum):
    AI = "ai"
    ME = "me"
