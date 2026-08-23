import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import About from './About.jsx'
import Help from './Help.jsx'
import Entry from './Entry.jsx'
import { APP_BASENAME } from './basePath'
import './bootstrap.min.css' 
import './font-awesome-4.2.0/css/font-awesome.min.css'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename={APP_BASENAME || undefined}>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/about" element={<About />} />
        <Route path="/help" element={<Help />} />
        <Route path="/entry/:id" element={<Entry />} />

        // Routes kept for backward compatibility with old links
        <Route path="/results.py" element={<App />} />
        <Route path="/entry.py" element={<App />} /> 
        <Route path="/results.cgi" element={<App />} />
        <Route path="/entry.cgi" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)