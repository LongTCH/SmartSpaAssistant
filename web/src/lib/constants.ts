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
  DOCUMENT: {
    UPLOAD: "/documents/upload",
    DETAIL: (id: string) => `/documents/${id}`,
  },
  CONVERSATION: {
    GET: "/conversations",
    DETAIL: (id: string) => `/conversations/${id}`,
    GET_SENTIMENT: "/conversations/sentiments",
    UPDATE_ASSIGNMENT: (id: string) => `/conversations/${id}/assignment/`,
  },
};

export const APP_ROUTES = {
  HOME: "/",
  LOGIN: "/auth/login",
  REGISTER: "/auth/register",
  DASHBOARD: "/dashboard",
  PROFILE: "/profile",
  AUTH_CALLBACK: "/auth/callback",
  SPACES: {
    PUBLIC: "/spaces/public",
    MINE: "/spaces/me",
  },
  DOCUMENT: {
    UPLOAD_PROGRESS: (id: string) => `/documents/upload-progress/${id}`,
  },
};

export const WS_MESSAGES = {
  CONNECTED: "CONNECTED",
  INBOX: "INBOX",
  UPDATE_SENTIMENT: "UPDATE_SENTIMENT",
};
