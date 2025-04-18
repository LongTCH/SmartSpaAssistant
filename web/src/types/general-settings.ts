export type SettingsState = {
  autoResponseTime: number;
  messageCount: number;
  pronouns: {
    self: string;
    other: string;
  };
  reactionMessage: string;
  undefinedQuestions: {
    action: "reply" | "notify";
    responseMessage: string;
  };
};
