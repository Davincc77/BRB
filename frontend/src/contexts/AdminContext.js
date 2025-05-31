import React, { createContext, useContext, useState, useEffect } from 'react';

const AdminContext = createContext();

export const useAdmin = () => {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error('useAdmin must be used within an AdminProvider');
  }
  return context;
};

export const AdminProvider = ({ children }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminUser, setAdminUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is admin based on their Twitter handle
  const checkAdminStatus = (user) => {
    if (user && user.twitter && user.twitter.username) {
      return user.twitter.username.toLowerCase() === 'davincc';
    }
    return false;
  };

  const setUser = (user) => {
    setAdminUser(user);
    setIsAdmin(checkAdminStatus(user));
    setIsLoading(false);
  };

  const logout = () => {
    setAdminUser(null);
    setIsAdmin(false);
    setIsLoading(false);
  };

  const value = {
    isAdmin,
    adminUser,
    isLoading,
    setUser,
    logout,
    checkAdminStatus
  };

  return (
    <AdminContext.Provider value={value}>
      {children}
    </AdminContext.Provider>
  );
};