import React from 'react';
import { Link } from 'react-router-dom';
import SearchNavbar from './SearchNavbar';
import { withBasePath } from './basePath';

const NAV_ITEMS = [
  { id: 'home', to: '/', icon: 'home', label: 'Home' },
  { id: 'help', to: '/help', icon: 'question-circle', label: 'How to' },
  { id: 'about', to: '/about', icon: 'info-circle', label: 'About' },
];

export function SiteHeader({ activePage, searchNavbarProps, sectionStyle }) {
  return (
    <div className="bs-docs-section clearfix" style={sectionStyle}>
      <div className="row">
        <div className="col-lg-12">
          
          <div className="page-header page-main-header" style={{ marginBottom: '0', padding: '5px 0' }}>
            <div className="container-fluid">
              <h1 id="navbar" style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr auto 1fr', 
                alignItems: 'center',
                margin: 0 // Resetting margin to let page-header handle the spacing
              }}>
                <span style={{ textAlign: 'left' }}>
                  Coptic Dictionary Online
                </span>
                
                <span style={{ textAlign: 'center', fontSize: '1.5em', fontFamily: 'antinoouRegular, serif' }}>
                  ⳾
                </span>
                
                <span style={{ textAlign: 'right', fontFamily: 'antinoouRegular, serif' }}>
                  Ⲗⲉⲝⲓⲕⲟⲛ &nbsp;&nbsp;ⲛϢⲛⲉ
                </span>
              </h1>
            </div>
          </div>

          <div className="bs-component" style={{ position: 'relative' }}>
            <nav className="navbar navbar-inverse" style={{ marginBottom: '0' }}>
              <div className="container-fluid">
                <ul className="nav navbar-nav">
                  {NAV_ITEMS.map((item) => (
                    <li key={item.id} id={item.id} className={activePage === item.id ? 'active' : undefined}>
                      <Link to={item.to}><i className={`fa fa-${item.icon}`}></i> {item.label}</Link>
                    </li>
                  ))}
                </ul>
                {searchNavbarProps ? <SearchNavbar {...searchNavbarProps} /> : null}
              </div>
            </nav>
          </div>
          
        </div>
      </div>
    </div>
  );
}
export function SiteFooter() {
  return (
    <footer className="footer" style={{ 
      marginTop: '50px', 
      padding: '20px 0', 
      borderTop: '1px solid #eee',
      height: 'auto', // Overrides the fixed height from Bootstrap's stylesheet
      minHeight: '150px' // Ensures it still has some body even if empty
    }}>
      <div className="container" style={{ textAlign: 'center', width: '100%' }}>
        <div className="row" style={{ textAlign: 'center' }}>
          <div id="inc" style={{ padding: '0 15px' }}>
            <div className="ftext">Lexicon data released under the <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a> license. Search interface code is released under the <a href="https://www.apache.org/licenses/LICENSE-2.0">Apache 2.0</a> license. </div>
            <div className="ftext">CSS based on <a href="http://getbootstrap.com" rel="nofollow" target="_blank" rel="noreferrer">Bootstrap</a>. Icons from <a href="http://fortawesome.github.io/Font-Awesome/" rel="nofollow" target="_blank" rel="noreferrer">Font Awesome</a>. </div>
            <div className="ftext">Web fonts from <a href="http://www.google.com/webfonts" rel="nofollow" target="_blank" rel="noreferrer">Google</a>. Theme adapted from <a href="http://thomaspark.co" rel="nofollow" target="_blank" rel="noreferrer">Thomas Park</a> under the <a href="https://github.com/thomaspark/bootswatch/blob/master/LICENSE" target="_blank" rel="noreferrer">MIT License</a>.</div>
          </div>
        </div>

        <div className="logos" style={{ 
          marginTop: '30px', 
          display: 'flex', 
          flexWrap: 'wrap', 
          justifyContent: 'center', 
          alignItems: 'center', 
          gap: '20px' 
        }}>
          <a href="https://adw-goe.de/" target="_blank" rel="noreferrer"><img src={withBasePath('img/awg.png')} height="75" alt="ADW Goettingen" /></a>
          <a href="http://www.bbaw.de/" target="_blank" rel="noreferrer"><img src={withBasePath('img/bbaw.gif')} height="75" alt="BBAW" /></a>
          <!--<a href="https://www.geschkult.fu-berlin.de/en/e/ddglc" target="_blank" rel="noreferrer"><img src={withBasePath('img/ddglc.png')} height="75" alt="DDGLC" /></a>-->
          <a href="http://www.fu-berlin.de/" target="_blank" rel="noreferrer"><img src={withBasePath('img/fu.png')} height="75" alt="FU Berlin" /></a>
          <a href="http://www.georgetown.edu/" target="_blank" rel="noreferrer"><img src={withBasePath('img/gu.gif')} height="75" alt="Georgetown" /></a>
          <a href="http://www.uni-goettingen.de/" target="_blank" rel="noreferrer"><img src={withBasePath('img/ug.png')} width="80" alt="Uni Goettingen" /></a>
          <a href="http://www.pacific.edu/" target="_blank" rel="noreferrer"><img src={withBasePath('img/pacific.png')} width="75" alt="Pacific" /></a>
          
          <a href="http://www.dfg.de/" target="_blank" rel="noreferrer"><img src={withBasePath('img/dfg.png')} width="100" alt="DFG" /></a>
          <a href="http://www.neh.gov/" target="_blank" rel="noreferrer"><img src={withBasePath('img/neh.png')} width="100" alt="NEH" /></a>
        </div>
      </div>
    </footer>
  );
}