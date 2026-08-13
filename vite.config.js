import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs';
import path from 'node:path';

const normalizeBasePath = (value) => {
  const trimmed = (value || '').trim();
  if (!trimmed || trimmed === '/') return '/';
  return `/${trimmed.replace(/^\/+|\/+$/g, '')}/`;
};

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const base = normalizeBasePath(env.CDO_BASE_PATH);

  return {
    base,
    plugins: [
      react(),
      {
        name: 'serve-local-details', // Get entry-specific .json files from middleware to prevent refreshing them on each build in public/details/
        configureServer(server) {
          // Use standard middleware without a mounted route so we can inspect the full URL
          server.middlewares.use((req, res, next) => {
            const urlPath = req.url?.split('?')[0] || '';
            
            // Extract the filename regardless of the dynamic base path
            const detailsMatch = urlPath.match(/\/details\/(.+)$/);
            
            if (detailsMatch) {
              const filename = detailsMatch[1];
              const filePath = path.resolve(__dirname, 'local-data/details', filename);

              if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
                res.setHeader('Content-Type', 'application/json');
                // Ensure CORS doesn't block local fetching
                res.setHeader('Access-Control-Allow-Origin', '*'); 
                
                // Stream the file directly
                fs.createReadStream(filePath).pipe(res);
                return;
              }
            }
            
            // If it's not a /details/ request, or the file doesn't exist, continue normally
            next(); 
          });
        }
      }
    ],
  };
});