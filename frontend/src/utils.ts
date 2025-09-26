import type { User } from './types';

/**
 * Role precedence order (highest to lowest)
 */
export const ROLE_PRECEDENCE = ['ADMIN', 'CEO', 'BDO', 'VDO'] as const;

/**
 * Get the highest precedence role for a user
 * @param user User object
 * @returns The highest precedence role or null if no recognized roles
 */
export const getUserHighestRole = (user: User): string | null => {
  if (!user.roles || user.roles.length === 0) {
    return null;
  }

  // Find the highest precedence role
  for (const role of ROLE_PRECEDENCE) {
    if (user.roles.includes(role)) {
      return role;
    }
  }

  // If no recognized roles, return the first role
  return user.roles[0] || null;
};

/**
 * Check if user has any of the specified roles
 * @param user User object
 * @param roles Array of roles to check
 * @returns true if user has any of the specified roles
 */
export const userHasRole = (user: User, roles: string[]): boolean => {
  if (!user.roles || user.roles.length === 0) {
    return false;
  }

  return roles.some(role => user.roles.includes(role));
};

/**
 * Check if user has admin privileges (ADMIN, CEO, BDO)
 * @param user User object
 * @returns true if user has admin privileges
 */
export const userHasAdminPrivileges = (user: User): boolean => {
  return userHasRole(user, ['ADMIN', 'CEO', 'BDO']);
};

/**
 * Check if user is a worker (VDO)
 * @param user User object
 * @returns true if user is a worker
 */
export const userIsWorker = (user: User): boolean => {
  return userHasRole(user, ['VDO']);
};

/**
 * Get user's full name from positions
 * @param user User object
 * @returns Full name or username as fallback
 */
export const getUserFullName = (user: User): string => {
  if (user.positions && user.positions.length > 0) {
    const position = user.positions[0]; // Get first position
    const parts = [
      position.first_name,
      position.middle_name,
      position.last_name
    ].filter(Boolean);
    
    if (parts.length > 0) {
      return parts.join(' ');
    }
  }
  
  return user.username;
};