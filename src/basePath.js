const rawBaseUrl = import.meta.env.BASE_URL || '/';

export const APP_BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl : `${rawBaseUrl}/`;
export const APP_BASENAME = APP_BASE_URL === '/' ? '' : APP_BASE_URL.replace(/\/$/, '');

export const withBasePath = (path = '') => {
  const normalizedPath = String(path || '').replace(/^\/+/, '');
  return `${APP_BASE_URL}${normalizedPath}`;
};
