import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  isAuthenticated,
  getCurrentUser,
  getToken,
  logout,
  hasRole,
  canAccess,
  getAuthHeaders
} from '../services/auth'

describe('auth service', () => {
  const mockUser = {
    username: 'testuser',
    fullName: 'Test User',
    role: 'ADMIN'
  }

  // Валидный JWT токен (exp в далеком будущем)
  const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6OTk5OTk5OTk5OX0.test'

  // Просроченный токен
  const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTAwMDAwMDAwMH0.test'

  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('isAuthenticated', () => {
    it('returns false when no token', () => {
      expect(isAuthenticated()).toBe(false)
    })

    it('returns true when valid token exists', () => {
      localStorage.setItem('warehouse_auth_token', validToken)
      expect(isAuthenticated()).toBe(true)
    })

    it('returns false and clears expired token', () => {
      localStorage.setItem('warehouse_auth_token', expiredToken)
      expect(isAuthenticated()).toBe(false)
      expect(localStorage.getItem('warehouse_auth_token')).toBeNull()
    })
  })

  describe('getCurrentUser', () => {
    it('returns null when no user stored', () => {
      expect(getCurrentUser()).toBeNull()
    })

    it('returns user object when stored', () => {
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))
      expect(getCurrentUser()).toEqual(mockUser)
    })

    it('returns null for invalid JSON', () => {
      localStorage.setItem('warehouse_user', 'invalid json')
      expect(getCurrentUser()).toBeNull()
    })
  })

  describe('getToken', () => {
    it('returns null when no token', () => {
      expect(getToken()).toBeNull()
    })

    it('returns token when stored', () => {
      localStorage.setItem('warehouse_auth_token', validToken)
      expect(getToken()).toBe(validToken)
    })
  })

  describe('logout', () => {
    it('clears token and user from localStorage', () => {
      localStorage.setItem('warehouse_auth_token', validToken)
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))

      logout()

      expect(localStorage.getItem('warehouse_auth_token')).toBeNull()
      expect(localStorage.getItem('warehouse_user')).toBeNull()
    })
  })

  describe('hasRole', () => {
    it('returns false when no user', () => {
      expect(hasRole('ADMIN')).toBe(false)
    })

    it('returns true for matching role', () => {
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))
      expect(hasRole('ADMIN')).toBe(true)
    })

    it('returns false for non-matching role', () => {
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))
      expect(hasRole('SUPER_USER')).toBe(false)
    })

    it('works with array of roles', () => {
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))
      expect(hasRole(['ADMIN', 'MANAGER'])).toBe(true)
      expect(hasRole(['SUPER_USER', 'MANAGER'])).toBe(false)
    })
  })

  describe('canAccess', () => {
    it('returns false when no user', () => {
      expect(canAccess('system-status')).toBe(false)
    })

    it('returns true for allowed feature', () => {
      localStorage.setItem('warehouse_user', JSON.stringify(mockUser))
      expect(canAccess('system-status')).toBe(true)
    })

    it('returns false for non-allowed feature', () => {
      localStorage.setItem('warehouse_user', JSON.stringify({ ...mockUser, role: 'EMPLOYEE' }))
      expect(canAccess('system-status')).toBe(false)
    })
  })

  describe('getAuthHeaders', () => {
    it('returns empty object when no token', () => {
      expect(getAuthHeaders()).toEqual({})
    })

    it('returns Authorization header when token exists', () => {
      localStorage.setItem('warehouse_auth_token', validToken)
      expect(getAuthHeaders()).toEqual({
        Authorization: `Bearer ${validToken}`
      })
    })
  })
})
