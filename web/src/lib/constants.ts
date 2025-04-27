export const API_ROUTES = {
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    LOGOUT: "/auth/logout",
    GOOGLE: "/auth/oauth/google",
    CALLBACK: "/auth/callback",
    EXCHANGE_STATE: "/auth/exchange-state",
  },
  SCRIPT: {
    GET: "/scripts",
    DETAIL: (id: string) => `/scripts/${id}`,
    UPDATE: (id: string) => `/scripts/${id}`,
    DELETE: (id: string) => `/scripts/${id}`,
    DELETE_MULTIPLE: "/scripts/delete-multiple",
    CREATE: "/scripts",
    DOWNLOAD: "/scripts/download",
    UPLOAD: "/scripts/upload",
    GET_ALL_PUBLISHED: "/scripts/all-published",
  },
  INTEREST: {
    GET: "/interests",
    DETAIL: (id: string) => `/interests/${id}`,
    UPDATE: (id: string) => `/interests/${id}`,
    DELETE: (id: string) => `/interests/${id}`,
    DELETE_MULTIPLE: "/interests/delete-multiple",
    CREATE: "/interests",
    DOWNLOAD: "/interests/download",
    UPLOAD: "/interests/upload",
    GET_ALL_PUBLISHED: "/interests/all-published",
  },
  SHEET: {
    GET: "/sheets",
    DETAIL: (id: string) => `/sheets/${id}`,
    UPDATE: (id: string) => `/sheets/${id}`,
    DELETE: (id: string) => `/sheets/${id}`,
    DELETE_MULTIPLE: "/sheets/delete-multiple",
    CREATE: "/sheets",
    GET_ROWS: (sheetId: string) => `/sheets/${sheetId}/rows`,
    DOWNLOAD: (sheetId: string) => `/sheets/${sheetId}/download`,
  },
  GUEST: {
    FILTER: "/guests/filter",
    DETAIL: (id: string) => `/guests/${id}`,
    DELETE: (id: string) => `/guests/${id}`,
    UPDATE: (id: string) => `/guests/${id}`,
    DELETE_MULTIPLE: "/guests/delete-multiple",
  },
  CONVERSATION: {
    GET: "/conversations",
    DETAIL: (id: string) => `/conversations/${id}`,
    GET_SENTIMENT: "/conversations/sentiments",
    UPDATE_ASSIGNMENT: (id: string) => `/conversations/${id}/assignment`,
  },
  SETTING: {
    GET: "/settings",
    UPDATE: "/settings",
  },
};

export const APP_ROUTES = {
  HOME: "/",
  LOGIN: "/auth/login",
  REGISTER: "/auth/register",
  DASHBOARD: "/dashboard",
  PROFILE: "/profile",
  AUTH_CALLBACK: "/auth/callback",
  CONVERSATIONS: "/conversations",
  SETTINGS: "/settings",
  ANALYSIS: "/analysis",
  CUSTOMERS: "/customers",
};

export const WS_MESSAGES = {
  CONNECTED: "CONNECTED",
  INBOX: "INBOX",
  UPDATE_SENTIMENT: "UPDATE_SENTIMENT",
};
