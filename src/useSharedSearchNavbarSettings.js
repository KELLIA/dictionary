import { useEffect, useMemo, useState } from 'react';
import { loadSearchSettings, saveSearchSettings, DEFAULT_SEARCH_SETTINGS } from './searchSettingsStorage';
import { getCachedIndexData, preloadIndexData } from './indexDataCache';

const getAvailablePos = (entries = []) => {
  const posSet = new Set(entries.map((entry) => entry?.pos).filter(Boolean));
  return Array.from(posSet).sort();
};

export default function useSharedSearchNavbarSettings() {
  const persistedSettings = useMemo(() => loadSearchSettings(), []);

  const [showAdvanced, setShowAdvanced] = useState(persistedSettings.showAdvanced);
  const [dialects, setDialects] = useState(new Set(persistedSettings.dialects));
  const [languages, setLanguages] = useState(new Set(persistedSettings.languages));
  const [searchType, setSearchType] = useState(persistedSettings.searchType);
  const [posFilter, setPosFilter] = useState(persistedSettings.posFilter);
  const [availablePos, setAvailablePos] = useState(() => getAvailablePos(getCachedIndexData() || []));

  useEffect(() => {
    let isMounted = true;

    preloadIndexData()
      .then((data) => {
        if (!isMounted) return;
        setAvailablePos(getAvailablePos(data));
      })
      .catch((error) => {
        console.error('Failed to load POS filter options:', error);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    saveSearchSettings({
      showAdvanced,
      dialects: Array.from(dialects),
      languages: Array.from(languages),
      searchType,
      posFilter,
    });
  }, [showAdvanced, dialects, languages, searchType, posFilter]);

  const navbarSettingsProps = {
    showAdvanced,
    onToggleAdvanced: () => setShowAdvanced(!showAdvanced),
    searchType,
    onSearchTypeChange: setSearchType,
    posFilter,
    onPosFilterChange: setPosFilter,
    dialects,
    onDialectsChange: setDialects,
    allDialects: DEFAULT_SEARCH_SETTINGS.dialects,
    languages,
    onLanguagesChange: setLanguages,
  };

  return {
    showAdvanced,
    setShowAdvanced,
    availablePos,
    dialects,
    setDialects,
    languages,
    setLanguages,
    searchType,
    setSearchType,
    posFilter,
    setPosFilter,
    navbarSettingsProps,
  };
}