// Mini mapa de la ficha (D3 7.9.0). Es secundario: todo lo que muestra ya está
// en las secciones de la ficha como texto. Dibuja el subgrafo de `/api/nodes`
// del elemento en foco, sin inventar nodos ni aristas.
//
// RF-22 sin depender del color: la capa de referencia (CS2023) se dibuja con
// cuadrados; la institucional (sílabos), con círculos; los documentos, con rombos.
(function (global) {
  'use strict';

  const DOCUMENTOS = ['LearningResource', 'ResourceType'];
  let contador = 0;

  function datosMapa(detalle) {
    const foco = detalle.nodes[0];
    const conDocs = DOCUMENTOS.includes(foco.label);
    const nodes = detalle.nodes
      .filter((n) => conDocs || !DOCUMENTOS.includes(n.label))
      .map((n) => ({ key: n.key, label: n.label, layer: n.layer, name: n.name_es, code: n.course_code, mas: !!n.more_neighbors }));
    const claves = new Set(nodes.map((n) => n.key));
    const links = detalle.edges
      .filter((e) => e.type !== 'WAS_DERIVED_FROM' && claves.has(e.source) && claves.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, type: e.type }));
    const vecinos = new Set();
    for (const l of links) {
      if (l.source === foco.key) vecinos.add(l.target);
      if (l.target === foco.key) vecinos.add(l.source);
    }
    for (const n of nodes) n.nivel = n.key === foco.key ? 0 : vecinos.has(n.key) ? 1 : 2;
    return { nodes, links, foco: foco.key };
  }

  function forma(n, r) {
    if (DOCUMENTOS.includes(n.label)) return `M0,${-r * 1.25}L${r * 1.25},0L0,${r * 1.25}L${-r * 1.25},0Z`;
    if (n.layer === 'reference') return `M${-r},${-r}H${r}V${r}H${-r}Z`;
    return `M${-r},0A${r},${r} 0 1,0 ${r},0A${r},${r} 0 1,0 ${-r},0`;
  }

  function corto(texto, max) {
    return texto.length > max ? `${texto.slice(0, max - 1)}…` : texto;
  }

  // Dibuja en `svg` (elemento DOM). opciones: {grande, alElegir(clave)}.
  function dibujar(svg, detalle, opciones) {
    const d3 = global.d3;
    const { grande, alElegir } = opciones || {};
    const id = `mm${++contador}`;
    const { nodes, links, foco } = datosMapa(detalle);
    const raiz = d3.select(svg);
    raiz.selectAll('*').remove();

    const radio = (n) => (n.nivel === 0 ? (grande ? 11 : 8) : n.nivel === 1 ? (grande ? 7 : 5) : (grande ? 4.5 : 3.2));
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((n) => n.key).distance((l) => (l.source.nivel === 0 || l.target.nivel === 0 ? (grande ? 95 : 55) : (grande ? 45 : 26))))
      .force('charge', d3.forceManyBody().strength(grande ? -260 : -90))
      .force('collide', d3.forceCollide((n) => radio(n) + (grande ? 10 : 4)))
      .force('x', d3.forceX(0).strength(0.04))
      .force('y', d3.forceY(0).strength(0.04))
      .stop();
    const centro = nodes.find((n) => n.key === foco);
    if (centro) { centro.fx = 0; centro.fy = 0; }
    for (let i = 0; i < 300; i++) sim.tick();

    // Encuadre simétrico alrededor del foco (fijo en 0,0): el foco queda al centro.
    const pad = grande ? 70 : 18;
    const ex = Math.max(40, ...nodes.map((n) => Math.abs(n.x))) + pad;
    const ey = Math.max(30, ...nodes.map((n) => Math.abs(n.y))) + pad;
    raiz.attr('viewBox', `${-ex} ${-ey} ${2 * ex} ${2 * ey}`).attr('preserveAspectRatio', 'xMidYMid meet');

    const defs = raiz.append('defs');
    defs.append('marker').attr('id', `${id}-flecha`).attr('viewBox', '0 -4 8 8').attr('refX', grande ? 16 : 11)
      .attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto')
      .append('path').attr('d', 'M0,-4L8,0L0,4').attr('class', 'mm-flecha');

    const capa = raiz.append('g');
    capa.append('g').selectAll('line').data(links).join('line')
      .attr('class', (l) => `mm-arista mm-${l.type.toLowerCase()}${l.source.nivel === 0 || l.target.nivel === 0 ? ' mm-cerca' : ''}`)
      .attr('x1', (l) => l.source.x).attr('y1', (l) => l.source.y)
      .attr('x2', (l) => l.target.x).attr('y2', (l) => l.target.y)
      .attr('marker-end', (l) => (l.type === 'HAS_PREREQUISITE' || l.type === 'SPECIALIZES' ? `url(#${id}-flecha)` : null));

    const g = capa.append('g').selectAll('g').data(nodes).join('g')
      .attr('class', (n) => `mm-nodo mm-${n.layer} mm-nivel${n.nivel}`)
      .attr('transform', (n) => `translate(${n.x},${n.y})`)
      .attr('tabindex', grande ? 0 : -1)
      .attr('role', 'link')
      .attr('aria-label', (n) => `${n.name}${n.code ? ` (${n.code})` : ''}`)
      .on('click', (ev, n) => { if (alElegir && n.key !== foco) alElegir(n.key); })
      .on('keydown', (ev, n) => { if ((ev.key === 'Enter' || ev.key === ' ') && alElegir && n.key !== foco) { ev.preventDefault(); alElegir(n.key); } });
    g.append('title').text((n) => `${n.name}${n.code ? ` (${n.code})` : ''} · ${n.layer === 'reference' ? 'CS2023' : 'Sílabo PUCP'}${n.mas ? ' · tiene más relaciones' : ''}`);
    // Anillo punteado: el vecino tiene más relaciones de las que caben; su ficha las muestra.
    g.filter((n) => grande && n.mas && n.nivel > 0).append('circle').attr('class', 'mm-mas').attr('r', (n) => radio(n) + 4);
    g.append('path').attr('d', (n) => forma(n, radio(n)));

    const conEtiqueta = (n) => n.nivel === 0 || (grande && n.nivel === 1);
    g.filter(conEtiqueta).append('text')
      .attr('class', 'mm-etiqueta')
      .attr('y', (n) => radio(n) + (grande ? 14 : 11))
      .attr('text-anchor', 'middle')
      .text((n) => (n.nivel === 0 ? corto(n.name, grande ? 40 : 26) : corto(n.code || n.name, 22)));

    if (grande) {
      raiz.call(d3.zoom().scaleExtent([0.4, 4]).on('zoom', (ev) => capa.attr('transform', ev.transform)));
    }
    return { nodos: nodes.length, aristas: links.length };
  }

  global.IEKG_MINIMAPA = { dibujar, datosMapa };
})(typeof window !== 'undefined' ? window : globalThis);
