import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { preloadIndexData } from './indexDataCache';
import { SiteHeader, SiteFooter } from './SiteChrome';
import useSharedSearchNavbarSettings from './useSharedSearchNavbarSettings';
import { withBasePath } from './basePath';

const formatNumber = (value) => new Intl.NumberFormat('en-US').format(value);

export default function About() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState('');
  const { availablePos, navbarSettingsProps } = useSharedSearchNavbarSettings();
  const [stats, setStats] = useState({ entries: null, senses: null, uniqueExampleSentences: null });

  useEffect(() => {
    let active = true;

    fetch(withBasePath('stats.json'))
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!active) return;

        setStats({
          entries: data.entries,
          senses: data.senses,
          uniqueExampleSentences: data.uniqueExampleSentences,
        });
      })
      .catch((error) => {
        console.error('Failed to load dictionary stats:', error);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="container">
      <SiteHeader
        activePage="about"
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
                <p>
                  The <em>Coptic Dictionary Online</em> aims to make it easy to look up Coptic words in all dialects
                  and supply freely accessible translations in English, French and German, via human and machine readable interfaces.
                  To learn more about using this dictionary, check out our quick <Link to="/help">how-to guide</Link>.
                </p>

                <div className="row" style={{ marginTop: '20px', marginBottom: '20px' }}>
                  <div className="col-sm-4">
                    <div style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid #ddd', borderRadius: '6px', padding: '14px' }}>
                      <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{stats.entries == null ? '...' : formatNumber(stats.entries)}</div>
                      <div className="text-muted">dictionary entries</div>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid #ddd', borderRadius: '6px', padding: '14px' }}>
                      <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{stats.senses == null ? '...' : formatNumber(stats.senses)}</div>
                      <div className="text-muted">recorded senses</div>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid #ddd', borderRadius: '6px', padding: '14px' }}>
                      <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{stats.uniqueExampleSentences == null ? '...' : formatNumber(stats.uniqueExampleSentences)}</div>
                      <div className="text-muted">unique example sentences</div>
                    </div>
                  </div>
                </div>

                <h3>Lexicon preparation</h3>
                <p>
                  The new <em>Comprehensive Coptic Lexicon</em> is a combination of two parts: the <em><strong>BBAW Lexicon of Coptic Egyptian</strong></em> of the project <em>Strukturen und Transformationen des Wortschatzes der ägyptischen Sprache</em> at the Berlin-Brandenburgische Akademie der Wissenschaften, Berlin, Germany, which includes etymologically Egyptian lexemes of Coptic, and the <em><strong>DDGLC Lexicon of Greek Loanwords in Coptic</strong></em> of the project <em>Database and Dictionary of Greek Loanwords in Coptic</em> at the Ägyptologisches Seminar, Freie Universität Berlin, Germany. Both projects are led by Prof. Tonio Sebastian Richter. The following people mainly contributed to compiling the lexical data:
                </p>
                <ul>
                  <li>Dylan M. Burns (DDGLC)</li>
                  <li>Frank Feder (BBAW, AdWG)</li>
                  <li>Katrin John (DDGLC)</li>
                  <li>Maxim Kupreyev (BBAW)</li>
                </ul>
                <p>moreover</p>
                <ul>
                  <li>Mathew Almond, Sina Becker, Marc Brose, Sonja Dahlgren, Julien Delhez, Anne Grons, Joost Hagen, Jakob Höper, Mariana Jung, Elisabeth Koch, Lena Krastel, Frederic Krueger, Peter Missael, Jan Moje, Franziska Naether, Simon D. Schweitzer, Anne Sörgel, Nina Speranskaja, Gunnar Sperveslage, Vincent Walter, Daniel A. Werning and Alberto Winterberg.</li>
                </ul>
                <p>Each lexicon entry has a stable <em>Thesaurus Linguae Aegyptiae</em> (TLA) ID number.</p>
                <p>
                  TEI XML compliant data files of the lexica are published under a{' '}
                  <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>{' '}
                  license at DOI{' '}
                  <a href="https://doi.org/10.17169/refubium-27566" target="_blank" rel="noreferrer">10.17169/refubium-27566</a>.
                </p>

                <h3>Search interface</h3>
                <p>
                  The search interface is operated and maintained by Georgetown University. It was originally developed as part of the project KELLIA by:
                </p>
                <ul>
                  <li>Emma Manning</li>
                  <li>Amir Zeldes</li>
                </ul>
                <p>
                  Links for Greek words are provided pointing to the{' '}
                  <a href="https://www.perseus.tufts.edu/" target="_blank" rel="noreferrer">Perseus</a>{' '}
                  Greek lexicon and to{' '}
                  <a href="https://logeion.uchicago.edu/" target="_blank" rel="noreferrer">Logeion</a>.
                  Ancient Egyptian etymologies were aligned to Coptic TLA entries by TLA / Simon D. Schweitzer.
                </p>

                <h3>Projects</h3>
                <ul>
                  <li><a href="http://www.copticscriptorium.org/" target="_blank" rel="noreferrer"><em>Coptic Scriptorium</em></a>, Georgetown University, University of the Pacific.</li>
                  <li><a href="http://coptot.manuscriptroom.com/" target="_blank" rel="noreferrer"><em>CoptOT</em></a><em> - Digital Edition of the Coptic Old Testament</em>, Akademie der Wissenschaften zu Göttingen (<strong>AdWG</strong>), Germany.</li>
                  <li><a href="https://www.geschkult.fu-berlin.de/en/e/ddglc" target="_blank" rel="noreferrer"><em>Database and Dictionary of Greek Loanwords in Coptic</em></a> (<strong>DDGLC</strong>), Freie Universität Berlin, Germany.</li>
                  <li><a href="http://kellia.uni-goettingen.de/" target="_blank" rel="noreferrer"><em>Koptische/Coptic Electronic Language and Literature International Alliance</em></a> (<strong>KELLIA</strong>), partners: BBAW, Georgetown University, University of Göttingen, University of Münster, University of the Pacific.</li>
                  <li><a href="https://thesaurus-linguae-aegyptiae.de" target="_blank" rel="noreferrer"><em>Thesaurus Linguae Aegyptiae</em></a> (TLA), <a href="http://aaew.bbaw.de/" target="_blank" rel="noreferrer">Strukturen und Transformationen des Wortschatzes der ägyptischen Sprache</a>, Berlin-Brandenburgische Akademie der Wissenschaften (<strong>BBAW</strong>), Berlin, Germany.</li>
                </ul>

                <h3>Funding</h3>
                <ul>
                  <li><a href="https://www.akademienunion.de/forschung/akademieforschung/" target="_blank" rel="noreferrer">Akademienprogramm der Union der deutschen Akademien der Wissenschaften</a></li>
                  <li><a href="http://www.dfg.de/" target="_blank" rel="noreferrer">Deutsche Forschungsgemeinschaft (DFG)</a></li>
                  <li><a href="http://www.neh.gov/" target="_blank" rel="noreferrer">The National Endowment for the Humanities (NEH)</a></li>
                </ul>

                <h3>Reporting issues / contributing</h3>
                <p>
                  For issues regarding dictionary content or the interface, please use our{' '}
                  <a href="https://github.com/KELLIA/dictionary/issues/new/choose" target="_blank" rel="noreferrer">Issue Tracker</a>{' '}
                  and choose the appropriate template to report your issue.
                </p>

                <h3>How to cite this page</h3>
                <p>As an academic citation describing the dictionary as a whole, please cite the following paper:</p>
                <blockquote>
                  Frank Feder, Maxim Kupreyev, Emma Manning, Caroline T. Schroeder, and Amir Zeldes (2018).{' '}
                  <a href="https://aclanthology.org/W18-4502/" target="_blank" rel="noreferrer">A Linked Coptic Dictionary Online</a>. In <i>Proceedings of the Second Joint SIGHUM Workshop on Computational Linguistics for Cultural Heritage, Social Sciences, Humanities and Literature</i>. Santa Fe, New Mexico, 12&ndash;21.
                </blockquote>
                <p>To cite the CDO interface when using dictionary entries, use the following format:</p>
                <blockquote>
                  <i>Coptic Dictionary Online</i>, ed. by the Koptische/Coptic Electronic Language and Literature International Alliance (KELLIA), https://coptic-dictionary.org/ (accessed yyyy-mm-dd).
                </blockquote>
              </div>
            </div>
          </div>
        </div>
      </div>

      <SiteFooter />
    </div>
  );
}