/**
 * api/authApi.js
 * API client pour l'authentification et la gestion des utilisateurs
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Stockage local des tokens
const TOKEN_KEY = "medilab_access_token";
const REFRESH_TOKEN_KEY = "medilab_refresh_token";

/**
 * Gestion des tokens
 */
export const tokenManager = {
  getAccessToken: () => localStorage.getItem(TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },
  clearTokens: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

/**
 * Helper pour les requêtes authentifiées
 */
const authFetch = async (url, options = {}) => {
  const token = tokenManager.getAccessToken();

  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  const response = await fetch(`${API_BASE}${url}`, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  });

  // Gérer le refresh token si 401
  if (response.status === 401 && !url.includes("/refresh")) {
    try {
      await refreshAccessToken();
      // Réessayer la requête avec le nouveau token
      const newToken = tokenManager.getAccessToken();
      return fetch(`${API_BASE}${url}`, {
        ...defaultOptions,
        ...options,
        headers: {
          ...defaultOptions.headers,
          ...options.headers,
          Authorization: `Bearer ${newToken}`,
        },
      });
    } catch (error) {
      // Refresh failed, déconnecter l'utilisateur
      tokenManager.clearTokens();
      window.location.href = "/login";
      throw new Error("Session expired");
    }
  }

  return response;
};

/**
 * Rafraîchir le token d'accès
 */
export const refreshAccessToken = async () => {
  const refreshToken = tokenManager.getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  const response = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${refreshToken}`,
    },
  });

  if (!response.ok) {
    throw new Error("Token refresh failed");
  }

  const data = await response.json();
  tokenManager.setTokens(data.access_token, refreshToken);

  return data;
};

/**
 * Authentification
 */
export const authApi = {
  /**
   * Connexion
   */
  login: async (email, password) => {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data = await response.json();
    tokenManager.setTokens(data.access_token, data.refresh_token);

    return data;
  },

  /**
   * Inscription
   */
  register: async (userData) => {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Registration failed");
    }

    return response.json();
  },

  /**
   * Déconnexion
   */
  logout: () => {
    tokenManager.clearTokens();
  },

  /**
   * Obtenir les infos de l'utilisateur courant
   */
  getCurrentUser: async () => {
    const response = await authFetch("/api/auth/me");

    if (!response.ok) {
      throw new Error("Failed to get user info");
    }

    return response.json();
  },

  /**
   * Mettre à jour le profil utilisateur
   */
  updateProfile: async (userData) => {
    const response = await authFetch("/api/auth/me", {
      method: "PUT",
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Profile update failed");
    }

    return response.json();
  },

  /**
   * Obtenir le token d'authentification
   */
  getAuthToken: () => {
    return tokenManager.getAccessToken();
  },

  /**
   * Vérifier si l'utilisateur est authentifié
   */
  isAuthenticated: () => {
    return !!tokenManager.getAccessToken();
  },
};

/**
 * API Admin pour la gestion des utilisateurs
 */
export const adminApi = {
  /**
   * Créer un utilisateur
   */
  createUser: async (userData) => {
    const response = await authFetch("/api/auth/users", {
      method: "POST",
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "User creation failed");
    }

    return response.json();
  },

  /**
   * Lister les utilisateurs
   */
  getUsers: async (filters = {}) => {
    const params = new URLSearchParams();

    if (filters.page) params.append("page", filters.page);
    if (filters.perPage) params.append("per_page", filters.perPage);
    if (filters.search) params.append("search", filters.search);
    if (filters.role) params.append("role", filters.role);
    if (filters.status) params.append("status", filters.status);
    if (filters.region) params.append("region", filters.region);

    const response = await authFetch(`/api/auth/users?${params}`);

    if (!response.ok) {
      throw new Error("Failed to fetch users");
    }

    return response.json();
  },

  /**
   * Obtenir les détails d'un utilisateur
   */
  getUser: async (userId) => {
    const response = await authFetch(`/api/auth/users/${userId}`);

    if (!response.ok) {
      throw new Error("Failed to fetch user");
    }

    return response.json();
  },

  /**
   * Mettre à jour un utilisateur
   */
  updateUser: async (userId, userData) => {
    const response = await authFetch(`/api/auth/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "User update failed");
    }

    return response.json();
  },

  /**
   * Supprimer un utilisateur
   */
  deleteUser: async (userId) => {
    const response = await authFetch(`/api/auth/users/${userId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "User deletion failed");
    }

    return response.json();
  },

  /**
   * Bannir un utilisateur
   */
  banUser: async (userId) => {
    const response = await authFetch(`/api/auth/users/${userId}/ban`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to ban user");
    }

    return response.json();
  },

  /**
   * Débannir un utilisateur
   */
  unbanUser: async (userId) => {
    const response = await authFetch(`/api/auth/users/${userId}/unban`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to unban user");
    }

    return response.json();
  },

  /**
   * Obtenir les statistiques des utilisateurs
   */
  getUserStats: async () => {
    const response = await authFetch("/api/auth/stats");

    if (!response.ok) {
      throw new Error("Failed to fetch user stats");
    }

    return response.json();
  },
};

/**
 * Vérifier si l'utilisateur est authentifié
 */
export const isAuthenticated = () => {
  return !!tokenManager.getAccessToken();
};

/**
 * Obtenir le token d'accès pour les requêtes
 */
export const getAuthToken = () => {
  return tokenManager.getAccessToken();
};
