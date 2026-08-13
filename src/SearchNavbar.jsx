import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { withBasePath } from './basePath';

const DEFAULT_LANGUAGES = ['en', 'fr', 'de'];
const SELECTION_STATE_MAX_AGE_MS = 15000;

const ASCII_COPTIC_PAIRS = [
  ['a', 'ⲁ'], ['b', 'ⲃ'], ['g', 'ⲅ'], ['d', 'ⲇ'], ['e', 'ⲉ'], ['z', 'ⲍ'], ['E', 'ⲏ'], ['8', 'ⲑ'],
  ['i', 'ⲓ'], ['k', 'ⲕ'], ['l', 'ⲗ'], ['m', 'ⲙ'], ['n', 'ⲛ'], ['c', 'ⲝ'], ['o', 'ⲟ'], ['p', 'ⲡ'],
  ['r', 'ⲣ'], ['s', 'ⲥ'], ['t', 'ⲧ'], ['u', 'ⲩ'], ['F', 'ⲫ'], ['X', 'ⲭ'], ['y', 'ⲯ'], ['O', 'ⲱ'],
  ['S', 'ϣ'], ['f', 'ϥ'], ['x', 'ϧ'], ['h', 'ϩ'], ['j', 'ϫ'], ['q', 'ϭ'], ['T', 'ϯ']
];

export const ASCII_TO_COPTIC_MAP = Object.fromEntries(ASCII_COPTIC_PAIRS);

let lastSearchInputState = {
  value: '',
  selectionStart: null,
  selectionEnd: null,
  selectionDirection: 'none',
  hadFocus: false,
  timestamp: 0,
};

const clampSelection = (position, valueLength) => {
  if (!Number.isFinite(position)) return valueLength;
  return Math.max(0, Math.min(valueLength, position));
};

const shouldReuseSelectionState = (value) => {
  const isFresh = Date.now() - lastSearchInputState.timestamp <= SELECTION_STATE_MAX_AGE_MS;
  return isFresh && lastSearchInputState.value === value;
};

const getToggleStyle = (isSelected) => ({
  padding: '4px 8px',
  borderRadius: '4px',
  border: 'none',
  cursor: 'pointer',
  userSelect: 'none',
  fontSize: '13px',
  fontWeight: 'bold',
  backgroundColor: isSelected ? '#add8e6' : '#e0e0e0',
  color: isSelected ? '#000' : '#777',
  transition: 'all 0.2s ease-in-out'
});

export default function SearchNavbar({
  searchInput,
  onSearchInputChange,
  autoFocus = false,
  showAdvanced = false,
  onToggleAdvanced,
  searchType = 'startsWith',
  onSearchTypeChange,
  posFilter = 'any',
  onPosFilterChange,
  availablePos = [],
  dialects,
  onDialectsChange,
  allDialects = [],
  languages,
  onLanguagesChange,
  availableLanguages = DEFAULT_LANGUAGES,
  showAdvancedSettings = true,
}) {
  const inputRef = useRef(null);
  const isRestoringSelectionRef = useRef(true);
  
  const [showAsciiHelp, setShowAsciiHelp] = useState(false);

  const captureInputState = (inputElement) => {
    if (!inputElement) return;
    lastSearchInputState = {
      value: inputElement.value ?? '',
      selectionStart: inputElement.selectionStart,
      selectionEnd: inputElement.selectionEnd,
      selectionDirection: inputElement.selectionDirection || 'none',
      hadFocus: document.activeElement === inputElement,
      timestamp: Date.now(),
    };
  };

  useLayoutEffect(() => {
    if (!inputRef.current) return;

    const inputElement = inputRef.current;
    const value = inputElement.value ?? '';
    const valueLength = value.length;
    const canRestoreSelection = shouldReuseSelectionState(value);
    const shouldFocus = autoFocus || (canRestoreSelection && lastSearchInputState.hadFocus);

    if (shouldFocus) {
      inputElement.focus({ preventScroll: true });
    }

    const applySelection = (start, end, direction) => {
      inputElement.setSelectionRange(start, end, direction);
    };

    if (canRestoreSelection) {
      const nextStart = clampSelection(lastSearchInputState.selectionStart, valueLength);
      const nextEnd = clampSelection(lastSearchInputState.selectionEnd, valueLength);
      applySelection(nextStart, nextEnd, lastSearchInputState.selectionDirection);

      const rafId = window.requestAnimationFrame(() => {
        applySelection(nextStart, nextEnd, lastSearchInputState.selectionDirection);
      });

      isRestoringSelectionRef.current = false;
      return () => window.cancelAnimationFrame(rafId);
    }

    if (autoFocus) {
      applySelection(valueLength, valueLength, 'none');
    }
    isRestoringSelectionRef.current = false;
  }, [autoFocus, searchInput]);

  useEffect(() => {
    isRestoringSelectionRef.current = true;
  }, [searchInput]);

  useEffect(() => {
    return () => {
      captureInputState(inputRef.current);
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (showAsciiHelp) setShowAsciiHelp(false);
        else if (showAdvanced && onToggleAdvanced) onToggleAdvanced();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showAdvanced, showAsciiHelp, onToggleAdvanced]);

  // Handler to open ASCII help and close Advanced Settings
  const handleToggleAsciiHelp = () => {
    if (!showAsciiHelp && showAdvanced && onToggleAdvanced) {
      onToggleAdvanced(); // Close advanced settings if opening help
    }
    setShowAsciiHelp(!showAsciiHelp);
  };

  // Handler to open Advanced Settings and close ASCII help
  const handleToggleAdvancedClick = () => {
    if (!showAdvanced && showAsciiHelp) {
      setShowAsciiHelp(false); // Close help if opening advanced settings
    }
    if (onToggleAdvanced) onToggleAdvanced();
  };

  return (
    <>
    <form className="navbar-form navbar-left cdo-search-form" onSubmit={e => e.preventDefault()} role="search">
      {/* 1. Ensure the form-group fills the available space on mobile */}
      <div className="form-group" style={{ width: '100%' }}>
        
        {/* 2. Constrain the overall group (Input + Buttons) to max 450px on desktop, but 100% on mobile */}
        <div className="input-group cdo-search-group" style={{ width: '100%', maxWidth: '450px' }}>
          <input
            ref={inputRef}
            type="text"
            style={{ 
              fontFamily: 'antinoouRegular', 
              width: '100%' // 3. The input just takes up whatever space the group gives it
            }}
            className="form-control"
            style={{minWidth: '220px'}}
            placeholder="Search (e.g. ⲥⲱⲧⲙ, hear, _sOtm_)"
            value={searchInput}
            onChange={e => {
              captureInputState(e.target);
              onSearchInputChange(e.target.value);
            }}
            onSelect={e => captureInputState(e.target)}
            onKeyUp={e => captureInputState(e.target)}
            onClick={e => captureInputState(e.target)}
            onFocus={e => {
              if (isRestoringSelectionRef.current) return;
              captureInputState(e.target);
            }}
            onBlur={e => captureInputState(e.target)}
            autoFocus={false}
          />
          {showAdvancedSettings && (
            <span className="input-group-btn">
              <button
                type="button"
                className={`btn btn-default ${showAsciiHelp ? 'active' : ''}`}
                onClick={handleToggleAsciiHelp}
                title="ASCII Input Help"
                aria-label="Toggle ASCII Help"
                style={{ height: '34px' }}
              >
                <i className="fa fa-question-circle" aria-hidden="true"></i>
              </button>
              <button
                type="button"
                className="btn btn-default cdo-advanced-toggle"
                onClick={handleToggleAdvancedClick}
                title="Advanced Settings"
                aria-label="Toggle advanced settings"
                style={{ height: '34px' }}
              >
                <i className="fa fa-cog" aria-hidden="true"></i>
                <i className="fa fa-angle-down" aria-hidden="true"></i>
              </button>
            </span>
          )}
        </div>
      </div>
    </form>

      <ul className="nav navbar-nav navbar-right cdo-navbar-right-logos">
        <li>
          <a
            className="cdo-award-link"
            href="http://dhawards.org/dhawards2019/results/"
            target="_blank"
            rel="noreferrer"
          >
            <img
              src={withBasePath('img/CDO_DH_awards_2019.png')}
              className="cdo-award-logo"
              alt="Digital Humanities Awards 2019"
            />
          </a>
        </li>
        <li>
          <a href="http://kellia.uni-goettingen.de/" className="kellia" target="_blank" rel="noreferrer">
            KELLIA
          </a>
        </li>
      </ul>

      {/* Ascii Help Dropdown aligned with the navbar container */}
      {showAsciiHelp && (
        <div
          className="ascii-help-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 1001,
            backgroundColor: '#f8f9fa',
            border: '1px solid #ddd',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            padding: '15px 20px',
            boxShadow: '0 6px 12px rgba(0,0,0,0.175)'
          }}
        >
          <button
            type="button"
            onClick={() => setShowAsciiHelp(false)}
            aria-label="Close ASCII Help"
            title="Close"
            style={{
              position: 'absolute',
              top: '10px',
              right: '15px',
              background: 'transparent',
              border: 'none',
              fontSize: '18px',
              color: '#555',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <i className="fa fa-times" aria-hidden="true"></i>
          </button>
          <h5 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Latin to Coptic Keyboard Mapping</h5>
          <p style={{ fontSize: '12px', color: '#666', marginBottom: '10px' }}>
            If you don't have a Coptic keyboard, you can type Latin characters and enclose them in underscores (e.g. <strong>_sOtm_</strong>)
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table className="table table-bordered table-condensed" style={{ margin: 0, textAlign: 'center', backgroundColor: '#fff' }}>
              <tbody>
                <tr>
                  {ASCII_COPTIC_PAIRS.map(([ascii, coptic], i) => (
                    <td key={`coptic-${i}`} style={{ fontFamily: 'antinoouRegular', fontSize: '1.2em', padding: '4px 8px' }}>
                      {coptic}
                    </td>
                  ))}
                </tr>
                <tr>
                  {ASCII_COPTIC_PAIRS.map(([ascii, coptic], i) => (
                    <td key={`ascii-${i}`} style={{ padding: '4px 8px' }}>
                      <code>{ascii}</code>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Advanced Settings Dropdown */}
      {showAdvancedSettings && showAdvanced && (
        <div
          className="advanced-search-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 1000,
            backgroundColor: '#f8f9fa',
            border: '1px solid #ddd',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            padding: '15px 20px',
            boxShadow: '0 6px 12px rgba(0,0,0,0.175)'
          }}
        >
          <button
            type="button"
            onClick={onToggleAdvanced}
            aria-label="Close advanced settings"
            title="Close"
            style={{
              position: 'absolute',
              top: '10px',
              right: '15px',
              background: 'transparent',
              border: 'none',
              fontSize: '18px',
              color: '#555',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <i className="fa fa-times" aria-hidden="true"></i>
          </button>

          <div style={{ display: 'flex', gap: '40px', marginBottom: '15px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
              <strong>Search Type:</strong>
              {['substring', 'startsWith', 'whole'].map(type => (
                <label key={type} style={{ margin: 0, fontWeight: 'normal', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="searchType"
                    value={type}
                    checked={searchType === type}
                    onChange={e => onSearchTypeChange(e.target.value)}
                    style={{ marginRight: '5px' }}
                  /> {type === 'startsWith' ? 'starts with' : type === 'whole' ? 'whole words' : type === 'substring' ? 'contains' : type}
                </label>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <strong>Part of Speech:</strong>
              <select
                className="form-control input-sm"
                style={{ width: 'auto', display: 'inline-block' }}
                value={posFilter}
                onChange={e => onPosFilterChange(e.target.value)}
              >
                <option value="any">Any</option>
                {availablePos.map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '40px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <strong style={{ marginRight: '5px' }}>Dialects:</strong>
              {allDialects.map(d => (
                <button
                  type="button"
                  key={d}
                  style={getToggleStyle(dialects.has(d))}
                  onClick={() => {
                    const nextDialects = new Set(dialects);
                    dialects.has(d) ? nextDialects.delete(d) : nextDialects.add(d);
                    onDialectsChange(nextDialects);
                  }}
                >
                  {d}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <strong style={{ marginRight: '5px' }}>Def. Languages:</strong>
              {availableLanguages.map(l => (
                <button
                  type="button"
                  key={l}
                  style={getToggleStyle(languages.has(l))}
                  onClick={() => {
                    const nextLangs = new Set(languages);
                    languages.has(l) ? nextLangs.delete(l) : nextLangs.add(l);
                    onLanguagesChange(nextLangs);
                  }}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}