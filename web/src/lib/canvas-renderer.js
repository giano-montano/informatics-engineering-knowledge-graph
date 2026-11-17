// The canvas (C4: canvas). D3 owns this SVG; Svelte hands over the container
// and never touches what is inside (ADR-017). One force simulation moves the
// nodes towards the positions the active layout fixed (ADR-018), so a change
// of lens reads as the same map rearranging itself.

import * as d3 from 'd3';

import { CLASSES, RELATIONS, accessibleName, classColor, className, layerOf } from './vocabulary.js';

const LINE_HEIGHT = 16;
const CHAR_WIDTH = 7.1;

function hexagon(r) {
  const points = d3.range(6).map((i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    return `${(Math.cos(angle) * r).toFixed(2)},${(Math.sin(angle) * r).toFixed(2)}`;
  });
  return `M${points.join('L')}Z`;
}

function circle(r) {
  return `M${-r},0a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0Z`;
}

/** The outline that tells the layer: hexagon for CS2023, circle for the syllabi (ADR-019). */
function outline(d, r = d.r) {
  return d.node.layer === 'reference' ? hexagon(r * 1.14) : circle(r);
}

const DOCUMENT_GLYPH = 'M-3.6,-5h4.6l2.8,2.8v7.2h-7.4zM1,-5v2.8h2.8';

function labelBox(d) {
  if (!d.label) return { x0: d.tx - d.r, x1: d.tx + d.r, y0: d.ty - d.r, y1: d.ty + d.r };
  const width = Math.max(...d.label.lines.map((line) => line.length), (d.label.sub ?? '').length * 0.86) * CHAR_WIDTH;
  const height = (d.label.lines.length + (d.label.sub ? 1 : 0)) * LINE_HEIGHT;
  const { side } = d.label;
  if (side === 'left') return { x0: d.tx - d.r - 10 - width, x1: d.tx + d.r, y0: d.ty - Math.max(d.r, height / 2), y1: d.ty + Math.max(d.r, height / 2) };
  if (side === 'right') return { x0: d.tx - d.r, x1: d.tx + d.r + 10 + width, y0: d.ty - Math.max(d.r, height / 2), y1: d.ty + Math.max(d.r, height / 2) };
  if (side === 'above') return { x0: d.tx - width / 2, x1: d.tx + width / 2, y0: d.ty - d.r - 8 - height, y1: d.ty + d.r };
  return { x0: d.tx - width / 2, x1: d.tx + width / 2, y0: d.ty - d.r, y1: d.ty + d.r + 10 + height };
}

export function createCanvas(container, handlers) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const svg = d3.select(container).append('svg')
    .attr('class', 'graph')
    .attr('role', 'group')
    .attr('aria-label', 'Mapa del elemento en foco. Cada punto es un botón; la ficha de la derecha lista lo mismo en texto.');
  const defs = svg.append('defs');
  for (const tone of ['main', 'far', 'selected']) {
    defs.append('marker')
      .attr('id', `arrow-${tone}`).attr('class', `arrow arrow-${tone}`)
      .attr('viewBox', '0 0 10 10').attr('refX', 8.5).attr('refY', 5)
      .attr('markerWidth', 7.5).attr('markerHeight', 7.5).attr('orient', 'auto-start-reverse')
      .append('path').attr('d', 'M1,1.5 9,5 1,8.5Z');
  }
  // The glow of what matters now, and one sphere gradient per class: lit from
  // the upper left, in the hue of the class.
  const glow = defs.append('filter').attr('id', 'glow').attr('x', '-80%').attr('y', '-80%').attr('width', '260%').attr('height', '260%');
  glow.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', 4.5).attr('result', 'wide');
  const merged = glow.append('feMerge');
  merged.append('feMergeNode').attr('in', 'wide');
  merged.append('feMergeNode').attr('in', 'SourceGraphic');
  for (const [label, { color }] of Object.entries(CLASSES)) {
    const sphere = defs.append('radialGradient').attr('id', `sphere-${label}`).attr('cx', '35%').attr('cy', '30%').attr('r', '78%');
    sphere.append('stop').attr('offset', '0%').style('stop-color', `color-mix(in oklch, ${color} 35%, white)`);
    sphere.append('stop').attr('offset', '34%').style('stop-color', color);
    sphere.append('stop').attr('offset', '100%').style('stop-color', `color-mix(in oklch, ${color} 62%, black)`);
  }
  const viewport = svg.append('g').attr('class', 'viewport');
  const boxLayer = viewport.append('g').attr('class', 'boxes').attr('aria-hidden', 'true');
  const edgeLayer = viewport.append('g').attr('class', 'edges');
  const captionLayer = viewport.append('g').attr('class', 'captions').attr('aria-hidden', 'true');
  const nodeLayer = viewport.append('g').attr('class', 'nodes');
  const tooltip = d3.select(container).append('div').attr('class', 'graph-tip').attr('role', 'presentation').attr('hidden', true);

  let current = { nodes: [], edges: [], captions: [], boxes: [] };
  let placed = new Map();
  let selectedEdge = null;
  let firstRender = true;

  // --- Zoom -------------------------------------------------------------------

  const zoom = d3.zoom().scaleExtent([0.3, 2.5]).on('zoom', (event) => {
    viewport.attr('transform', event.transform);
    // Keeps the pointer target of an edge at 24 px on screen at any zoom.
    svg.style('--k', event.transform.k);
    handlers.onZoom?.(event.transform.k);
  });
  svg.call(zoom).on('dblclick.zoom', null);

  function fit(duration = 520) {
    const { width, height } = container.getBoundingClientRect();
    if (!current.nodes.length || !width || !height) return;
    const boxes = current.nodes.map(labelBox);
    for (const caption of current.captions) {
      const w = caption.text.length * CHAR_WIDTH;
      const x0 = caption.anchor === 'start' ? caption.x : caption.anchor === 'end' ? caption.x - w : caption.x - w / 2;
      boxes.push({ x0, x1: x0 + w, y0: caption.y - 16, y1: caption.y + 6 });
    }
    for (const box of current.boxes) boxes.push({ x0: box.x, x1: box.x + box.w, y0: box.y, y1: box.y + box.h });
    const x0 = Math.min(...boxes.map((b) => b.x0));
    const x1 = Math.max(...boxes.map((b) => b.x1));
    const y0 = Math.min(...boxes.map((b) => b.y0));
    const y1 = Math.max(...boxes.map((b) => b.y1));
    // The bottom clears the trail, the legend and the controls that sit on the canvas.
    const pad = { x: 40, top: 24, bottom: 112 };
    const k = Math.min(1.15, (width - 2 * pad.x) / Math.max(1, x1 - x0), (height - pad.top - pad.bottom) / Math.max(1, y1 - y0));
    const scale = Math.max(0.3, k);
    const tx = width / 2 - ((x0 + x1) / 2) * scale;
    const ty = pad.top + (height - pad.top - pad.bottom) / 2 - ((y0 + y1) / 2) * scale;
    const target = d3.zoomIdentity.translate(tx, ty).scale(scale);
    (reduced.matches || !duration ? svg : svg.transition().duration(duration).ease(d3.easeCubicOut)).call(zoom.transform, target);
  }

  function zoomBy(factor) {
    (reduced.matches ? svg : svg.transition().duration(200)).call(zoom.scaleBy, factor);
  }

  // --- Geometry of an edge ------------------------------------------------------

  function trimmed(a, b, ra, rb) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const length = Math.hypot(dx, dy) || 1;
    return [a.x + (dx / length) * ra, a.y + (dy / length) * ra, b.x - (dx / length) * rb, b.y - (dy / length) * rb];
  }

  function edgePath(d) {
    const a = placed.get(d.from);
    if (!a) return '';
    const b = d.to ? placed.get(d.to) : { x: d.point.x, y: d.point.y, r: 0 };
    if (!b) return '';
    const ra = a.r + 3;
    const rb = (b.r ?? 0) + (d.arrow ? 5 : 3);
    if (d.curve === 'h' && Math.abs(b.x - a.x) > 30) {
      const sign = Math.sign(b.x - a.x);
      const x1 = a.x + sign * (ra + (sign > 0 ? a.out ?? 0 : 0));
      const x2 = b.x - sign * rb;
      const mid = (x1 + x2) / 2;
      return `M${x1},${a.y}C${mid},${a.y} ${mid},${b.y} ${x2},${b.y}`;
    }
    if (d.curve === 'arc' && Math.abs(b.y - a.y) < 4 && Math.abs(b.x - a.x) > 260) {
      // Jumps over the nodes between two that are not next to each other.
      const lift = Math.min(90, Math.abs(b.x - a.x) * 0.16);
      const sign = Math.sign(b.x - a.x);
      return `M${a.x + sign * ra * 0.8},${a.y - ra * 0.6}Q${(a.x + b.x) / 2},${a.y - lift * 2} ${b.x - sign * rb * 0.8},${b.y - rb * 0.6}`;
    }
    const [x1, y1, x2, y2] = trimmed(a, b, ra, rb);
    return `M${x1},${y1}L${x2},${y2}`;
  }

  // --- Tooltip ------------------------------------------------------------------

  function showTip(html, x, y) {
    const bounds = container.getBoundingClientRect();
    tooltip.attr('hidden', null).html(html);
    const tip = tooltip.node().getBoundingClientRect();
    const left = Math.min(Math.max(8, x - bounds.left + 14), bounds.width - tip.width - 8);
    const top = y - bounds.top + 18 + tip.height > bounds.height ? y - bounds.top - tip.height - 12 : y - bounds.top + 18;
    tooltip.style('left', `${left}px`).style('top', `${Math.max(8, top)}px`);
  }

  function hideTip() {
    tooltip.attr('hidden', true);
  }

  const escape = (text) => String(text ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function nodeTip(d) {
    const code = d.node.course_code ? ` · ${escape(d.node.course_code)}` : '';
    return `<strong>${escape(d.node.name_es)}</strong><span>${escape(className(d.node))}${code} · ${escape(layerOf(d.node).name)}</span>`;
  }

  function edgeTip(d) {
    if (!d.edge) return `<span>${escape(RELATIONS[d.type].out)}: la lista con nombres está en la ficha</span>`;
    const source = placed.get(d.edge.source)?.node;
    const target = placed.get(d.edge.target)?.node;
    const said = d.document
      ? `${d.edge.provenance ? 'Lo dice' : 'Lo define'}: ${escape(d.document.name_es)}`
      : 'Sin fuente registrada';
    return `<strong>${escape(source?.name_es)} ${escape(RELATIONS[d.type].phrase)} ${escape(target?.name_es)}</strong><span>${said} · clic para ver la fuente</span>`;
  }

  // --- Keyboard: arrows move between the points of the map ----------------------

  function nearest(from, direction) {
    let best = null;
    let bestScore = Infinity;
    for (const d of current.nodes) {
      if (d.key === from.key) continue;
      const dx = d.x - from.x;
      const dy = d.y - from.y;
      const along = direction === 'ArrowLeft' ? -dx : direction === 'ArrowRight' ? dx : direction === 'ArrowUp' ? -dy : dy;
      const across = direction === 'ArrowLeft' || direction === 'ArrowRight' ? Math.abs(dy) : Math.abs(dx);
      if (along <= 4) continue;
      const score = along + across * 2.2;
      if (score < bestScore) {
        bestScore = score;
        best = d;
      }
    }
    return best;
  }

  function focusNodeElement(key) {
    const element = nodeLayer.selectAll('g.node').filter((d) => d.key === key).node();
    element?.focus({ preventScroll: true });
  }

  function onNodeKey(event, d) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (d.tone !== 'focus') handlers.onFocus?.(d.key);
    } else if ((event.key === '+' || event.key === '=') && d.expandable) {
      event.preventDefault();
      handlers.onExpand?.(d.key);
    } else if (event.key.startsWith('Arrow')) {
      const next = nearest(d, event.key);
      if (next) {
        event.preventDefault();
        focusNodeElement(next.key);
      }
    }
  }

  // --- Simulation: every node is pulled to the position its layout fixed ---------

  const simulation = d3.forceSimulation([]).alphaDecay(0.1).velocityDecay(0.42).force('target', () => {
    for (const d of current.nodes) {
      d.vx += (d.tx - d.x) * 0.2;
      d.vy += (d.ty - d.y) * 0.2;
    }
  }).on('tick', draw).on('end', () => {
    for (const d of current.nodes) {
      d.x = d.tx;
      d.y = d.ty;
    }
    draw();
  });
  simulation.stop();

  function draw() {
    nodeLayer.selectAll('g.node').attr('transform', (d) => `translate(${d.x.toFixed(1)},${d.y.toFixed(1)})`);
    edgeLayer.selectAll('g.edge').each(function each(d) {
      const path = edgePath(d);
      d3.select(this).selectAll('path').attr('d', path);
    });
  }

  // --- Render -------------------------------------------------------------------

  function render(scene, options = {}) {
    // How small the names may get when the map is fitted small (see app.css).
    svg.style('--floor', scene.labelFloor ?? 0.85);
    const hadFocus = svg.node().contains(document.activeElement);
    const anchor = placed.get(options.enterFrom) ?? placed.get(scene.focusKey) ?? { x: 0, y: 0 };
    const nodes = scene.nodes.map((target) => {
      const before = placed.get(target.key);
      return { ...target, tx: target.x, ty: target.y, x: before ? before.x : anchor.x, y: before ? before.y : anchor.y, vx: 0, vy: 0 };
    });
    // Tab order: the focus, then the map column by column.
    nodes.sort((a, b) => (b.tone === 'focus') - (a.tone === 'focus') || Math.round(a.tx / 60) - Math.round(b.tx / 60) || a.ty - b.ty);
    placed = new Map(nodes.map((d) => [d.key, d]));
    current = { ...scene, nodes };
    svg.classed('is-overview', !scene.focusKey);

    boxLayer.selectAll('rect').data(scene.boxes).join('rect')
      .attr('x', (d) => d.x).attr('y', (d) => d.y).attr('width', (d) => d.w).attr('height', (d) => d.h).attr('rx', 14);

    captionLayer.selectAll('text').data(scene.captions, (d) => `${d.kind}|${d.text}`).join(
      (enter) => enter.append('text').attr('class', (d) => `caption caption-${d.kind}`),
    )
      .attr('x', (d) => d.x).attr('y', (d) => d.y).attr('text-anchor', (d) => d.anchor)
      .style('--c', (d) => d.color)
      .text((d) => d.text);

    const edges = edgeLayer.selectAll('g.edge').data(scene.edges, (d) => d.id).join((enter) => {
      const g = enter.append('g');
      g.append('path').attr('class', 'edge-line');
      g.append('path').attr('class', 'edge-hit');
      return g;
    });
    edges
      .attr('class', (d) => `edge edge-${d.tone} rel-${d.type}${d.edge ? '' : ' edge-bundle'}${d.id === selectedEdge ? ' is-selected' : ''}`)
      .style('--c', (d) => RELATIONS[d.type]?.color)
      .on('pointermove', (event, d) => showTip(edgeTip(d), event.clientX, event.clientY))
      .on('pointerleave', hideTip)
      .on('click', (event, d) => {
        if (d.edge) handlers.onEdge?.(d);
      });
    edges.select('.edge-line').attr('marker-end', (d) => (d.arrow ? `url(#arrow-${d.id === selectedEdge ? 'selected' : d.tone === 'far' ? 'far' : 'main'})` : null));

    const joined = nodeLayer.selectAll('g.node').data(nodes, (d) => d.key).join(
      (enter) => {
        const g = enter.append('g').attr('role', 'button');
        g.append('path').attr('class', 'halo');
        g.append('path').attr('class', 'shape');
        g.append('path').attr('class', 'core');
        g.append('path').attr('class', 'ring');
        g.append('g').attr('class', 'label');
        return g;
      },
    );
    joined
      .attr('class', (d) => `node node-${d.tone}${d.lit ? ' node-lit' : ''} layer-${d.node.layer} class-${d.node.label}`)
      .attr('tabindex', (d) => (d.tone === 'dot' ? -1 : 0))
      .attr('aria-label', (d) => accessibleName(d.node)
        + (d.tone === 'focus' ? '. En foco' : '. Enter para ponerlo en foco')
        + (d.expandable ? '. Tiene más conexiones: pulsa + para traerlas' : ''))
      .attr('aria-current', (d) => (d.tone === 'focus' ? 'true' : null))
      .style('--c', (d) => classColor(d.node))
      .on('click', (event, d) => {
        if (event.target.closest('.plus')) return;
        if (d.tone !== 'focus') handlers.onFocus?.(d.key);
      })
      .on('keydown', onNodeKey)
      .on('pointerenter', (event, d) => {
        showTip(nodeTip(d), event.clientX, event.clientY);
        edgeLayer.selectAll('g.edge').classed('is-near', (e) => e.from === d.key || e.to === d.key);
      })
      .on('pointerleave', () => {
        hideTip();
        edgeLayer.selectAll('g.edge').classed('is-near', false);
      })
      .on('focus', function onFocus(event, d) {
        if (!this.matches(':focus-visible')) return;
        const box = this.getBoundingClientRect();
        showTip(nodeTip(d), box.left + box.width / 2, box.bottom - 6);
      })
      .on('blur', hideTip);

    joined.select('.halo').attr('d', (d) => (d.tone === 'focus' ? outline(d, d.r + 9) : null));
    joined.select('.shape').attr('d', (d) => outline(d))
      .style('fill', (d) => (d.node.layer === 'reference' || d.tone === 'dot' ? null : `url(#sphere-${d.node.label})`));
    // CS2023 reads as a double outline; a document carries its page.
    joined.select('.core').attr('d', (d) => {
      if (d.tone === 'dot') return null;
      if (d.node.label === 'LearningResource') return DOCUMENT_GLYPH;
      return d.node.layer === 'reference' ? hexagon(d.r * 0.62) : null;
    }).classed('glyph', (d) => d.node.label === 'LearningResource');
    joined.select('.ring').attr('d', (d) => outline(d, d.r + 5));

    joined.select('.label').each(function label(d) {
      const g = d3.select(this);
      g.selectAll('*').remove();
      if (!d.label) return;
      const { side, lines, sub } = d.label;
      const count = lines.length + (sub ? 1 : 0);
      const anchorText = side === 'left' ? 'end' : side === 'right' ? 'start' : 'middle';
      const gap = d.tone === 'focus' ? 18 : 10;
      const x = side === 'left' ? -(d.r + gap) : side === 'right' ? d.r + gap : 0;
      const first = side === 'below' ? d.r + (d.tone === 'focus' ? 26 : 19) : side === 'above' ? -(d.r + 10) - (count - 1) * LINE_HEIGHT : -((count - 1) * LINE_HEIGHT) / 2 + 4.5;
      lines.forEach((line, index) => {
        g.append('text').attr('class', 'name').attr('x', x).attr('y', first + index * LINE_HEIGHT).attr('text-anchor', anchorText).text(line);
      });
      if (sub) {
        g.append('text').attr('class', 'sub').attr('x', x).attr('y', first + lines.length * LINE_HEIGHT).attr('text-anchor', anchorText).text(sub);
      }
    });

    joined.each(function plus(d) {
      const g = d3.select(this);
      g.select('.plus').remove();
      if (!d.expandable) return;
      const offset = d.r * 0.82 + 5;
      const button = g.append('g').attr('class', 'plus').attr('transform', `translate(${offset},${-offset})`);
      button.append('circle').attr('r', 8.5);
      button.append('path').attr('d', 'M-4,0h8M0,-4v8');
      button.append('title').text('Traer sus conexiones sin cambiar de lugar');
      button.on('click', (event) => {
        event.stopPropagation();
        handlers.onExpand?.(d.key);
      });
    });

    simulation.nodes(nodes);
    if (reduced.matches || firstRender) {
      for (const d of nodes) {
        d.x = d.tx;
        d.y = d.ty;
      }
      draw();
    } else {
      simulation.alpha(1).restart();
    }
    fit(firstRender || options.instant ? 0 : 560);
    firstRender = false;
    if (hadFocus && scene.focusKey) focusNodeElement(options.keepFocusOn ?? scene.focusKey);
  }

  function select(id) {
    selectedEdge = id;
    edgeLayer.selectAll('g.edge')
      .classed('is-selected', (d) => d.id === id)
      .select('.edge-line')
      .attr('marker-end', (d) => (d.arrow ? `url(#arrow-${d.id === id ? 'selected' : d.tone === 'far' ? 'far' : 'main'})` : null));
  }

  const resize = new ResizeObserver(() => fit(0));
  resize.observe(container);

  return {
    render,
    select,
    fit,
    zoomBy,
    focusNode: focusNodeElement,
    destroy() {
      resize.disconnect();
      simulation.stop();
      svg.remove();
      tooltip.remove();
    },
  };
}
