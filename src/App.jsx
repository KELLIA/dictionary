import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, useLocation, Link } from 'react-router-dom';
import './bootstrap.min.css';
import './font-awesome-4.2.0/css/font-awesome.min.css';
import './index.css';
import { getCachedIndexData, preloadIndexData } from './indexDataCache';
import { SiteHeader, SiteFooter } from './SiteChrome';
import useSharedSearchNavbarSettings from './useSharedSearchNavbarSettings';
import { withBasePath } from './basePath';
import { ASCII_TO_COPTIC_MAP } from './SearchNavbar';
import { SearchExampleLink } from './Help';

const COPTIC_REGEX = /[\u03E2-\u03EF\u2C80-\u2CFF]/;
const ALL_DIALECTS = ['A', 'Ak', 'B', 'F', 'M', 'L', 'P', 'S', 'V', 'W', '?'];

const translateAsciiToCoptic = (text) => {
  if (!text) return '';
  return text.replace(/_([^_]+)_/g, (match, asciiContent) => {
    return asciiContent.split('').map(char => ASCII_TO_COPTIC_MAP[char] || char).join('');
  });
};

// Helper to escape regex characters
const escapeRegExp = (string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const hasRegexOperators = (token) => escapeRegExp(token) !== token;

const normalizeSegmentationKey = (value) => {
  return (value || '')
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '');
};

const parseSegmentationTable = (tableText) => {
  const nextMap = new Map();

  tableText.split(/\r?\n/).forEach((line) => {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine.startsWith('#')) return;

    const segments = trimmedLine
      .split('|')
      .map(normalizeWordToken)
      .filter(Boolean);

    if (segments.length < 2) return;

    const key = normalizeSegmentationKey(segments.join(''));
    if (!key) return;

    const existing = nextMap.get(key) || [];
    const isDuplicate = existing.some(
      (existingSegments) =>
        existingSegments.length === segments.length &&
        existingSegments.every((segment, index) => segment === segments[index])
    );

    if (!isDuplicate) {
      existing.push(segments);
      nextMap.set(key, existing);
    }
  });

  return nextMap;
};

const parseVideTable = (tableText) => {
  const nextMap = new Map();

  tableText.split(/\r?\n/).forEach((line) => {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine.startsWith('#')) return;

    // Split by whitespace (spaces or tabs)
    const parts = trimmedLine.split(/\s+/);
    
    if (parts.length >= 2) {
      const key = normalizeSegmentationKey(parts[0]);
      if (key) {
        nextMap.set(key, parts[1].trim());
      }
    }
  });

  return nextMap;
};

const normalizeWordToken = (value) => {
  return (value || '')
    .trim()
    .toLowerCase()
    .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '');
};

const tokenizeWords = (value) => {
  return (value || '')
    .split(/\s+/)
    .map(normalizeWordToken)
    .filter(Boolean);
};

const normalizeIdToken = (value) => {
  return (value || '')
    .trim()
    .toUpperCase()
    .replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '');
};

const parseIdCriterion = (term) => {
  const normalized = normalizeIdToken(term);
  if (!/^CF?\d+$/i.test(normalized)) return null;
  return normalized;
};

const matchesEntryIdCriterion = (entry, idCriterion) => {
  if (!entry || !idCriterion) return false;

  if (String(entry.id || '').toUpperCase() === idCriterion) {
    return true;
  }

  if (Array.isArray(entry.form_ids)) {
    if (entry.form_ids.some((formId) => String(formId || '').toUpperCase() === idCriterion)) {
      return true;
    }
  }

  if (Array.isArray(entry.forms)) {
    return entry.forms.some((form) => String(form?.id || '').toUpperCase() === idCriterion);
  }

  return false;
};

const matchesWholeWord = (term, value) => {
  const normalizedTerm = normalizeWordToken(term);
  if (!normalizedTerm) return false;
  return tokenizeWords(value).includes(normalizedTerm);
};

const buildSearchRegex = (term, searchType, isCopticTerm, useRegexToken) => {
  if (!useRegexToken) {
    if (searchType === 'whole') {
      return isCopticTerm
        ? new RegExp(`^${escapeRegExp(term)}$`, 'i')
        : new RegExp(`\\b${escapeRegExp(term)}\\b`, 'i');
    }

    if (searchType === 'startsWith') {
      return isCopticTerm
        ? new RegExp(`^${escapeRegExp(term)}`, 'i')
        : new RegExp(`\\b${escapeRegExp(term)}`, 'i');
    }

    return new RegExp(escapeRegExp(term), 'i');
  }

  let pattern = term;

  if (searchType === 'startsWith') {
    if (isCopticTerm) {
      if (!pattern.startsWith('^')) pattern = `^${pattern}`;
    } else if (!pattern.startsWith('^') && !pattern.startsWith('\\b')) {
      pattern = `\\b${pattern}`;
    }
  }

  if (searchType === 'whole') {
    if (isCopticTerm) {
      if (!pattern.startsWith('^')) pattern = `^${pattern}`;
      if (!pattern.endsWith('$')) pattern = `${pattern}$`;
    } else {
      if (!pattern.startsWith('^') && !pattern.startsWith('\\b')) {
        pattern = `\\b${pattern}`;
      }
      if (!pattern.endsWith('$') && !pattern.endsWith('\\b')) {
        pattern = `${pattern}\\b`;
      }
    }
  }

  return new RegExp(pattern, 'i');
};

export default function App() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';
  const [searchInput, setSearchInput] = useState(query);

  useEffect(() => {
    const legacyPath = location.pathname === '/results.py' || location.pathname === '/entry.py' || 
      location.pathname === '/results.cgi' || location.pathname === '/entry.cgi';
    const hasLegacyParams =
      searchParams.has('quick_search') ||
      searchParams.has('tla') ||
      searchParams.has('coptic') ||
      searchParams.has('definition');

    if (!legacyPath && !hasLegacyParams) return;

    const normalizeLegacyToken = (value) =>
      (value || '')
        .replace(/[\u0000-\u001F\u007F]/g, '')
        .trim();

    const queryParts = [
      searchParams.get('q'),
      searchParams.get('quick_search'),
      searchParams.get('tla'),
      searchParams.get('coptic'),
      searchParams.get('definition'),
    ]
      .map(normalizeLegacyToken)
      .filter(Boolean);

    const mergedQuery = queryParts.join(' ').replace(/\s+/g, ' ').trim();

    if (!mergedQuery) {
      navigate('/', { replace: true, state: { keepSearchFocus: true } });
      return;
    }

    navigate(`/?q=${encodeURIComponent(mergedQuery)}`, {
      replace: true,
      state: { keepSearchFocus: true },
    });
  }, [location.pathname, searchParams, navigate]);

  const setQuery = (nextQuery, options = {}) => {
    const { replace = true } = options;
    const normalized = (nextQuery || '').trim();
    if (!normalized) {
      navigate('/', { replace, state: { keepSearchFocus: true } });
      return;
    }
    navigate(`/?q=${encodeURIComponent(nextQuery)}`, {
      replace,
      state: { keepSearchFocus: true },
    });
  };

  const [indexData, setIndexData] = useState(() => getCachedIndexData() || []);
  const [isIndexReady, setIsIndexReady] = useState(() => Boolean(getCachedIndexData()));
  
  const [segmentationMap, setSegmentationMap] = useState(() => new Map());
  const [isSegmentationReady, setIsSegmentationReady] = useState(false);

  const [videMap, setVideMap] = useState(() => new Map());
  const [isVideReady, setIsVideReady] = useState(false);

  useEffect(() => {
    if (query !== searchInput) {
      setSearchInput(query);
    }
  }, [query]);
  
  const {
    dialects,
    languages,
    searchType,
    posFilter,
    navbarSettingsProps,
  } = useSharedSearchNavbarSettings();
  
  const [sortBy, setSortBy] = useState('relevance');
  
  const availablePos = useMemo(() => {
    const posSet = new Set(indexData.map(entry => entry.pos).filter(Boolean));
    return Array.from(posSet).sort();
  }, [indexData]);

  useEffect(() => {
    if (indexData.length > 0) {
      setIsIndexReady(true);
      return;
    }

    let isMounted = true;
    preloadIndexData()
      .then(data => {
        if (isMounted) {
          setIndexData(data);
          setIsIndexReady(true);
        }
      })
      .catch(err => {
        console.error("Failed to load index:", err);
        if (isMounted) setIsIndexReady(true);
      });

    return () => {
      isMounted = false;
    };
  }, [indexData.length]);

  useEffect(() => {
    let isMounted = true;

    fetch(withBasePath('seg_data.tab'))
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load seg_data.tab: ${res.status}`);
        return res.text();
      })
      .then((tableText) => {
        if (!isMounted) return;
        setSegmentationMap(parseSegmentationTable(tableText));
        setIsSegmentationReady(true);
      })
      .catch((err) => {
        console.error('Failed to load segmentation table:', err);
        if (isMounted) setIsSegmentationReady(true);
      });

    fetch(withBasePath('vide.tab'))
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load vide.tab: ${res.status}`);
        return res.text();
      })
      .then((tableText) => {
        if (!isMounted) return;
        setVideMap(parseVideTable(tableText));
        setIsVideReady(true);
      })
      .catch((err) => {
        console.error('Failed to load vide table:', err);
        if (isMounted) setIsVideReady(true);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const q = formData.get('q');
    if (q) {
      navigate(`/?q=${encodeURIComponent(q)}`);
    }
  };

  // Convert any ASCII mapped search text to Coptic for internal matching
  const processedQuery = useMemo(() => translateAsciiToCoptic(query), [query]);

  const filteredResults = useMemo(() => {
    if (!processedQuery?.trim()) return [];

    const terms = processedQuery.trim().split(/\s+/).filter(Boolean);
    const tokenSearches = terms.map(term => ({
      term,
      idCriterion: parseIdCriterion(term),
      isCopticTerm: COPTIC_REGEX.test(term),
      useRegexToken: hasRegexOperators(term),
    }));

    return indexData.filter(entry => {
      if (posFilter !== 'any' && entry.pos !== posFilter) return false;

      const validForms = entry.forms && entry.forms.length > 0
        ? entry.forms.filter(f => dialects.has(f.dialect || '?'))
        : (dialects.has('?') ? [{ orth: entry.lemma }] : []);

      if (validForms.length === 0) return false;

      const formsToSearch = validForms.map(f => f.orth);

      const matchesDefinitions = (regex) => {
        return entry.senses?.some(sense => {
          return Object.entries(sense.translations || {}).some(([lang, defs]) => {
            if (!languages.has(lang)) return false;
            return defs.some(def => regex.test(def));
          });
        });
      };

      const matchesWholeWords = (term, isCopticTerm) => {
        if (isCopticTerm) {
          return formsToSearch.some(orth => matchesWholeWord(term, orth));
        }

        return entry.senses?.some(sense => {
          return Object.entries(sense.translations || {}).some(([lang, defs]) => {
            if (!languages.has(lang)) return false;
            return defs.some(def => matchesWholeWord(term, def));
          });
        });
      };

      return tokenSearches.every(({ term, idCriterion, isCopticTerm, useRegexToken }) => {
        if (idCriterion) {
          return matchesEntryIdCriterion(entry, idCriterion);
        }

        if (searchType === 'whole' && !useRegexToken) {
          return matchesWholeWords(term, isCopticTerm);
        }

        let regex;
        try {
          regex = buildSearchRegex(term, searchType, isCopticTerm, useRegexToken);
        } catch (e) {
          return false;
        }

        if (isCopticTerm) {
          return formsToSearch.some(orth => regex.test(orth));
        }

        return matchesDefinitions(regex);
      });
    });
  }, [processedQuery, indexData, posFilter, dialects, languages, searchType]);

  useEffect(() => {
    if (query && filteredResults.length === 1) {
      navigate(`/entry/${filteredResults[0].id}`, {
        replace: true,
        state: {
          preloadedEntry: filteredResults[0],
          searchQuery: query,
          keepSearchFocus: Boolean(location.state?.keepSearchFocus),
        }
      });
    }
  }, [query, filteredResults, navigate, location.state]);

  const searchData = useMemo(() => {
    if (!processedQuery?.trim()) return { results: [], totalCount: 0 };

    const qRaw = processedQuery.trim().toLowerCase();
    const filtered = [...filteredResults];

    filtered.forEach(entry => {
      let score = 0;
      const lemma = (entry.lemma || '').toLowerCase().replace(/[*⸗︦̄-]/g, '');
      const forms = entry.forms ? entry.forms.map(f => (f.orth || '').toLowerCase()) : [];
      
      if (lemma === qRaw) score += 100000;
      if (forms.includes(qRaw)) score += 10000;
      if (lemma.startsWith(qRaw)) score += 1000;
      if (forms.some(f => f.startsWith(qRaw))) score += 100;
      if (lemma.includes(qRaw)) score += 50;
      if (forms.some(f => f.includes(qRaw))) score += 5;
      
      const allDefs = (entry.senses || []).flatMap(s => 
        Object.values(s.translations || {}).flat()
      ).join(' ').toLowerCase();
      
      const exactDefRegex = new RegExp('\\b' + escapeRegExp(qRaw) + '\\b', 'i');
      const prefixDefRegex = new RegExp('\\b' + escapeRegExp(qRaw), 'i');
      const containsDefRegex = new RegExp(escapeRegExp(qRaw), 'i');
      
      if (exactDefRegex.test(allDefs)) score += 10;
      if (prefixDefRegex.test(allDefs)) score += 3;
      if (containsDefRegex.test(allDefs)) score += 1;
      
      entry._relevanceScore = score;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'relevance') {
        if (b._relevanceScore !== a._relevanceScore) {
          return b._relevanceScore - a._relevanceScore;
        }
      }

      if (sortBy === 'relevance' || sortBy === 'frequency') {
        const freqA = a.lemma_freq ?? 0;
        const freqB = b.lemma_freq ?? 0;
        if (freqB !== freqA) {
          return freqB - freqA;
        }
      }

      return (a.lemma || '').localeCompare(b.lemma || '');
    });

    const totalCount = filtered.length;
    return { results: filtered.slice(0, 200), totalCount };
  }, [processedQuery, filteredResults, sortBy]);

  const { results, totalCount } = searchData;
  const hasQuery = Boolean(processedQuery?.trim());
  const showPendingSearchState = hasQuery && !isIndexReady;

  const segmentedFallbackSuggestions = useMemo(() => {
    if (!hasQuery || showPendingSearchState || results.length > 0 || !isSegmentationReady) {
      return [];
    }

    const queryKey = normalizeSegmentationKey(processedQuery);
    if (!queryKey) return [];

    const segmentations = segmentationMap.get(queryKey) || [];
    if (segmentations.length === 0) return [];

    const seenSegments = new Set();
    const flatSegments = [];

    segmentations.forEach((segmentation) => {
      segmentation.forEach((segment) => {
        if (!seenSegments.has(segment)) {
          seenSegments.add(segment);
          flatSegments.push(segment);
        }
      });
    });

    return flatSegments;
  }, [hasQuery, showPendingSearchState, results.length, isSegmentationReady, processedQuery, segmentationMap]);

  const videFallbackSuggestion = useMemo(() => {
    if (!hasQuery || showPendingSearchState || results.length > 0 || segmentedFallbackSuggestions.length > 0 || !isVideReady) {
      return null;
    }

    const queryKey = normalizeSegmentationKey(processedQuery);
    if (!queryKey) return null;

    return videMap.get(queryKey) || null;
  }, [hasQuery, showPendingSearchState, results.length, segmentedFallbackSuggestions.length, isVideReady, processedQuery, videMap]);

  return (
    <div className="container">
      <SiteHeader
        activePage="home"
        searchNavbarProps={{
          searchInput,
          onSearchInputChange: (nextValue) => {
            setSearchInput(nextValue);
            setQuery(nextValue);
          },
          autoFocus: true,
          availablePos,
          ...navbarSettingsProps,
        }}
      />

      <div className="bs-docs-section" style={{ marginTop: '20px' }}>
        <div className="row">
          <div className="col-lg-12">
            <div className="bs-component">
              <div className="content">
                {hasQuery ? (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', flexWrap: 'wrap', gap: '10px' }}>
                      <p style={{ margin: 0 }}>
                        You searched for '<span style={{ fontFamily: 'antinoouRegular, sans-serif', fontWeight: 'bold' }}>{query}</span>' 
                        {processedQuery !== query && (
                          <span className="text-muted" style={{ marginLeft: '5px' }}>(interpreted as <strong>{processedQuery}</strong>)</span>
                        )}
                        {showPendingSearchState ? (
                          <span className="text-muted" style={{ marginLeft: '10px' }}>(Searching...)</span>
                        ) : (
                          <span className="text-muted" style={{ marginLeft: '10px' }}>
                            ({totalCount} Results{totalCount > 200 ? ', showing top 200' : ''})
                          </span>
                        )}
                      </p>
                      <div>
                        <label style={{ fontWeight: 'normal', margin: 0 }}>Sort by: </label>
                        <select 
                          value={sortBy} 
                          onChange={e => setSortBy(e.target.value)}
                          style={{ marginLeft: '8px', padding: '2px 5px', borderRadius: '4px', border: '1px solid #ccc' }}
                        >
                          <option value="relevance">Relevance</option>
                          <option value="frequency">Frequency</option>
                          <option value="alphabetic">Alphabetic</option>
                        </select>
                      </div>
                    </div>
                    
                    <table id="results" className="entrylist" style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        {showPendingSearchState ? (
                          <tr>
                            <td className="text-muted" style={{ padding: '12px 0' }}>Loading search index...</td>
                          </tr>
                        ) : results.length > 0 ? results.map(entry => {
                          const altForms = entry.forms 
                            ? Array.from(new Set(entry.forms.map(f => f.orth).filter(o => o !== entry.lemma)))
                            : [];

                          const previewDefs = entry.senses?.map(s => 
                            s.translations?.en?.[0] || s.translations?.fr?.[0] || s.translations?.de?.[0]
                          ).filter(Boolean) || [];

                          return (
                            <tr key={entry.id}>
                              <td className="orth_cell" style={{ width: '20%', fontSize: '1.2em', border: 'none', padding: '8px 0' }}>
                                <Link to={`/entry/${entry.id}`} state={{ preloadedEntry: entry, searchQuery: query }}>
                                  {entry.lemma}
                                </Link>
                              </td>
                              <td className="second_orth_cell" style={{ width: '30%', color: '#666', border: 'none', padding: '8px 0', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                                {altForms.length > 0 ? altForms.join(', ') : '--'}
                              </td>
                              <td className="sense_cell" style={{ border: 'none', padding: '8px 0', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                                {previewDefs.length > 1 ? (
                                  <ol className="sense_list" style={{ paddingLeft: '20px', margin: 0 }}>
                                    {previewDefs.map((def, i) => <li key={i}>{def}</li>)}
                                  </ol>
                                ) : (
                                  <div className="single_sense">{previewDefs[0]}</div>
                                )}
                              </td>
                            </tr>
                          );
                        }) : (
                          <tr>
                            <td colSpan={3} style={{ padding: '12px 0' }}>
                              {(!isSegmentationReady || !isVideReady) ? (
                                <span className="text-muted">Checking orthography...</span>
                              ) : segmentedFallbackSuggestions.length > 0 ? (
                                <div>
                                  <div>This may be a complex word form; search instead for:</div>
                                  <div style={{ marginTop: '6px' }}>
                                    {segmentedFallbackSuggestions.map((segment, index) => (
                                      <React.Fragment key={segment}>
                                        <a
                                          href="#"
                                          onClick={(event) => {
                                            event.preventDefault();
                                            setSearchInput(segment);
                                            setQuery(segment, { replace: false });
                                          }}
                                          style={{ fontFamily: 'antinoouRegular, sans-serif' }}
                                        >
                                          {segment}
                                        </a>
                                        {index < segmentedFallbackSuggestions.length - 1 ? ' - ' : ''}
                                      </React.Fragment>
                                    ))}
                                  </div>
                                </div>
                              ) : videFallbackSuggestion ? (
                                <div>
                                  <span>This may be a form of </span>
                                  <a
                                    href="#"
                                    onClick={(event) => {
                                      event.preventDefault();
                                      setSearchInput(videFallbackSuggestion);
                                      setQuery(videFallbackSuggestion, { replace: false });
                                    }}
                                    style={{ fontFamily: 'antinoouRegular, sans-serif' }}
                                  >
                                    {videFallbackSuggestion}
                                  </a>
                                </div>
                              ) : (
                                <span className="text-muted">No results found.</span>
                              )}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </>
                ) : (
                  <div style={{ padding: '0px 0', fontSize: '1.05em', lineHeight: '1.6' }}>
                    <h2>Welcome to the Coptic Dictionary!</h2>
                    <p>
                      Search for Coptic words or definitions separately or combined, using Unicode or Latin characters. 
                    </p>
                    <h3>Basic examples</h3>
                    <ul>
                      <li>Coptic word (in Unicode): <SearchExampleLink query="ⲥⲙⲟⲩ" navigate={navigate} searchType="substring">ⲥⲙⲟⲩ</SearchExampleLink></li>
                      <li>Words in definition (English/French/German): <SearchExampleLink query="bless" navigate={navigate} searchType="substring">bless</SearchExampleLink> / <SearchExampleLink query="bénir" navigate={navigate} searchType="substring">bénir</SearchExampleLink> / <SearchExampleLink query="segnen" navigate={navigate} searchType="substring">segnen</SearchExampleLink></li>
                      <li>Coptic word (in Latin letters, with underscores): <SearchExampleLink query="_smou_" navigate={navigate} searchType="substring">_smou_</SearchExampleLink></li> (click the <i className="fa fa-question-circle"></i> icon in the search bar for more information on Latin input)
                      <li>Combined search: <SearchExampleLink query="ⲥⲙⲟⲩ blessing" navigate={navigate} searchType="substring">ⲥⲙⲟⲩ blessing</SearchExampleLink></li>
                    </ul>
                    <h3>Advanced search</h3>
                    <p>
                      For advanced options (search by dialect, part of speech, etc.), please click the <strong>cog icon</strong> (<i className="fa fa-cog"></i>) in the search bar.
                    </p>
                    <p>
                      For more complex searches, see our <Link to="/help">how to</Link> guide. For more information on the dictionary, please see the <Link to="/about">About page</Link>.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <SiteFooter />
    </div>
  );
}