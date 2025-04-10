export const API_ROUTES = {
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    LOGOUT: "/auth/logout",
    GOOGLE: "/auth/oauth/google",
    CALLBACK: "/auth/callback",
    EXCHANGE_STATE: "/auth/exchange-state",
  },
  SPACE: {
    ALL: "/spaces",
    CREATE: "/spaces/create",
    DETAIL: "/space",
    PUBLIC: "/spaces/public",
    MINE: "/spaces/me",
  },
  DOCUMENT: {
    UPLOAD: "/documents/upload",
    DETAIL: (id: string) => `/documents/${id}`,
  },
  CONVERSATION: {
    GET: "/conversations",
    DETAIL: (id: string) => `/conversations/${id}`,
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
