// The state of the exploration (C4: explorationState): the single source of
// the focus, the lens, the «ver por», the expansions and the trail, shared by
// the canvas, the header, the panel and the stops line, and mirrored in the
// URL (ADR-016, ADR-017). On a change of focus or lens it asks for the
// subgraph and decides the layout.

import { fetchSubgraph, forgetResponses } from './api-client.js';
import { edgeId, justifyStop, nodeByKey } from './graph-reading.js';
import {
  layoutContents, layoutCourses, layoutKinds, layoutLocation, layoutNeighborhood, layoutOverview, layoutPath,
  layoutPrerequisites, layoutResources, withSources,
} from './layouts.js';
import {
  GRAINS, LENSES, classArticle, grainFromSlug, lensApplies, lensFromSlug,
} from './vocabulary.js';

const TRAIL_LENGTH = 9;
const PRODUCT = 'InfoKnows';

class Exploration {
  // 'explore' is the student's navigation; 'operator', the operator panel.
  view = $state('explore');

  focusKey = $state(null);
  focusNode = $state.raw(null);
  // Responses are kept raw: D3 and the layouts read them as plain objects.
  detail = $state.raw(null);
  lens = $state('neighborhood');
  grain = $state('course');
  response = $state.raw(null);
  overview = $state.raw(null);
  expansions = $state.raw(new Map());

  // 'loading' while a subgraph is on its way; the last scene stays on screen.
  status = $state('loading');
  error = $state.raw(null);
  notice = $state.raw(null);

  trail = $state.raw([]);
  selectedRelation = $state.raw(null);
  whyStop = $state(null);
  showSources = $state(false);
  steps = $state(0);

  #turn = 0;
  #noticeTimer = null;

  scene = $derived.by(() => {
    if (!this.focusKey) return this.overview ? layoutOverview(this.overview) : null;
    if (!this.detail) return null;
    let scene = null;
    if (this.lens === 'neighborhood') scene = layoutNeighborhood(this.detail, this.focusKey, this.expansions);
    else if (!this.response) return null;
    else if (this.lens === 'prerequisites') scene = layoutPrerequisites(this.response, this.focusKey, this.detail);
    else if (this.lens === 'path') scene = layoutPath(this.response, this.focusKey, this.grain);
    else if (this.lens === 'courses') scene = layoutCourses(this.response, this.focusKey);
    else if (this.lens === 'location') scene = layoutLocation(this.response, this.focusKey);
    else if (this.lens === 'contents') scene = layoutContents(this.response, this.focusKey);
    else if (this.lens === 'resources') scene = layoutResources(this.response, this.focusKey);
    else if (this.lens === 'kinds') scene = layoutKinds(this.response, this.focusKey);
    if (scene && this.showSources) withSources(scene, [this.response, this.detail, ...this.expansions.values()]);
    return scene;
  });

  /** The edge the map marks: the selected relationship, or the last step of an open «¿Por qué?». */
  markedEdge = $derived.by(() => {
    if (this.selectedRelation) return this.selectedRelation.id;
    if (this.whyStop && this.response) {
      const steps = justifyStop(this.response, this.whyStop, this.focusKey);
      return steps.length ? edgeId(steps.at(-1)) : null;
    }
    return null;
  });

  canGoBack = $derived(this.steps > 0);

  // --- URL ----------------------------------------------------------------------

  start() {
    window.addEventListener('popstate', () => this.#applyLocation());
    this.#applyLocation();
  }

  #applyLocation() {
    const params = new URLSearchParams(window.location.search);
    this.steps = window.history.state?.steps ?? 0;
    if (params.get('panel') === 'operador') {
      this.view = 'operator';
      document.title = `Panel del operador · ${PRODUCT}`;
      return;
    }
    if (this.view === 'operator') forgetResponses();
    this.view = 'explore';
    const key = params.get('key');
    if (!key) return this.#showHome();
    return this.#load(key, {
      lens: lensFromSlug(params.get('lente')) ?? 'neighborhood',
      grain: grainFromSlug(params.get('ver')) ?? this.grain,
    });
  }

  #write(push) {
    const params = new URLSearchParams();
    if (this.view === 'operator') params.set('panel', 'operador');
    else if (this.focusKey) {
      params.set('key', this.focusKey);
      if (this.lens !== 'neighborhood') params.set('lente', LENSES[this.lens].slug);
      if (this.lens === 'path') params.set('ver', GRAINS[this.grain].slug);
    }
    const query = params.toString();
    const url = query ? `?${query}` : window.location.pathname;
    if (push) {
      this.steps += 1;
      window.history.pushState({ steps: this.steps }, '', url);
    } else {
      window.history.replaceState({ steps: this.steps }, '', url);
    }
  }

  // --- Notices --------------------------------------------------------------------

  notify(text) {
    clearTimeout(this.#noticeTimer);
    this.notice = { text, id: Date.now() };
    this.#noticeTimer = setTimeout(() => {
      this.notice = null;
    }, 7000);
  }

  dismissNotice() {
    clearTimeout(this.#noticeTimer);
    this.notice = null;
  }

  // --- Start ----------------------------------------------------------------------

  goHome() {
    if (this.view === 'operator') forgetResponses();
    this.view = 'explore';
    this.#showHome();
    this.#write(true);
  }

  // The start screen asks for the areas and the courses itself (C4: home).
  #showHome() {
    this.#turn += 1;
    this.error = null;
    this.#clearFocus();
    this.status = this.overview ? 'ready' : 'loading';
    document.title = `${PRODUCT} · Mapa de conocimientos de Ingeniería Informática`;
  }

  #clearFocus() {
    this.focusKey = null;
    this.focusNode = null;
    this.detail = null;
    this.response = null;
    this.lens = 'neighborhood';
    this.expansions = new Map();
    this.selectedRelation = null;
    this.whyStop = null;
  }

  // --- Focus, lens and expansion ----------------------------------------------------

  /** Puts an element in focus. The lens stays if it applies to the new element. */
  async focus(key, options = {}) {
    if (key === this.focusKey && this.view === 'explore') {
      if (options.lens) await this.setLens(options.lens, options.grain ?? this.grain);
      return;
    }
    this.view = 'explore';
    const done = await this.#load(key, { lens: options.lens ?? this.lens, grain: options.grain ?? this.grain });
    if (done) this.#write(true);
  }

  async #load(key, wanted) {
    const turn = ++this.#turn;
    this.status = 'loading';
    this.error = null;
    try {
      const detail = await fetchSubgraph('/api/nodes', key);
      const node = nodeByKey(detail, key);
      let lens = wanted.lens;
      let dropped = null;
      if (!lensApplies(lens, node)) {
        if (lens !== 'neighborhood') dropped = lens;
        lens = 'neighborhood';
      }
      const response = await this.#fetchLens(lens, key, wanted.grain);
      if (turn !== this.#turn) return false;
      this.focusKey = key;
      this.focusNode = node;
      this.detail = detail;
      this.lens = lens;
      this.grain = wanted.grain;
      this.response = response;
      this.expansions = new Map();
      this.selectedRelation = null;
      this.whyStop = null;
      this.status = 'ready';
      this.trail = [...this.trail.filter((visited) => visited.key !== key),
        { key, name_es: node.name_es, label: node.label, layer: node.layer }].slice(-TRAIL_LENGTH);
      document.title = `${node.name_es} · ${PRODUCT}`;
      if (dropped) this.notify(`«${LENSES[dropped].name}» no aplica a ${classArticle(node)}: ves lo que lo rodea.`);
      return true;
    } catch (error) {
      if (turn !== this.#turn) return false;
      this.status = 'error';
      this.error = {
        message: error.notFound ? 'Ese elemento ya no está en el grafo.' : error.message,
        retry: error.notFound ? null : () => this.#load(key, wanted),
      };
      return false;
    }
  }

  #fetchLens(lens, key, grain) {
    if (lens === 'neighborhood') return null;
    return fetchSubgraph(LENSES[lens].path, key, lens === 'path' ? { grain } : {});
  }

  async setLens(lens, grain = this.grain) {
    if (!this.focusKey || !lensApplies(lens, this.focusNode)) return;
    if (lens === this.lens && grain === this.grain) return;
    const turn = ++this.#turn;
    this.status = 'loading';
    this.error = null;
    try {
      const response = await this.#fetchLens(lens, this.focusKey, grain);
      if (turn !== this.#turn) return;
      this.lens = lens;
      this.grain = grain;
      this.response = response;
      this.selectedRelation = null;
      this.whyStop = null;
      this.status = 'ready';
      this.#write(false);
    } catch (error) {
      if (turn !== this.#turn) return;
      this.status = 'error';
      this.error = { message: error.message, retry: () => this.setLens(lens, grain) };
    }
  }

  setGrain(grain) {
    return this.setLens('path', grain);
  }

  /** Brings the connections of a neighbor without moving the focus. */
  async expand(key) {
    if (this.expansions.has(key)) return;
    try {
      const response = await fetchSubgraph('/api/nodes', key);
      const expansions = new Map(this.expansions);
      expansions.set(key, response);
      this.expansions = expansions;
      if (this.lens !== 'neighborhood') await this.setLens('neighborhood');
      const name = nodeByKey(response, key)?.name_es ?? '';
      this.notify(`Se trajeron las conexiones de «${name}»: están abajo, con su nombre. Sigues en el mismo lugar.`);
    } catch (error) {
      this.notify(`No se pudieron traer esas conexiones. ${error.message}`);
    }
  }

  clearExpansions() {
    this.expansions = new Map();
  }

  back() {
    if (this.canGoBack) window.history.back();
  }

  // --- Provenance -------------------------------------------------------------------

  /** Fixes a relationship in the panel, with the document that states it. */
  selectRelation(relation) {
    this.whyStop = null;
    this.selectedRelation = relation;
  }

  clearRelation() {
    this.selectedRelation = null;
  }

  toggleWhy(key) {
    this.selectedRelation = null;
    this.whyStop = this.whyStop === key ? null : key;
  }

  toggleSources() {
    this.showSources = !this.showSources;
  }

  // --- Operator panel ---------------------------------------------------------------

  openOperator() {
    this.view = 'operator';
    document.title = `Panel del operador · ${PRODUCT}`;
    this.#write(true);
  }
}

export const exploration = new Exploration();

/** A relationship as the panel shows it: the edge, its two ends and its document. */
export function relationOf(edge, source, target, document) {
  return { id: edgeId(edge), edge, source, target, document };
}
