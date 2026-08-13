import { withBasePath } from './basePath';

let indexDataCache = null;
let indexDataPromise = null;

export const getCachedIndexData = () => indexDataCache;

export const preloadIndexData = async () => {
  if (indexDataCache) return indexDataCache;
  if (indexDataPromise) return indexDataPromise;

  indexDataPromise = fetch(withBasePath('index.json'))
    .then((res) => {
      if (!res.ok) throw new Error(`Failed to load index: ${res.status}`);
      return res.json();
    })
    .then((data) => {
      indexDataCache = data;
      return data;
    })
    .finally(() => {
      indexDataPromise = null;
    });

  return indexDataPromise;
};
