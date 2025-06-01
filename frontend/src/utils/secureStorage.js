/**
 * Secure Storage Utility for Admin Tokens
 * Provides better security than localStorage for sensitive data
 */

class SecureStorage {
  constructor() {
    this.keyPrefix = 'brb_secure_';
    this.tokenKey = `${this.keyPrefix}admin_token`;
    this.sessionKey = `${this.keyPrefix}session_id`;
  }

  /**
   * Store admin token with enhanced security
   * @param {string} token - Admin token to store
   * @param {number} expirationMinutes - Token expiration in minutes (default: 60)
   */
  setAdminToken(token, expirationMinutes = 60) {
    try {
      const tokenData = {
        token: token,
        timestamp: Date.now(),
        expiration: Date.now() + (expirationMinutes * 60 * 1000),
        sessionId: this.generateSessionId()
      };

      // Use sessionStorage instead of localStorage for better security
      sessionStorage.setItem(this.tokenKey, JSON.stringify(tokenData));
      sessionStorage.setItem(this.sessionKey, tokenData.sessionId);
      
      // Also set a backup in localStorage with shorter expiration
      localStorage.setItem(this.tokenKey, JSON.stringify({
        ...tokenData,
        expiration: Date.now() + (15 * 60 * 1000) // 15 minutes for localStorage
      }));

      return true;
    } catch (error) {
      console.error('Failed to store admin token:', error);
      return false;
    }
  }

  /**
   * Retrieve admin token with security validation
   * @returns {string|null} - Valid token or null if expired/invalid
   */
  getAdminToken() {
    try {
      // Try sessionStorage first (more secure)
      let tokenData = this.getTokenData(sessionStorage);
      
      // Fallback to localStorage if sessionStorage is empty
      if (!tokenData) {
        tokenData = this.getTokenData(localStorage);
      }

      if (!tokenData) {
        return null;
      }

      // Check if token is expired
      if (Date.now() > tokenData.expiration) {
        this.clearAdminToken();
        return null;
      }

      // Validate session integrity
      if (!this.validateSession(tokenData.sessionId)) {
        this.clearAdminToken();
        return null;
      }

      return tokenData.token;
    } catch (error) {
      console.error('Failed to retrieve admin token:', error);
      this.clearAdminToken();
      return null;
    }
  }

  /**
   * Clear all admin token data
   */
  clearAdminToken() {
    try {
      sessionStorage.removeItem(this.tokenKey);
      sessionStorage.removeItem(this.sessionKey);
      localStorage.removeItem(this.tokenKey);
      localStorage.removeItem(this.sessionKey);
    } catch (error) {
      console.error('Failed to clear admin token:', error);
    }
  }

  /**
   * Check if admin token exists and is valid
   * @returns {boolean}
   */
  hasValidAdminToken() {
    return this.getAdminToken() !== null;
  }

  /**
   * Get remaining token time in minutes
   * @returns {number} - Minutes until expiration, 0 if expired/invalid
   */
  getTokenRemainingTime() {
    try {
      const tokenData = this.getTokenData(sessionStorage) || this.getTokenData(localStorage);
      
      if (!tokenData) {
        return 0;
      }

      const remaining = tokenData.expiration - Date.now();
      return Math.max(0, Math.floor(remaining / (60 * 1000)));
    } catch (error) {
      return 0;
    }
  }

  /**
   * Extend token expiration (if valid)
   * @param {number} additionalMinutes - Minutes to add to expiration
   */
  extendTokenExpiration(additionalMinutes = 30) {
    const currentToken = this.getAdminToken();
    if (currentToken) {
      this.setAdminToken(currentToken, additionalMinutes);
    }
  }

  // Private helper methods
  getTokenData(storage) {
    try {
      const data = storage.getItem(this.tokenKey);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      return null;
    }
  }

  generateSessionId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  validateSession(sessionId) {
    try {
      const storedSessionId = sessionStorage.getItem(this.sessionKey);
      return storedSessionId === sessionId;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const secureStorage = new SecureStorage();

// Export class for testing
export { SecureStorage };

// Utility functions for backward compatibility
export const setAdminToken = (token) => secureStorage.setAdminToken(token);
export const getAdminToken = () => secureStorage.getAdminToken();
export const clearAdminToken = () => secureStorage.clearAdminToken();
export const hasValidAdminToken = () => secureStorage.hasValidAdminToken();