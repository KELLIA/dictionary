import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { preloadIndexData } from './indexDataCache';
import NetworkGraph from './NetworkGraph';
import { loadSearchSettings, saveSearchSettings } from './searchSettingsStorage';
import { SiteHeader, SiteFooter } from './SiteChrome';
import useSharedSearchNavbarSettings from './useSharedSearchNavbarSettings';
import { withBasePath } from './basePath';

export const SearchExampleLink = ({ children, query, navigate, searchType = null }) => {
  const queryPath = `/?q=${encodeURIComponent(query)}`;
  const href = withBasePath(`?q=${encodeURIComponent(query)}`);

  const handleClick = (event) => {
    event.preventDefault();
    if (searchType) {
      const currentSettings = loadSearchSettings();
      saveSearchSettings({
        ...currentSettings,
        searchType,
      });
    }
    navigate(queryPath);
  };

  return <a href={href} onClick={handleClick}><span style={{ fontFamily: 'antinoouRegular, serif' }}>{children}</span></a>;
}

export default function Help() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState('');
  const [networkExample, setNetworkExample] = useState(null);
  const [networkLemma, setNetworkLemma] = useState('');
  const [networkFormId, setNetworkFormId] = useState('');
  const { availablePos, navbarSettingsProps } = useSharedSearchNavbarSettings();

  useEffect(() => {
    let isMounted = true;

    fetch(withBasePath('details/C951.json'))
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load help graph example: ${response.status}`);
        }
        return response.json();
      })
      .then((entry) => {
        if (!isMounted) return;
        const sahidicNetwork = entry.network?.S || entry.network?.[Object.keys(entry.network || {})[0]] || null;
        const targetForm = entry.forms?.find((form) => form.id === 'CF3246')
          || entry.forms?.find((form) => form.dialect === 'S')
          || entry.forms?.[0];
        setNetworkExample(sahidicNetwork);
        setNetworkLemma(targetForm?.orth || 'ⲉⲓⲣⲉ');
        setNetworkFormId(targetForm?.id || '');
      })
      .catch((error) => {
        console.error(error);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="container">
      <SiteHeader
        activePage="help"
        searchNavbarProps={{
          searchInput,
          onSearchInputChange: (nextValue) => {
            setSearchInput(nextValue);
            const trimmedValue = nextValue.trim();
            if (trimmedValue) {
              preloadIndexData().catch(() => {});
              navigate(`/?q=${encodeURIComponent(trimmedValue)}`, { replace: true });
            }
          },
          availablePos,
          ...navbarSettingsProps,
        }}
      />

      <div className="bs-docs-section clearfix">
        <div className="row">
          <div className="col-lg-12">
            <div className="bs-component">
              <div className="content">
                <h2>How to search</h2>

                <h3>Search bar</h3>
                <p>
                  From the dictionary&apos;s search bar you can run a configurable search for any of the following fields:
                </p>
                <ul>
                  <li>
                    <b>Coptic word</b> - enter Coptic text in utf-8 characters. You can also use regular expression wildcards:
                    <ul>
                      <li>Words starting in some prefix: <SearchExampleLink query="ⲙⲛⲧ.*" navigate={navigate} searchType="substring">ⲙⲛⲧ.*</SearchExampleLink></li>
                      <li>Words ending in some suffix: <SearchExampleLink query=".*ϩⲏⲧ" navigate={navigate} searchType="substring">.*ϩⲏⲧ</SearchExampleLink></li>
                      <li>Wildcard in middle: <SearchExampleLink query="ⲥ.ⲧⲙ" navigate={navigate} searchType="substring">ⲥ.ⲧⲙ</SearchExampleLink></li>
                      <li>Optional character: <SearchExampleLink query="ⲥⲱⲧⲉ?ⲙ" navigate={navigate} searchType="substring">ⲥⲱⲧⲉ?ⲙ</SearchExampleLink></li>
                      <li>For complete documentation on regular expressions see: <a href="http://www.regular-expressions.info/" target="_blank" rel="noreferrer">http://www.regular-expressions.info/</a></li>
                    </ul>
                  </li>
                  <li><b>Search in definitions</b> - you can search within definitions in either English, French or German, or in any language</li>
                  <li><b>Search using Latin characters</b> - 
                    <ul>
                      <li>If you don't have a Coptic keyboard, you can use Latin characters surrounded by underscores like this: <SearchExampleLink query="_sOtm_" navigate={navigate}>_sOtm_</SearchExampleLink></li>
                      <li>See the icon <i className="fa fa-question-circle"></i> in the search bar for the full mapping</li>
                    </ul>
                  </li>
                  <li>
                    <b>Lemma IDs and form IDs</b> - you can search directly by stable IDs:
                    <ul>
                        <li>
                            <SearchExampleLink query="C225" navigate={navigate}>C225</SearchExampleLink> - lemma ID for the entry ⲁⲥⲡⲉ "language"
                        </li>
                        <li>    
                            <SearchExampleLink query="CF903" navigate={navigate}>CF903</SearchExampleLink> - specific form ID for the Bohairic form of the same lemma, ⲁⲥⲡⲓ
                        </li>
                    </ul>
                  </li>
                </ul>
                <p>
                    Typing in the search box will immediately update the search results. To see a detailed entry, click on one of the search results, or narrow down
                    the search until a unique entry has been identified.
                </p>

                <h3>Advanced settings</h3>
                <p>
                  Clicking on the cog icon next to the search bar opens the advanced settings. Here you can:
                </p>
                <ul>
                  <li>Choose to search for words <b>starting</b> with some letters, <b>containing</b> some letters, or <b>exact word</b> match</li>
                  <li>Enable or disable languages for search in definitions (by default English/French/German are all enabled)</li>
                  <li>Turn on/off <b>dialect</b> labels to search in (all on by default)</li>
                  <li>Use <b>Scriptorium tags</b> to limit search by part of speech (N, V etc.), see the inventory described <a href="https://github.com/CopticScriptorium/tagger-part-of-speech/blob/master/scriptorium_tagset_documentation.pdf" target="_blank" rel="noreferrer">here</a></li>
                </ul>

                <h3>Frequencies and collocations</h3>
                <p>
                  The Coptic Dictionary Online is linked to <a href="http://copticscriptorium.org" target="_blank" rel="noreferrer">Coptic Scriptorium</a> corpora. Users can search for attestations of words, get frequencies and rank information or browse collocations of words using the following icons on each entry&apos;s page:
                </p>
                <ul>
                  <li><img src={withBasePath('img/scriptorium.png')} className="scriptorium_logo" title="Search in Coptic Scriptorium" alt="Coptic Scriptorium" /> - click on this icon next to a word form to search for it in Coptic Scriptorium corpora (you will be taken to ANNIS, the project&apos;s search interface)</li>
                  <li><i className="fa fa-sort-numeric-asc freq_icon" aria-hidden="true"></i> - pass over this icon to show frequencies and ranks for each word. For example, you can compare which is more frequent and how much: <Link to="/entry/C615">ⲉ</Link> or <Link to="/entry/C2349">ⲛ</Link>?</li>
                  <li>
                    <b className="fa-stack freq-icon" style={{ position: 'relative', left: '-5px' }}>
                      <i className="fa fa-share-alt fa-stack-1x fa-rotate-315" style={{top:'-10px'}}></i>
                      <i className="fa fa-share-alt fa-stack-1x fa-rotate-45" style={{top:'10px'}}></i>
                    </b>
                    <span style={{ left: '-9px', position: 'relative' }}>- if available, this icon shows collocations, words that co-occur with this word form much more often than expected by chance</span>
                  </li>
                </ul>

                <p><b>Note:</b> frequencies in the dictionary are cached and updated periodically. Numbers in ANNIS searches may differ slightly in some cases due to updates and/or slight differences in handling duplicate texts.</p>

                <h3>Sorting</h3>
                <p>
                    You can sort search results in several ways:
                </p>
                <ul>
                    <li><b>Relevance</b> - show exact matches first (prioritized by Coptic match, then definition match), the partial matches, sorted internally by the lemma's corpus frequency, then alphabetically</li>
                    <li><b>Frequency</b> - sort only by lemma frequency (more frequently attested lemmas first)</li>
                    <li><b>Alphabetically</b> - order the matches alphabetically based on Coptic letter order</li>
                </ul>

                <h3>Phrase network graph</h3>
                <p>For entries with sufficient attestations in our corpora, you may see a phrase network graph thumbnail displayed as follows:</p>
                <div style={{ marginBottom: '15px' }}>
                  {networkExample ? (
                    <span style={{ display: 'inline-block', maxWidth: '100px' }}>
                      <NetworkGraph networkData={networkExample} targetLemma={networkLemma} targetFormId={networkFormId} width="100px" height="100px" />
                    </span>
                  ) : (
                    <img src={withBasePath('img/phrase_network.png')} width="100" style={{ border: '1px solid' }} alt="Phrase network thumbnail" />
                  )}
                </div>
                <p>Clicking on this will take you to a phrase network graph like the one below, showing typical sequences of words involving this entry. The network shows a diagram of up to 20 most common phrases headed by the head word, truncated to 8 words at most for readability. Nodes and transitions are sized proportionally to how often they are attested in Coptic Scriptorium data. Correspondences between nodes in different phrases are computed using dependency parses based on the <a href="https://copticscriptorium.org/treebank.html" target="_blank" rel="noreferrer">Coptic Universal Dependency Treebank</a>.</p>

                <div style={{ maxWidth: '900px', width: '100%', marginBottom: '10px' }}>
                  {networkExample ? (
                    <NetworkGraph networkData={networkExample} targetLemma={networkLemma} targetFormId={networkFormId} width="100%" height="420px" />
                  ) : (
                    <img src={withBasePath('img/phrase_network.png')} width="50%" style={{ border: '1px solid' }} alt="Phrase network example" />
                  )}
                </div>

                <p style={{ marginTop: '5px' }}><b>Disclaimer:</b> some errors due to automatic Natural Language Processing may be included in these graphs, which are provided as an assistive tool only.</p>

                <h3>Example usages</h3>
                <p>If available, each entry will also provide some automatically extracted examples of the entry, including examples of inflected forms of the same lemma, as shown below. As with network graphs, this functionality depends on automatic analysis and may occasionally contain errors - we welcome reports on incorrect examples at our <a href="https://github.com/KELLIA/dictionary/issues/new?assignees=&labels=&template=bad-example-usage-report.md&title=Bad+example+sentence+for+the+entry+%3CENTRY%3E" target="_blank" rel="noreferrer">GitHub repository</a>.</p>

                <img src={withBasePath('img/examples.png')} width="50%" style={{ border: '1px solid' }} alt="Entry examples" />

                <p style={{ marginTop: '5px' }}>For each example, you can also see the text from which it is extracted, and click on the URN link to see the entire text for more context.</p>

                <p style={{ marginTop: '20px' }}>
                  For background information about the project, funding, and citation format, see the <Link to="/about">About page</Link>.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <SiteFooter />
    </div>
  );
}