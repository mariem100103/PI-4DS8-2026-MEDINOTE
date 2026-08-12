/**
 * pages/ProfilePage.jsx
 * Page de profil utilisateur avec photo et informations complètes
 */

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContextHybrid.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import {
  User,
  Phone,
  MapPin,
  Calendar,
  Mail,
  Edit,
  Camera,
  Save,
  X,
  TrendingUp,
  FileText,
  Activity,
  Award,
} from "lucide-react";

const ProfilePage = () => {
  const { user, updateProfile } = useAuth();
  const { t } = useLanguage();
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (user) {
      setEditData({
        full_name: user.full_name || "",
        phone: user.phone || "",
        region: user.region || "",
        sector: user.sector || "",
        bio: user.bio || "",
        avatar_url: user.avatar_url || "",
      });
    }
  }, [user]);

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setEditData((current) => ({
        ...current,
        avatar_url: reader.result,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await updateProfile(editData);
      if (result.ok) {
        setSuccess("Profil mis à jour avec succès!");
        setIsEditing(false);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditData({
      full_name: user?.full_name || "",
      phone: user?.phone || "",
      region: user?.region || "",
      sector: user?.sector || "",
      bio: user?.bio || "",
      avatar_url: user?.avatar_url || "",
    });
    setIsEditing(false);
    setError(null);
    setSuccess(null);
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Mon Profil</h1>
        <p className="text-gray-600 mt-2">
          Gérez vos informations personnelles
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4">
          <p className="text-green-700">{success}</p>
        </div>
      )}

      {/* Carte principale */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header avec avatar */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8">
          <div className="flex items-center space-x-6">
            <div className="relative">
              <img
                src={
                  (isEditing ? editData.avatar_url : user.avatar_url) ||
                  `https://ui-avatars.com/api/?name=${encodeURIComponent(
                    user.full_name || user.email,
                  )}&background=0066CC&color=fff&size=120`
                }
                alt={user.full_name || user.email}
                className="w-24 h-24 rounded-full border-4 border-white shadow-lg"
              />
              {isEditing && (
                <label className="absolute bottom-0 right-0 bg-white rounded-full p-2 shadow-lg cursor-pointer hover:bg-gray-100">
                  <Camera className="w-4 h-4 text-gray-600" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                </label>
              )}
            </div>
            <div className="text-white">
              <h2 className="text-2xl font-bold">{user.full_name}</h2>
              <p className="text-blue-100">{user.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
                  {user.role === "admin" ? "Administrateur" : "Délégué Médical"}
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Actif
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Contenu */}
        <div className="p-6">
          {/* Actions */}
          <div className="flex justify-end mb-6">
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Edit className="w-4 h-4" />
                Modifier le profil
              </button>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={handleCancel}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  Annuler
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {loading ? "Enregistrement..." : "Enregistrer"}
                </button>
              </div>
            )}
          </div>

          {/* Informations personnelles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom complet
              </label>
              <input
                type="text"
                value={isEditing ? editData.full_name : user.full_name}
                onChange={(e) =>
                  setEditData({ ...editData, full_name: e.target.value })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-50 disabled:border-gray-200"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                value={user.email}
                disabled
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Téléphone
              </label>
              <input
                type="tel"
                value={isEditing ? editData.phone : user.phone || ""}
                onChange={(e) =>
                  setEditData({ ...editData, phone: e.target.value })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-50 disabled:border-gray-200"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rôle
              </label>
              <input
                type="text"
                value={
                  user.role === "admin" ? "Administrateur" : "Délégué Médical"
                }
                disabled
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Région
              </label>
              <select
                value={isEditing ? editData.region : user.region || ""}
                onChange={(e) =>
                  setEditData({ ...editData, region: e.target.value })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-50 disabled:border-gray-200"
              >
                <option value="">Sélectionner une région</option>
                <option value="Tunis">Tunis</option>
                <option value="Sfax">Sfax</option>
                <option value="Sousse">Sousse</option>
                <option value="Monastir">Monastir</option>
                <option value="Bizerte">Bizerte</option>
                <option value="Gabès">Gabès</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Secteur
              </label>
              <input
                type="text"
                value={isEditing ? editData.sector : user.sector || ""}
                onChange={(e) =>
                  setEditData({ ...editData, sector: e.target.value })
                }
                disabled={!isEditing}
                placeholder="Ex: Nord Tunis, Centre Sfax..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-50 disabled:border-gray-200"
              />
            </div>
          </div>

          {/* Biographie */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Biographie
            </label>
            <textarea
              value={isEditing ? editData.bio : user.bio || ""}
              onChange={(e) =>
                setEditData({ ...editData, bio: e.target.value })
              }
              disabled={!isEditing}
              rows={4}
              placeholder="Parlez-vous de votre expérience et de vos spécialités..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-50 disabled:border-gray-200 resize-none"
            />
          </div>
        </div>
      </div>

      {/* Statistiques d'activité */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Statistiques d'activité
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mx-auto mb-3">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {user.total_visits}
            </p>
            <p className="text-sm text-gray-600">Visites effectuées</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mx-auto mb-3">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {user.total_reports}
            </p>
            <p className="text-sm text-gray-600">Rapports créés</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mx-auto mb-3">
              <User className="w-6 h-6 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {user.total_doctors_followed}
            </p>
            <p className="text-sm text-gray-600">Médecins suivis</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mx-auto mb-3">
              <Award className="w-6 h-6 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {user.average_quality_score > 0
                ? user.average_quality_score.toFixed(1)
                : "N/A"}
            </p>
            <p className="text-sm text-gray-600">Score qualité moyen</p>
          </div>
        </div>
      </div>

      {/* Informations de connexion */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Informations de connexion
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Date d'inscription</p>
              <p className="font-medium text-gray-900">
                {new Date(user.created_at).toLocaleDateString("fr-FR", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Dernière connexion</p>
              <p className="font-medium text-gray-900">
                {user.last_login_at
                  ? new Date(user.last_login_at).toLocaleDateString("fr-FR", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Jamais"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
