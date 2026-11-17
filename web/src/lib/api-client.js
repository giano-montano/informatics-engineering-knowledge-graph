// The only door of the navigation to the API (C4: apiClient). Every call is
// a relative path: Vite forwards it in development and nginx when deployed.

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }

  get notFound() {
    return this.status === 404;
  }
}

// The graph does not change while a student explores, so a subgraph already
// fetched is reused: the panel and the canvas ask for the same ones.
const cache = new Map();

export function forgetResponses() {
  cache.clear();
}

async function request(path, params, signal) {
  // URLSearchParams encodes the keys of the reference layer, which are IRIs
  // with «#» and «/».
  const url = `${path}?${new URLSearchParams(params)}`;
  let response;
  try {
    response = await fetch(url, { signal, headers: { Accept: 'application/json' } });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, 'No se pudo conectar con el sistema.');
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.status === 404
      ? 'El sistema no tiene ese elemento.'
      : `El sistema respondió con un error (${response.status}).`);
  }
  return response.json();
}

function cached(path, params) {
  const id = `${path}?${new URLSearchParams(params)}`;
  if (!cache.has(id)) {
    const pending = request(path, params).catch((error) => {
      cache.delete(id);
      throw error;
    });
    cache.set(id, pending);
  }
  return cache.get(id);
}

/** The subgraph `{nodes, edges}` of a navigation route about one node. */
export function fetchSubgraph(path, key, extra = {}) {
  return cached(path, { key, ...extra });
}

export function fetchOverview() {
  return cached('/api/overview', {});
}

/** Not cached: it changes with every keystroke, and the caller aborts the previous one. */
export function searchByName(text, signal) {
  return request('/api/search', { q: text }, signal);
}

/**
 * Where a document opens. An uploaded document's locator carries the host it
 * was ingested on (ADR-009, ADR-013); the web application is served next to
 * `/resources`, so it keeps only the path. Any other link stays as it is.
 */
export function documentHref(locator) {
  if (!locator) return null;
  try {
    const url = new URL(locator, window.location.origin);
    if (url.pathname.startsWith('/resources/')) return url.pathname;
  } catch {
    return null;
  }
  return locator;
}
