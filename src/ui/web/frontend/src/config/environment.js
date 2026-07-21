/**
 * Environment Configuration
 * Centralized environment detection and configuration
 */

export const ENV = {
  DEV: 'development',
  PROD: 'production',
  TEST: 'test'
}

export const getCurrentEnv = () => {
  if (import.meta.env.MODE === 'production') return ENV.PROD
  if (import.meta.env.MODE === 'test') return ENV.TEST
  return ENV.DEV
}

export const isDev = () => getCurrentEnv() === ENV.DEV
export const isProd = () => getCurrentEnv() === ENV.PROD
export const isTest = () => getCurrentEnv() === ENV.TEST
