const STORAGE_KEY = 'cdo.searchSettings.v1';
const ALLOWED_SEARCH_TYPES = ['startsWith', 'substring', 'whole'];

export const DEFAULT_SEARCH_SETTINGS = {
  showAdvanced: false,
  dialects: ['A', 'Ak', 'B', 'F', 'M', 'L', 'P', 'S', 'V', 'W', '?'],
  languages: ['en', 'fr', 'de'],
  searchType: 'startsWith',
  posFilter: 'any',
};

const normalizeList = (value, fallback) => {
  if (!Array.isArray(value) || value.length === 0) return [...fallback];
  return Array.from(new Set(value.filter(Boolean)));
};

export const loadSearchSettings = () => {
  if (typeof window === 'undefined') {
    return {
      ...DEFAULT_SEARCH_SETTINGS,
      dialects: [...DEFAULT_SEARCH_SETTINGS.dialects],
      languages: [...DEFAULT_SEARCH_SETTINGS.languages],
    };
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {
        ...DEFAULT_SEARCH_SETTINGS,
        dialects: [...DEFAULT_SEARCH_SETTINGS.dialects],
        languages: [...DEFAULT_SEARCH_SETTINGS.languages],
      };
    }

    const parsed = JSON.parse(raw);
    const parsedSearchType = typeof parsed.searchType === 'string' ? parsed.searchType : '';
    const normalizedSearchType = parsedSearchType === 'regex'
      ? 'substring'
      : parsedSearchType;

    return {
      showAdvanced: Boolean(parsed.showAdvanced),
      dialects: normalizeList(parsed.dialects, DEFAULT_SEARCH_SETTINGS.dialects),
      languages: normalizeList(parsed.languages, DEFAULT_SEARCH_SETTINGS.languages),
      searchType: ALLOWED_SEARCH_TYPES.includes(normalizedSearchType)
        ? normalizedSearchType
        : DEFAULT_SEARCH_SETTINGS.searchType,
      posFilter: typeof parsed.posFilter === 'string' && parsed.posFilter
        ? parsed.posFilter
        : DEFAULT_SEARCH_SETTINGS.posFilter,
    };
  } catch {
    return {
      ...DEFAULT_SEARCH_SETTINGS,
      dialects: [...DEFAULT_SEARCH_SETTINGS.dialects],
      languages: [...DEFAULT_SEARCH_SETTINGS.languages],
    };
  }
};

export const saveSearchSettings = (settings) => {
  if (typeof window === 'undefined') return;

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Ignore storage failures, e.g. private mode or disabled persistence.
  }
};