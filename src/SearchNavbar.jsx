import { useState, useEffect, useLayoutEffect, useRef } from 'react';
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

// Each key is [unshifted, shifted]. Special keys: Bksp, Shift
const letterRow = (letters) => [...letters].map(l => [l, l.toUpperCase()]);
const KEYBOARD_ROWS = [
  [["`", "~"], ["1", "!"], ["2", "@"], ["3", "#"], ["4", "$"], ["5", "%"], ["6", "^"], ["7", "&"], ["8", "*"], ["9", "("], ["0", ")"], ["Bksp", "Bksp"]],
  letterRow('ϭϣⲉⲣⲧⲩⲑⲓⲟⲡⳉ'),
  letterRow('ⲁⲥⲇϫϥⲅⲏϩⲝⲕⲗ'),
  [["Shift", "Shift"], ...letterRow('ⲍⲭϧⲯⲱⲃⲛⲙⲫϯ')],
];

let lastSearchInputState = {
  value: '',
  selectionStart: null,
  selectionEnd: null,
  selectionDirection: 'none',
  hadFocus: false,
  timestamp: 0,
};

const rememberCaret = (value, caret) => {
  lastSearchInputState = {
    value,
    selectionStart: caret,
    selectionEnd: caret,
    selectionDirection: 'none',
    hadFocus: true,
    timestamp: Date.now(),
  };
};

const clampSelection = (position, valueLength) => {
  if (!Number.isFinite(position)) return valueLength;
  return Math.max(0, Math.min(valueLength, position));
};

const shouldReuseSelectionState = (value) => {
  const isFresh = Date.now() - lastSearchInputState.timestamp <= SELECTION_STATE_MAX_AGE_MS;
  return isFresh && lastSearchInputState.value === value;
};

const DIALECT_NAMES = {
  A: 'Akhmimic',
  Ak: 'Sub-Akhmimic',
  B: 'Bohairic',
  F: 'Fayyumic',
  M: 'Mesokemic',
  L: 'Lycopolitan',
  P: 'Proto-Theban',
  S: 'Sahidic',
  V: 'South Fayyumic Greek',
  W: 'Crypto-Mesokemic Greek',
  '?': 'Unknown'
};

const CheckMark = () => (
  <span aria-hidden="true" style={{
    position: 'absolute', top: '2px', right: '4px',
    fontSize: '9px', lineHeight: 1, color: '#1a5f7a'
  }}>✓</span>
);

// Symmetric horizontal padding keeps the label centered and leaves room for the check mark
const getToggleStyle = (isSelected) => ({
  position: 'relative',
  padding: '4px 12px',
  borderRadius: '4px',
  border: 'none',
  cursor: 'pointer',
  userSelect: 'none',
  fontSize: '12px',
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
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [shifted, setShifted] = useState(false);

  const handleVirtualKey = (key) => {
    const inputElement = inputRef.current;
    const value = searchInput ?? '';
    const start = clampSelection(inputElement?.selectionStart, value.length);
    const end = clampSelection(inputElement?.selectionEnd, value.length);
    let nextValue;
    let caret;
    if (key === 'Bksp') {
      const from = start === end ? Math.max(0, start - 1) : start;
      nextValue = value.slice(0, from) + value.slice(end);
      caret = from;
    } else {
      nextValue = value.slice(0, start) + key + value.slice(end);
      caret = start + key.length;
    }
    rememberCaret(nextValue, caret);
    onSearchInputChange(nextValue);
    if (shifted && key !== 'Bksp') setShifted(false);
  };

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
        if (showKeyboard) setShowKeyboard(false);
        else if (showAsciiHelp) setShowAsciiHelp(false);
        else if (showAdvanced && onToggleAdvanced) onToggleAdvanced();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showAdvanced, showAsciiHelp, showKeyboard, onToggleAdvanced]);

  // Handler to open ASCII help and close Advanced Settings
  const handleToggleAsciiHelp = () => {
    if (!showAsciiHelp) {
      if (showAdvanced && onToggleAdvanced) onToggleAdvanced();
      setShowKeyboard(false);
    }
    setShowAsciiHelp(!showAsciiHelp);
  };

  const handleToggleKeyboard = () => {
    if (!showKeyboard) {
      if (showAdvanced && onToggleAdvanced) onToggleAdvanced();
      setShowAsciiHelp(false);
    }
    setShowKeyboard(!showKeyboard);
  };

  // Handler to open Advanced Settings and close ASCII help
  const handleToggleAdvancedClick = () => {
    if (!showAdvanced) {
      setShowAsciiHelp(false);
      setShowKeyboard(false);
    }
    if (onToggleAdvanced) onToggleAdvanced();
  };

  return (
    <>
    <form className="navbar-form navbar-left cdo-search-form" onSubmit={e => e.preventDefault()} role="search">
      {/* 1. Ensure the form-group fills the available space on mobile */}
      <div className="form-group" style={{ width: '100%', position: 'relative' }}>
        {showAdvancedSettings && showKeyboard && (
          <div
            className="coptic-keyboard-dropdown"
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              width: '100%',
              maxWidth: '450px',
              marginTop: '1px',
              zIndex: 1001,
              backgroundColor: '#f8f9fa',
              border: '1px solid #ddd',
              borderRadius: '0 0 4px 4px',
              padding: '8px',
              boxShadow: '0 6px 12px rgba(0,0,0,0.175)'
            }}
            // Keep focus in the search input while clicking keys
            onMouseDown={e => e.preventDefault()}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {KEYBOARD_ROWS.map((row, r) => (
                <div key={r} style={{ display: 'flex', gap: '3px' }}>
                  {row.map(([base, shift], c) => {
                    const key = shifted ? shift : base;
                    const isShift = key === 'Shift';
                    const isBksp = key === 'Bksp';
                    return (
                      <button
                        type="button"
                        key={c}
                        className={`btn btn-default ${isShift && shifted ? 'active' : ''}`}
                        onClick={() => (isShift ? setShifted(!shifted) : handleVirtualKey(key))}
                        aria-label={isBksp ? 'Backspace' : isShift ? 'Shift' : undefined}
                        style={{
                          fontFamily: 'antinoouRegular',
                          fontSize: '15px',
                          flex: isShift || isBksp ? '1.6 1 0' : '1 1 0',
                          minWidth: 0,
                          padding: '3px 0',
                        }}
                      >
                        {isBksp ? <i className="fa fa-long-arrow-left" aria-hidden="true"></i>
                          : isShift ? <i className="fa fa-arrow-up" aria-hidden="true"></i>
                          : key}
                      </button>
                    );
                  })}
                </div>
              ))}
              <button
                type="button"
                className="btn btn-default"
                aria-label="Space"
                onClick={() => handleVirtualKey(' ')}
                style={{ width: '60%', alignSelf: 'center', padding: '3px 0' }}
              >&nbsp;</button>
            </div>
          </div>
        )}
        
        {/* 2. Constrain the overall group (Input + Buttons) to max 450px on desktop, but 100% on mobile */}
        <div className="input-group cdo-search-group" style={{ width: '100%', maxWidth: '450px' }}>
          <input
            ref={inputRef}
            type="text"
            style={{ 
              fontFamily: 'antinoouRegular', 
              minWidth: '225px',
              width: '100%' // 3. The input just takes up whatever space the group gives it
            }}
            className="form-control"
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
                className={`btn btn-default ${showKeyboard ? 'active' : ''}`}
                onClick={handleToggleKeyboard}
                title="Coptic Virtual Keyboard"
                aria-label="Toggle Coptic virtual keyboard"
                aria-expanded={showKeyboard}
                style={{ height: '34px', paddingLeft: '8px', paddingRight: '8px' }}
              >
                <i className="fa fa-keyboard-o fa-fw" aria-hidden="true"></i>
              </button>
              <button
                type="button"
                className={`btn btn-default ${showAsciiHelp ? 'active' : ''}`}
                onClick={handleToggleAsciiHelp}
                title="ASCII Input Help"
                aria-label="Toggle ASCII Help"
                style={{ height: '34px', paddingLeft: '8px', paddingRight: '8px' }}
              >
                <i className="fa fa-question-circle fa-fw" aria-hidden="true"></i>
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
            If you don't have a Coptic keyboard, you can use the virtual keyboard button above to open the keyboard, or type Latin characters and enclose them in underscores (e.g. <strong>_sOtm_</strong>)
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
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
              <strong style={{ marginRight: '5px' }}>Dialects:</strong>
              {allDialects.map(d => (
                <button
                  type="button"
                  key={d}
                  title={DIALECT_NAMES[d]}
                  style={getToggleStyle(dialects.has(d))}
                  onClick={() => {
                    const nextDialects = new Set(dialects);
                    dialects.has(d) ? nextDialects.delete(d) : nextDialects.add(d);
                    onDialectsChange(nextDialects);
                  }}
                >
                  {dialects.has(d) && <CheckMark />}
                  {d}
                </button>
              ))}
              <button
                type="button"
                title={allDialects.every(d => dialects.has(d)) ? 'Turn all dialects off' : 'Turn all dialects on'}
                style={{
                  ...getToggleStyle(false),
                  backgroundColor: '#fff',
                  color: '#333',
                  border: '1px dashed #777',
                  fontWeight: 'normal',
                  fontSize: '12px',
                  padding: '4px 8px'
                }}
                onClick={() => {
                  const allOn = allDialects.every(d => dialects.has(d));
                  onDialectsChange(allOn ? new Set() : new Set(allDialects));
                }}
              >
                {allDialects.every(d => dialects.has(d)) ? 'None' : 'All'}
              </button>
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
                  {languages.has(l) && <CheckMark />}
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