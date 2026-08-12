/**
 * pages/AdminDashboardPage.jsx
 * Tableau de bord admin enrichi avec gestion des utilisateurs
 */

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextHybrid.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import {
  Users,
  UserCheck,
  UserX,
  AlertTriangle,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Ban,
  Eye,
  Phone,
  MapPin,
  Calendar,
  TrendingUp,
  FileText,
  Activity,
} from "lucide-react";

const AdminDashboardPage = () => {
  const { t } = useLanguage();
  const {
    getUsers,
    getUserStats,
    banUser,
    unbanUser,
    deleteUserById,
    updateUserById,
  } = useAuth();
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("");
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Charger les données
  useEffect(() => {
    loadData();
  }, [currentPage, searchTerm, selectedRole, selectedStatus, selectedRegion]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const statsData = getUserStats();
      const usersData = getUsers({
        page: currentPage,
        search: searchTerm,
        role: selectedRole,
        status: selectedStatus,
        region: selectedRegion,
      });

      setStats(statsData);
      setUsers(usersData.users);
      setTotalPages(
        Math.max(1, Math.ceil(usersData.total / usersData.per_page)),
      );
    } catch (err) {
      setError(err.message || "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  const handleBanUser = async (userId) => {
    try {
      const result = banUser(userId);
      if (!result.ok) {
        throw new Error(result.error || "Impossible de bannir l'utilisateur");
      }
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUnbanUser = async (userId) => {
    try {
      const result = unbanUser(userId);
      if (!result.ok) {
        throw new Error(result.error || "Impossible de débannir l'utilisateur");
      }
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (
      !window.confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")
    ) {
      return;
    }

    try {
      const result = deleteUserById(userId);
      if (!result.ok) {
        throw new Error(
          result.error || "Impossible de supprimer l'utilisateur",
        );
      }
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: {
        color: "bg-green-100 text-green-800",
        icon: UserCheck,
        text: "Actif",
      },
      banned: { color: "bg-red-100 text-red-800", icon: UserX, text: "Banni" },
      inactive: {
        color: "bg-gray-100 text-gray-800",
        icon: AlertTriangle,
        text: "Inactif",
      },
    };

    const config = statusConfig[status] || statusConfig.inactive;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
      >
        <Icon className="w-3 h-3" />
        {config.text}
      </span>
    );
  };

  const getRoleBadge = (role) => {
    const roleConfig = {
      admin: { color: "bg-purple-100 text-purple-800", text: "Admin" },
      delegate: { color: "bg-blue-100 text-blue-800", text: "Délégué" },
    };

    const config = roleConfig[role] || roleConfig.delegate;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
      >
        {config.text}
      </span>
    );
  };

  if (loading && !users.length) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Tableau de Bord Admin
        </h1>
        <p className="text-gray-600 mt-2">
          Gestion des utilisateurs et statistiques
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Utilisateurs
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total_users}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Utilisateurs Actifs
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.active_users}
                </p>
              </div>
              <UserCheck className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Utilisateurs Bannis
                </p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.banned_users}
                </p>
              </div>
              <UserX className="w-8 h-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Délégués</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.delegate_users}
                </p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>
      )}

      {/* Filtres et recherche */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Recherche */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Rechercher par nom, email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Filtres */}
          <div className="flex gap-2">
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Tous les rôles</option>
              <option value="admin">Admin</option>
              <option value="delegate">Délégué</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Tous les statuts</option>
              <option value="active">Actif</option>
              <option value="banned">Banni</option>
              <option value="inactive">Inactif</option>
            </select>

            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Toutes les régions</option>
              <option value="Tunis">Tunis</option>
              <option value="Sfax">Sfax</option>
              <option value="Sousse">Sousse</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tableau des utilisateurs */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Liste des Utilisateurs
          </h2>
        </div>

        {error && (
          <div className="px-6 py-4 bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Utilisateur
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rôle/Statut
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Activité
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dernière connexion
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0">
                        <img
                          className="h-10 w-10 rounded-full"
                          src={
                            user.avatar_url ||
                            `https://ui-avatars.com/api/?name=${user.full_name}&background=0066CC&color=fff`
                          }
                          alt={user.full_name}
                        />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {user.full_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {user.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 space-y-1">
                      {user.phone && (
                        <div className="flex items-center gap-1">
                          <Phone className="w-4 h-4 text-gray-400" />
                          {user.phone}
                        </div>
                      )}
                      {user.region && (
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4 text-gray-400" />
                          {user.region} {user.sector && `- ${user.sector}`}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-1">
                      {getRoleBadge(user.role)}
                      {getStatusBadge(user.status)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4 text-gray-400" />
                        {user.total_reports} rapports
                      </div>
                      <div className="flex items-center gap-1">
                        <Activity className="w-4 h-4 text-gray-400" />
                        {user.total_visits} visites
                      </div>
                      {user.average_quality_score > 0 && (
                        <div className="flex items-center gap-1">
                          <TrendingUp className="w-4 h-4 text-gray-400" />
                          Score: {user.average_quality_score.toFixed(1)}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.last_login_at ? (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        {new Date(user.last_login_at).toLocaleDateString(
                          "fr-FR",
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">Jamais</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          setSelectedUser(user);
                          setShowUserModal(true);
                        }}
                        className="text-blue-600 hover:text-blue-900"
                        title="Voir les détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>

                      {user.status === "active" ? (
                        <button
                          onClick={() => handleBanUser(user.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Bannir"
                        >
                          <Ban className="w-4 h-4" />
                        </button>
                      ) : user.status === "banned" ? (
                        <button
                          onClick={() => handleUnbanUser(user.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Débannir"
                        >
                          <UserCheck className="w-4 h-4" />
                        </button>
                      ) : null}

                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Page {currentPage} sur {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50"
                >
                  Précédent
                </button>
                <button
                  onClick={() =>
                    setCurrentPage(Math.min(totalPages, currentPage + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50"
                >
                  Suivant
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal détails utilisateur */}
      {showUserModal && selectedUser && (
        <UserDetailModal
          user={selectedUser}
          onClose={() => {
            setShowUserModal(false);
            setSelectedUser(null);
          }}
          onUpdate={loadData}
          onSave={updateUserById}
        />
      )}
    </div>
  );
};

// Modal pour les détails utilisateur
const UserDetailModal = ({ user, onClose, onUpdate, onSave }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({ ...user });
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    setLoading(true);
    try {
      const result = onSave(user.id, editData);
      if (!result.ok) {
        throw new Error(
          result.error || "Impossible de mettre à jour l'utilisateur",
        );
      }
      onUpdate();
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Détails Utilisateur
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Photo et infos principales */}
            <div className="flex items-center space-x-4">
              <img
                src={
                  user.avatar_url ||
                  `https://ui-avatars.com/api/?name=${user.full_name}&background=0066CC&color=fff&size=100`
                }
                alt={user.full_name}
                className="w-20 h-20 rounded-full"
              />
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {user.full_name}
                </h3>
                <p className="text-gray-500">{user.email}</p>
                <div className="flex gap-2 mt-2">
                  {getRoleBadge(user.role)}
                  {getStatusBadge(user.status)}
                </div>
              </div>
            </div>

            {/* Formulaire d'édition */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom complet
                </label>
                <input
                  type="text"
                  value={isEditing ? editData.full_name : user.full_name}
                  onChange={(e) =>
                    setEditData({ ...editData, full_name: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Téléphone
                </label>
                <input
                  type="tel"
                  value={isEditing ? editData.phone || "" : user.phone || ""}
                  onChange={(e) =>
                    setEditData({ ...editData, phone: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Région
                </label>
                <select
                  value={isEditing ? editData.region || "" : user.region || ""}
                  onChange={(e) =>
                    setEditData({ ...editData, region: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-50"
                >
                  <option value="">Sélectionner une région</option>
                  <option value="Tunis">Tunis</option>
                  <option value="Sfax">Sfax</option>
                  <option value="Sousse">Sousse</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Secteur
                </label>
                <input
                  type="text"
                  value={isEditing ? editData.sector || "" : user.sector || ""}
                  onChange={(e) =>
                    setEditData({ ...editData, sector: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-50"
                />
              </div>
            </div>

            {/* Bio */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Biographie
              </label>
              <textarea
                value={isEditing ? editData.bio || "" : user.bio || ""}
                onChange={(e) =>
                  setEditData({ ...editData, bio: e.target.value })
                }
                disabled={!isEditing}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md disabled:bg-gray-50"
              />
            </div>

            {/* Stats */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">
                Statistiques d'activité
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Visites</p>
                  <p className="font-medium">{user.total_visits}</p>
                </div>
                <div>
                  <p className="text-gray-500">Rapports</p>
                  <p className="font-medium">{user.total_reports}</p>
                </div>
                <div>
                  <p className="text-gray-500">Médecins suivis</p>
                  <p className="font-medium">{user.total_doctors_followed}</p>
                </div>
                <div>
                  <p className="text-gray-500">Score qualité</p>
                  <p className="font-medium">
                    {user.average_quality_score.toFixed(1)}
                  </p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              {!isEditing ? (
                <>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Modifier
                  </button>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Fermer
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setIsEditing(false)}
                    disabled={loading}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "Enregistrement..." : "Enregistrer"}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper functions (réutilisées du composant principal)
const getRoleBadge = (role) => {
  const roleConfig = {
    admin: { color: "bg-purple-100 text-purple-800", text: "Admin" },
    delegate: { color: "bg-blue-100 text-blue-800", text: "Délégué" },
  };

  const config = roleConfig[role] || roleConfig.delegate;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.text}
    </span>
  );
};

const getStatusBadge = (status) => {
  const statusConfig = {
    active: {
      color: "bg-green-100 text-green-800",
      icon: UserCheck,
      text: "Actif",
    },
    banned: { color: "bg-red-100 text-red-800", icon: UserX, text: "Banni" },
    inactive: {
      color: "bg-gray-100 text-gray-800",
      icon: AlertTriangle,
      text: "Inactif",
    },
  };

  const config = statusConfig[status] || statusConfig.inactive;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
    >
      <Icon className="w-3 h-3" />
      {config.text}
    </span>
  );
};

export default AdminDashboardPage;
