import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";

const AuthContext = createContext(null);

// Stockage local pour l'ancien système
const STORAGE_AUTH = "medinote-auth";
const STORAGE_USERS = "medinote-users";

function safeParse(str, defaultValue = null) {
  try {
    return JSON.parse(str);
  } catch {
    return defaultValue;
  }
}

function normalizeUser(user) {
  return {
    ...user,
    full_name: user.full_name || user.name || user.email,
    email: String(user.email || "")
      .trim()
      .toLowerCase(),
    role: user.role === "admin" ? "admin" : "delegate",
    phone: user.phone || "",
    region: user.region || "",
    sector: user.sector || "",
    bio: user.bio || "",
    avatar_url: user.avatar_url || "",
    total_visits: Number(user.total_visits) || 0,
    total_reports: Number(user.total_reports) || 0,
    total_doctors_followed: Number(user.total_doctors_followed) || 0,
    average_quality_score: Number(user.average_quality_score) || 0,
    status: user.status || "active",
    created_at: user.created_at || new Date().toISOString(),
    last_login_at: user.last_login_at || new Date().toISOString(),
  };
}

function saveUsers(users) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
}

function loadUsers() {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_USERS);
  const parsed = safeParse(raw, null);
  const defaults = [
    {
      id: "admin",
      name: "Administrateur",
      email: "admin@vital-labo.tn",
      password: "demo123",
      role: "admin",
    },
    {
      id: "delegate",
      name: "Délégué Médical",
      email: "delegate@vital-labo.tn",
      password: "demo123",
      role: "delegate",
    },
  ];

  const list = Array.isArray(parsed) ? parsed : defaults;
  return list.map(normalizeUser);
}

function loadSession() {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_AUTH);
  const data = safeParse(raw, null);
  if (
    data &&
    data.token === "mock-token" &&
    data.user &&
    typeof data.user.email === "string"
  ) {
    return {
      token: data.token,
      user: normalizeUser({
        ...data.user,
        email: data.user.email,
      }),
    };
  }
  return null;
}

function saveSession(session) {
  if (!session) {
    localStorage.removeItem(STORAGE_AUTH);
    return;
  }
  localStorage.setItem(STORAGE_AUTH, JSON.stringify(session));
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadSession());
  const [loading, setLoading] = useState(false);

  const login = useCallback((email, password) => {
    const users = loadUsers();
    const found = users.find(
      (u) =>
        u.email.toLowerCase() === String(email).trim().toLowerCase() &&
        u.password === password,
    );
    if (!found) {
      return { ok: false, error: "invalid_credentials" };
    }
    if (found.status === "banned") {
      return { ok: false, error: "account_suspended" };
    }

    const now = new Date().toISOString();
    const updatedUsers = users.map((u) =>
      u.id === found.id ? { ...u, last_login_at: now } : u,
    );
    saveUsers(updatedUsers);

    const next = {
      token: "mock-token",
      user: {
        ...found,
        last_login_at: now,
      },
    };
    saveSession(next);
    setSession(next);
    return { ok: true, user: next.user };
  }, []);

  const register = useCallback((name, email, password, role) => {
    const users = loadUsers();
    const em = String(email).trim().toLowerCase();
    if (users.some((u) => u.email.toLowerCase() === em)) {
      return { ok: false, error: "email_exists" };
    }
    const newUser = {
      id: `u${Date.now()}`,
      full_name: String(name).trim(),
      email: em,
      password,
      role: role === "admin" ? "admin" : "delegate",
      status: "active",
      phone: "",
      region: "",
      sector: "",
      bio: "",
      avatar_url: "",
      total_visits: 0,
      total_reports: 0,
      total_doctors_followed: 0,
      average_quality_score: 0,
      created_at: new Date().toISOString(),
      last_login_at: new Date().toISOString(),
    };
    users.push(newUser);
    localStorage.setItem(STORAGE_USERS, JSON.stringify(users));

    const next = {
      token: "mock-token",
      user: {
        ...newUser,
      },
    };
    saveSession(next);
    setSession(next);
    return { ok: true, user: next.user };
  }, []);

  const updateProfile = useCallback(
    (profileData) => {
      const users = loadUsers();
      if (!session?.user?.email) {
        return { ok: false, error: "user_not_authenticated" };
      }

      const email = session.user.email.toLowerCase();
      const index = users.findIndex((u) => u.email.toLowerCase() === email);
      if (index === -1) {
        return { ok: false, error: "user_not_found" };
      }

      const existing = users[index];
      const updatedUser = {
        ...existing,
        ...profileData,
        full_name:
          profileData.full_name ||
          existing.full_name ||
          existing.name ||
          existing.email,
        email: existing.email,
        role: existing.role,
      };

      users[index] = updatedUser;
      localStorage.setItem(STORAGE_USERS, JSON.stringify(users));

      const next = {
        token: session.token,
        user: updatedUser,
      };
      saveSession(next);
      setSession(next);

      return { ok: true, user: updatedUser };
    },
    [session],
  );

  const getUsers = useCallback((options = {}) => {
    const {
      page = 1,
      per_page = 12,
      search = "",
      role = "",
      status = "",
      region = "",
    } = options;

    let items = loadUsers();

    const searchTerm = String(search).trim().toLowerCase();
    if (searchTerm) {
      items = items.filter((user) => {
        return [
          user.full_name,
          user.email,
          user.phone,
          user.region,
          user.sector,
        ]
          .join(" ")
          .toLowerCase()
          .includes(searchTerm);
      });
    }

    if (role) {
      items = items.filter((user) => user.role === role);
    }

    if (status) {
      items = items.filter((user) => user.status === status);
    }

    if (region) {
      items = items.filter(
        (user) =>
          user.region && user.region.toLowerCase() === region.toLowerCase(),
      );
    }

    const total = items.length;
    const start = (page - 1) * per_page;
    const usersPage = items.slice(start, start + per_page);

    return {
      users: usersPage,
      total,
      per_page,
      page,
    };
  }, []);

  const getUserById = useCallback((userId) => {
    const users = loadUsers();
    return users.find((user) => user.id === userId) || null;
  }, []);

  const updateUserById = useCallback(
    (userId, userData) => {
      const users = loadUsers();
      const index = users.findIndex((user) => user.id === userId);
      if (index === -1) {
        return { ok: false, error: "user_not_found" };
      }

      const existing = users[index];
      const updatedUser = {
        ...existing,
        ...userData,
        full_name:
          userData.full_name ||
          existing.full_name ||
          existing.name ||
          existing.email,
        email: existing.email,
        role: existing.role,
        status: userData.status || existing.status,
        password: existing.password,
      };

      users[index] = normalizeUser(updatedUser);
      saveUsers(users);

      if (session?.user?.id === userId) {
        const next = { token: session.token, user: users[index] };
        saveSession(next);
        setSession(next);
      }

      return { ok: true, user: users[index] };
    },
    [session],
  );

  const banUser = useCallback(
    (userId) => updateUserById(userId, { status: "banned" }),
    [updateUserById],
  );

  const unbanUser = useCallback(
    (userId) => updateUserById(userId, { status: "active" }),
    [updateUserById],
  );

  const deleteUserById = useCallback(
    (userId) => {
      const users = loadUsers();
      const remaining = users.filter((user) => user.id !== userId);
      if (remaining.length === users.length) {
        return { ok: false, error: "user_not_found" };
      }
      saveUsers(remaining);

      if (session?.user?.id === userId) {
        saveSession(null);
        setSession(null);
      }

      return { ok: true };
    },
    [session],
  );

  const getUserStats = useCallback(() => {
    const users = loadUsers();
    return {
      total_users: users.length,
      admins: users.filter((user) => user.role === "admin").length,
      delegates: users.filter((user) => user.role === "delegate").length,
      banned_users: users.filter((user) => user.status === "banned").length,
    };
  }, []);

  const logout = useCallback(() => {
    saveSession(null);
    setSession(null);
  }, []);

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      token: session?.token ?? null,
      isAuthenticated: Boolean(session?.token),
      isAdmin: session?.user?.role === "admin",
      loading,
      error: null,
      login,
      register,
      logout,
      updateProfile,
      listUsers: () => loadUsers().map(({ password: _p, ...rest }) => rest),
      getUsers,
      getUserById,
      updateUserById,
      banUser,
      unbanUser,
      deleteUserById,
      getUserStats,
    }),
    [
      session,
      login,
      register,
      logout,
      updateProfile,
      loading,
      getUsers,
      getUserById,
      updateUserById,
      banUser,
      unbanUser,
      deleteUserById,
      getUserStats,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
