/* Dibujo del mapa de metro con D3 (selección, transiciones y zoom).
 * Recibe el modelo de modelo.js y su disposición; no conoce la API.
 */
(function (root) {
  'use strict';

  const TINTA = '#15171C';
  const SEP = 7;          // separación entre líneas paralelas
  const GROSOR = 6;       // grosor de línea
  const RADIO_ESQ = 16;   // radio de las esquinas de los tramos

  function partirTexto(texto, max, lineasMax) {
    const palabras = String(texto).split(/\s+/);
    const out = []; let actual = '';
    palabras.forEach(function (p) {
      if (!actual) actual = p;
      else if ((actual + ' ' + p).length <= max) actual += ' ' + p;
      else { out.push(actual); actual = p; }
    });
    if (actual) out.push(actual);
    if (out.length > lineasMax) {
      const cort = out.slice(0, lineasMax);
      cort[lineasMax - 1] = cort[lineasMax - 1].replace(/\s*\S*$/, '') + '…';
      return cort;
    }
    return out;
  }

  /** Polilínea con esquinas redondeadas (cuadráticas). */
  function caminoRedondeado(pts, r) {
    if (pts.length < 2) return '';
    let d = 'M' + pts[0][0] + ',' + pts[0][1];
    for (let i = 1; i < pts.length - 1; i++) {
      const p0 = pts[i - 1]; const p1 = pts[i]; const p2 = pts[i + 1];
      const l1 = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
      const l2 = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
      const rr = Math.min(r, l1 / 2, l2 / 2);
      const a = [p1[0] - (p1[0] - p0[0]) * rr / (l1 || 1), p1[1] - (p1[1] - p0[1]) * rr / (l1 || 1)];
      const b = [p1[0] + (p2[0] - p1[0]) * rr / (l2 || 1), p1[1] + (p2[1] - p1[1]) * rr / (l2 || 1)];
      d += 'L' + a[0] + ',' + a[1] + 'Q' + p1[0] + ',' + p1[1] + ' ' + b[0] + ',' + b[1];
    }
    const u = pts[pts.length - 1];
    return d + 'L' + u[0] + ',' + u[1];
  }

  /** Tramo octilineal: horizontal, diagonal a 45° y horizontal. */
  function octilineal(x1, y1, x2, y2) {
    const dy = y2 - y1; const dx = x2 - x1;
    if (Math.abs(dy) < 0.5) return caminoRedondeado([[x1, y1], [x2, y2]], 0);
    const h = (dx - Math.abs(dy)) / 2;
    if (h >= 18) return caminoRedondeado([[x1, y1], [x1 + h, y1], [x2 - h, y2], [x2, y2]], RADIO_ESQ);
    // demasiado empinado: curva suave
    return 'M' + x1 + ',' + y1 + 'C' + (x1 + dx * 0.6) + ',' + y1 + ' ' + (x2 - dx * 0.6) + ',' + y2 + ' ' + x2 + ',' + y2;
  }

  function crear(svgEl, manejadores) {
    const d3 = root.d3;
    const svg = d3.select(svgEl);
    svg.attr('role', 'img');
    const lienzo = svg.append('g').attr('class', 'm-lienzo');
    const capas = {};
    ['columnas', 'anden', 'tramos', 'espuelas', 'halo', 'estaciones', 'insignias', 'marcas'].forEach(function (c) {
      capas[c] = lienzo.append('g').attr('class', 'm-' + c);
    });
    const zoom = d3.zoom().scaleExtent([0.35, 2.6]).on('zoom', function (ev) { lienzo.attr('transform', ev.transform); });
    svg.call(zoom).on('dblclick.zoom', null);

    let actual = null; // {modelo, dispo}
    let seleccion = null;
    let ultimoDestino = null;

    function offsetEn(est, lineaKey, ordenLinea) {
      const ls = est.lineas.slice().sort(function (a, b) { return ordenLinea[a] - ordenLinea[b]; });
      const i = ls.indexOf(lineaKey);
      if (i < 0) return 0;
      return (i - (ls.length - 1) / 2) * SEP;
    }

    function encajar(animar) {
      if (!actual) return;
      const caja = svgEl.getBoundingClientRect();
      const w = caja.width || 800; const h = caja.height || 500;
      const d = actual.dispo;
      const k = Math.min(1.15, (w - 40) / d.ancho, (h - 30) / d.alto);
      const tx = (w - d.ancho * k) / 2; const ty = Math.max(6, (h - d.alto * k) / 2);
      const t = d3.zoomIdentity.translate(tx, ty).scale(k);
      (animar ? svg.transition().duration(500) : svg).call(zoom.transform, t);
    }

    function dibujar(modelo, dispo, sel) {
      const mismoDestino = ultimoDestino === (modelo.objetivo && modelo.objetivo.key) + '|' + modelo.tipo;
      ultimoDestino = (modelo.objetivo && modelo.objetivo.key) + '|' + modelo.tipo;
      actual = { modelo: modelo, dispo: dispo };
      seleccion = sel || null;
      const pos = dispo.pos;
      const porKey = {}; modelo.estaciones.forEach(function (s) { porKey[s.key] = s; });
      const lineaPorKey = {}; const ordenLinea = {};
      modelo.lineas.forEach(function (l, i) { lineaPorKey[l.key] = l; ordenLinea[l.key] = i; });
      const dur = 650;

      svg.attr('aria-label', 'Mapa del camino hasta ' + (modelo.objetivo ? modelo.objetivo.name_es : '') +
        '. La lista de indicaciones a la derecha describe el mismo recorrido.');

      /* columnas */
      const altoGuia = dispo.alto - 40;
      const col = capas.columnas.selectAll('g.m-col').data(dispo.columnas, function (c) { return c.col; });
      col.exit().remove();
      const colE = col.enter().append('g').attr('class', 'm-col');
      colE.append('line').attr('class', 'm-guia');
      colE.append('rect').attr('class', 'm-col-fondo');
      colE.append('text').attr('class', 'm-col-titulo');
      const colU = colE.merge(col);
      colU.select('line').attr('x1', function (c) { return c.x; }).attr('x2', function (c) { return c.x; }).attr('y1', 62).attr('y2', altoGuia);
      colU.select('text').attr('x', function (c) { return c.x; }).attr('y', 44).text(function (c) { return c.titulo.toUpperCase(); });
      colU.each(function () {
        const g = d3.select(this); const t = g.select('text').node();
        let bb = { width: 60, height: 14, x: 0, y: 32 };
        try { bb = t.getBBox(); } catch (e) { /* sin layout */ }
        g.select('rect').attr('x', bb.x - 10).attr('y', bb.y - 5).attr('width', bb.width + 20).attr('height', bb.height + 10).attr('rx', 4);
      });

      /* andén de destino (tema como destino) */
      const anden = capas.anden.selectAll('g.m-anden').data(dispo.anden ? [dispo.anden] : []);
      anden.exit().remove();
      const andE = anden.enter().append('g').attr('class', 'm-anden');
      andE.append('rect');
      andE.append('text').attr('class', 'm-anden-rotulo');
      andE.append('text').attr('class', 'm-anden-nombre');
      const andU = andE.merge(anden);
      andU.select('rect').attr('x', function (a) { return a.x; }).attr('y', function (a) { return a.y; })
        .attr('width', function (a) { return a.ancho; }).attr('height', function (a) { return a.alto; }).attr('rx', 18);
      andU.select('.m-anden-rotulo').attr('x', function (a) { return a.x + a.ancho / 2; }).attr('y', function (a) { return a.y + 20; }).text('META · TEMA');
      andU.select('.m-anden-nombre').attr('x', function (a) { return a.x + a.ancho / 2; }).attr('y', function (a) { return a.y + 38; })
        .text(function () { return partirTexto(modelo.objetivo.name_es, 26, 1)[0]; });

      /* tramos */
      const piezas = [];
      modelo.tramos.forEach(function (t) {
        const a = pos[t.desde]; const b = pos[t.hasta];
        const ea = porKey[t.desde]; const eb = porKey[t.hasta];
        const ra = ea.esCurso || ea.destino ? 0 : 0;
        if (t.lineas.length) {
          t.lineas.slice().sort(function (x, y) { return ordenLinea[x] - ordenLinea[y]; }).forEach(function (lk) {
            const l = lineaPorKey[lk];
            const oa = offsetEn(ea, lk, ordenLinea); const ob = offsetEn(eb, lk, ordenLinea);
            piezas.push({ id: t.id + '|' + lk, tramo: t, linea: l, d: octilineal(a.x + ra, a.y + oa, b.x, b.y + ob), col: ea.col });
          });
        } else {
          piezas.push({ id: t.id + '|x', tramo: t, linea: null, d: octilineal(a.x, a.y, b.x - (eb.esCurso ? 46 : 0), b.y), col: ea.col });
        }
      });
      // uniones verticales (ruta entre cursos): una línea recorre sus estaciones de la misma columna
      if (modelo.unirColumna) {
        modelo.lineas.forEach(function (l) {
          const ests = l.estaciones.map(function (k) { return porKey[k]; }).filter(Boolean)
            .sort(function (x, y) { return pos[x.key].y - pos[y.key].y; });
          if (ests.length) {
            const x0 = pos[ests[0].key].x + offsetEn(ests[0], l.key, ordenLinea);
            piezas.push({ id: 'v|' + l.key + '|cab', tramo: null, linea: l, vertical: true, cabecera: true,
              d: 'M' + x0 + ',' + (pos[ests[0].key].y - 46) + 'L' + x0 + ',' + pos[ests[0].key].y, col: 0 });
          }
          for (let i = 0; i < ests.length - 1; i++) {
            const x = pos[ests[i].key].x + offsetEn(ests[i], l.key, ordenLinea);
            piezas.push({ id: 'v|' + l.key + '|' + i, tramo: null, linea: l, vertical: true,
              d: 'M' + x + ',' + pos[ests[i].key].y + 'L' + x + ',' + pos[ests[i + 1].key].y, col: 0 });
          }
        });
      }
      const tr = capas.tramos.selectAll('g.m-pieza').data(piezas, function (p) { return p.id; });
      tr.exit().transition().duration(250).style('opacity', 0).remove();
      const trE = tr.enter().append('g').attr('class', 'm-pieza');
      trE.append('path').attr('class', 'm-via');
      trE.append('path').attr('class', 'm-via-interior');
      const trU = trE.merge(tr);
      trU.classed('m-transbordo', function (p) { return !p.linea; })
        .classed('m-ref', function (p) { return p.linea && p.linea.referencia; });
      trU.select('.m-via').attr('d', function (p) { return p.d; })
        .attr('stroke', function (p) { return p.linea ? p.linea.color : TINTA; })
        .attr('stroke-width', function (p) { return p.linea ? GROSOR : 3; });
      trU.select('.m-via-interior').attr('d', function (p) { return p.d; })
        .style('display', function (p) { return p.linea && p.linea.referencia ? null : 'none'; });
      // animación de trazado
      trE.select('.m-via').each(function (p) {
        if (p.linea === null) return;
        let L = 0;
        try { L = this.getTotalLength(); } catch (e) { L = 0; }
        if (!L) return;
        d3.select(this).attr('stroke-dasharray', L + ' ' + L).attr('stroke-dashoffset', L)
          .transition().delay(120 + p.col * 180).duration(dur).ease(d3.easeCubicOut)
          .attr('stroke-dashoffset', 0)
          .on('end', function () { d3.select(this).attr('stroke-dasharray', null); });
      });

      /* espuelas: la línea toca la estación pero no sigue por ningún tramo */
      const conTramo = {};
      piezas.forEach(function (p) {
        if (!p.linea) return;
        if (p.tramo) { conTramo[p.tramo.desde + '|' + p.linea.key] = true; conTramo[p.tramo.hasta + '|' + p.linea.key] = true; }
      });
      if (modelo.unirColumna) {
        modelo.lineas.forEach(function (l) { l.estaciones.forEach(function (k) { conTramo[k + '|' + l.key] = true; }); });
      }
      const espuelas = [];
      modelo.estaciones.forEach(function (s) {
        const sueltas = s.lineas.filter(function (lk) { return !conTramo[s.key + '|' + lk]; });
        sueltas.forEach(function (lk, i) {
          const p = pos[s.key];
          const ox = (i - (sueltas.length - 1) / 2) * 30;
          espuelas.push({ id: s.key + '|' + lk, linea: lineaPorKey[lk], x: p.x + ox, y: p.y, y2: p.y - 58, est: s });
        });
      });
      const es = capas.espuelas.selectAll('g.m-espuela').data(espuelas, function (e) { return e.id; });
      es.exit().remove();
      const esE = es.enter().append('g').attr('class', 'm-espuela');
      esE.append('path').attr('class', 'm-via');
      esE.append('path').attr('class', 'm-via-interior');
      esE.append('line').attr('class', 'm-tope');
      const esU = esE.merge(es);
      esU.classed('m-ref', function (e) { return e.linea.referencia; });
      esU.selectAll('path').attr('d', function (e) { return 'M' + e.x + ',' + e.y + 'L' + e.x + ',' + e.y2; });
      esU.select('.m-via').attr('stroke', function (e) { return e.linea.color; }).attr('stroke-width', GROSOR);
      esU.select('.m-via-interior').style('display', function (e) { return e.linea.referencia ? null : 'none'; });
      esU.select('.m-tope').attr('x1', function (e) { return e.x - 9; }).attr('x2', function (e) { return e.x + 9; })
        .attr('y1', function (e) { return e.y2; }).attr('y2', function (e) { return e.y2; }).attr('stroke', function (e) { return e.linea.color; });

      /* estaciones */
      const est = capas.estaciones.selectAll('g.m-est').data(modelo.estaciones, function (s) { return s.key; });
      est.exit().transition('salir').duration(200).style('opacity', 0).remove();
      const estE = est.enter().append('g').attr('class', 'm-est')
        .attr('tabindex', 0)
        .attr('transform', function (s) { return 'translate(' + pos[s.key].x + ',' + pos[s.key].y + ')'; })
        .style('opacity', 0);
      estE.append('circle').attr('class', 'm-halo').attr('r', 25);
      estE.append('g').attr('class', 'm-glifo');
      estE.append('g').attr('class', 'm-rotulo');
      const estU = estE.merge(est);
      estU.attr('role', 'button')
        .attr('aria-label', function (s) {
          return s.nombre + (s.destino ? ', meta' : '') + (s.lineas.length > 1 ? ', transbordo' : '') + '. Abrir ficha.';
        })
        .classed('m-destino', function (s) { return s.destino; })
        .classed('m-sel', function (s) { return s.key === seleccion; })
        .on('click', function (ev, s) { ev.stopPropagation(); manejadores.onEstacion && manejadores.onEstacion(s.key); })
        .on('keydown', function (ev, s) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); manejadores.onEstacion && manejadores.onEstacion(s.key); } });
      estE.transition('aparecer').delay(function (s) { return 60 + s.col * 180; }).duration(400).style('opacity', 1);
      estU.transition('mover').duration(mismoDestino ? 500 : 0)
        .attr('transform', function (s) { return 'translate(' + pos[s.key].x + ',' + pos[s.key].y + ')'; });

      estU.select('.m-glifo').each(function (s) {
        const g = d3.select(this); g.selectAll('*').remove();
        const k = s.lineas.length;
        if (s.esCurso) {
          g.append('rect').attr('class', 'm-terminal').attr('x', -46).attr('y', -21).attr('width', 92).attr('height', 42).attr('rx', 21);
          g.append('text').attr('class', 'm-terminal-codigo').attr('y', 5).text(s.nodo.course_code || '');
        } else if (s.destino) {
          g.append('circle').attr('class', 'm-terminal').attr('r', 18);
          g.append('circle').attr('class', 'm-terminal-ojo').attr('r', 7);
        } else if (k >= 2) {
          const alto = 24 + (k - 1) * SEP;
          g.append('rect').attr('class', 'm-parada m-cambio').attr('x', -12).attr('y', -alto / 2).attr('width', 24).attr('height', alto).attr('rx', 12);
        } else {
          g.append('circle').attr('class', 'm-parada').attr('r', 11);
        }
      });
      estU.select('.m-rotulo').each(function (s) {
        const g = d3.select(this); g.selectAll('*').remove();
        const k = s.lineas.length;
        const izquierda = modelo.unirColumna && !s.destino;
        const lineas = partirTexto(s.nombre, s.destino ? 22 : 21, 3);
        const salto = s.destino ? 18 : 16;
        const base = izquierda ? 5 - (lineas.length - 1) * salto / 2 - 6 : (s.esCurso ? 40 : (s.destino ? 38 : 30 + Math.max(0, k - 1) * SEP / 2));
        const x = izquierda ? -26 : 0;
        const t = g.append('text').attr('class', s.destino ? 'm-nombre m-nombre-destino' : 'm-nombre').attr('y', base);
        if (izquierda) t.style('text-anchor', 'end');
        lineas.forEach(function (l, i) { t.append('tspan').attr('x', x).attr('dy', i === 0 ? 0 : salto).text(l); });
        const yTag = base + (lineas.length - 1) * salto + 16;
        const fuente = root.IEKG_MODELO.codigoFuente(s.fuente);
        if (fuente) {
          const tag = g.append('text').attr('class', 'm-tag').attr('x', x).attr('y', yTag).text('Sílabo ' + fuente);
          if (izquierda) tag.style('text-anchor', 'end');
        }
        if (k > 1) {
          g.append('text').attr('class', 'm-cambio-rotulo').attr('x', 18).attr('y', -(12 + (k - 1) * SEP / 2)).text('TRANSBORDO');
        }
      });

      /* halo de selección */
      estU.select('.m-halo').classed('m-halo-on', function (s) { return s.key === seleccion; });

      /* insignias de línea y marcas "?" sobre cada tramo */
      const insignias = []; const marcas = [];
      const vistas = {};
      trU.each(function (p) {
        if (!p.tramo) return;
        const nodo = d3.select(this).select('.m-via').node();
        let L = 0; try { L = nodo.getTotalLength(); } catch (e) { L = 0; }
        if (!L) return;
        if (p.linea && !vistas[p.linea.key]) {
          vistas[p.linea.key] = true;
          const pt = nodo.getPointAtLength(L * 0.3);
          insignias.push({ id: 'i|' + p.linea.key, linea: p.linea, x: pt.x, y: pt.y });
        }
        if (!marcas.some(function (m) { return m.tramo.id === p.tramo.id; })) {
          const pm = nodo.getPointAtLength(L * 0.64);
          marcas.push({ id: 'q|' + p.tramo.id, tramo: p.tramo, x: pm.x, y: pm.y });
        }
      });
      espuelas.forEach(function (e) {
        if (!vistas[e.linea.key]) { vistas[e.linea.key] = true; insignias.push({ id: 'i|' + e.linea.key, linea: e.linea, x: e.x, y: e.y2 - 16 }); }
      });
      if (modelo.unirColumna) {
        piezas.filter(function (p) { return p.cabecera && !vistas[p.linea.key]; }).forEach(function (p) {
          vistas[p.linea.key] = true;
          const m = /M([0-9.-]+),([0-9.-]+)L/.exec(p.d);
          insignias.push({ id: 'i|' + p.linea.key, linea: p.linea, x: +m[1], y: +m[2] - 6 });
        });
      }
      const ins = capas.insignias.selectAll('g.m-insignia').data(insignias, function (i) { return i.id; });
      ins.exit().remove();
      const insE = ins.enter().append('g').attr('class', 'm-insignia').attr('tabindex', 0).attr('role', 'button');
      insE.append('rect'); insE.append('text');
      const insU = insE.merge(ins);
      insU.attr('transform', function (i) { return 'translate(' + i.x + ',' + i.y + ')'; })
        .attr('aria-label', function (i) { return 'Línea ' + i.linea.insignia + ': ' + i.linea.nombre + '. ¿Por qué está en el camino?'; })
        .classed('m-ref', function (i) { return i.linea.referencia; })
        .on('click', function (ev, i) { ev.stopPropagation(); manejadores.onLinea && manejadores.onLinea(i.linea); })
        .on('keydown', function (ev, i) { if (ev.key === 'Enter') manejadores.onLinea && manejadores.onLinea(i.linea); });
      insU.select('text').attr('y', 4.5).text(function (i) { return i.linea.insignia; });
      insU.select('rect').each(function (i) {
        const w = Math.max(24, String(i.linea.insignia).length * 8.4 + 14);
        d3.select(this).attr('x', -w / 2).attr('y', -12).attr('width', w).attr('height', 24)
          .attr('rx', i.linea.referencia ? 3 : 12).attr('fill', i.linea.color);
      });
      insE.style('opacity', 0).transition('aparecer').delay(500).duration(300).style('opacity', 1);

      const mq = capas.marcas.selectAll('g.m-marca').data(marcas, function (m) { return m.id; });
      mq.exit().remove();
      const mqE = mq.enter().append('g').attr('class', 'm-marca').attr('tabindex', 0).attr('role', 'button');
      mqE.append('circle').attr('r', 10);
      mqE.append('text').attr('y', 4).text('?');
      const mqU = mqE.merge(mq);
      mqU.attr('transform', function (m) { return 'translate(' + m.x + ',' + m.y + ')'; })
        .attr('aria-label', function (m) { return '¿Por qué ' + porKey[m.tramo.hasta].nombre + ' viene después de ' + porKey[m.tramo.desde].nombre + '?'; })
        .on('click', function (ev, m) { ev.stopPropagation(); manejadores.onTramo && manejadores.onTramo(m.tramo); })
        .on('keydown', function (ev, m) { if (ev.key === 'Enter') manejadores.onTramo && manejadores.onTramo(m.tramo); });
      mqE.style('opacity', 0).transition('aparecer').delay(700).duration(300).style('opacity', 1);

      if (!mismoDestino) encajar(false);
    }

    function seleccionar(key) {
      seleccion = key;
      capas.estaciones.selectAll('g.m-est').classed('m-sel', function (s) { return s.key === key; })
        .select('.m-halo').classed('m-halo-on', function (s) { return s.key === key; });
    }

    function limpiar() {
      Object.keys(capas).forEach(function (c) { capas[c].selectAll('*').remove(); });
      actual = null; ultimoDestino = null;
    }

    return {
      dibujar: dibujar,
      seleccionar: seleccionar,
      encajar: function () { encajar(true); },
      acercar: function (f) { svg.transition().duration(250).call(zoom.scaleBy, f); },
      limpiar: limpiar
    };
  }

  const exportado = { crear: crear, partirTexto: partirTexto, octilineal: octilineal };
  root.IEKG_METRO = exportado;
  if (typeof module !== 'undefined' && module.exports) module.exports = exportado;
})(typeof window !== 'undefined' ? window : globalThis);
