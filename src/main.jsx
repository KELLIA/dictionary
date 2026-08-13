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
        <Route path="/results.py" element={<App />} /> // This route is kept for backward compatibility with old links
        <Route path="/entry.py" element={<App />} /> // This route is kept for backward compatibility with old links
        <Route path="/about" element={<About />} />
        <Route path="/help" element={<Help />} />
        <Route path="/entry/:id" element={<Entry />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)