/**
 * Profile Page
 */
import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { RootState, logout } from "../store";
import { useNavigate } from "react-router-dom";

const ProfilePage: React.FC = () => {
  const user = useSelector((s: RootState) => s.auth.user);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile</h1>
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center text-xl font-bold text-blue-600">
            {user?.name?.charAt(0)?.toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-gray-800">{user?.name}</p>
            <p className="text-sm text-gray-400">{user?.email}</p>
          </div>
        </div>
        <div className="space-y-3 text-sm border-t border-gray-50 pt-4">
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Role</span>
            <span className="font-medium capitalize">{user?.role?.toLowerCase()}</span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="mt-6 w-full py-2.5 border border-red-200 text-red-600 rounded-xl text-sm font-medium hover:bg-red-50 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;
