export type SettingsState = {
  CHAT_WAIT_SECONDS: number;
  SENTIMENT_INTERVAL_CHAT_COUNT: number;
  FORM_OF_ADDRESS: {
    ME: string;
    OTHER: string;
  };
  REACTION_MESSAGE: string;
  UNDEFINED_MESSAGE_HANDLER: {
    TYPE: "response" | "notify";
    MESSAGE: string;
  };
};
