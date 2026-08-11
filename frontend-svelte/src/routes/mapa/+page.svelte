<script>
  import { onMount } from 'svelte';
  import { fetchAPI, capaNBIActiva } from '$lib/stores';
  import { get } from 'svelte/store';

  let facultades   = $state([]);
  let carreras     = $state([]);
  let periodos     = $state([]);
  let anios        = $state([]);

  let filtros = $state({ facultad:'', carrera:'', periodo:'', estado:'', anio:'', buscar:'' });
  let total   = $state(0);
  let proySeleccionado = $state(null);
  let modalTab = $state('general');
  let fotoActiva = $state(0);
  let lightboxAbierto = $state(false);
  let modalDocs = $state([]);       // documentos cacheados por proyecto id
  let modalDocsLoad = $state(false);
  let docAbierto = $state(null);    // {url, nombre, extension}

  async function cargarDocumentos(id) {
    modalDocs = []; modalDocsLoad = true;
    try {
      const r = await fetch(`/api/proyectos/${id}/documentos/`, { credentials:'include' });
      modalDocs = r.ok ? await r.json() : [];
    } catch { modalDocs = []; }
    finally { modalDocsLoad = false; }
  }

  $effect(() => {
    if (proySeleccionado && modalTab === 'documentos') {
      cargarDocumentos(proySeleccionado.id);
    }
  });

  // Capa NBI (estado en store compartido con layout)
  let nbiAviso     = $state('');
  let nbiCargaTodo = $state(false);   // switch: OFF = solo viewport, ON = todos los cantones
  let nbiByCanton  = null;
  let nbiLayer     = null;
  let nbiLeyenda   = null;

  // Quevedo (centro por defecto)
  const QUEVEDO = { lat: -1.026, lng: -79.474, zoom: 12 };

  const ESTADOS = [
    { val:'EN_EJECUCION', label:'En ejecución', color:'#1b7505' },
    { val:'PROPUESTO',    label:'Propuesto',    color:'#dba112' },
    { val:'APROBADO',     label:'Aprobado',     color:'#0d6efd' },
    { val:'EN_CIERRE',    label:'En cierre',    color:'#fd7e14' },
    { val:'DETENIDO',     label:'Detenido',     color:'#dc3545' },
    { val:'FINALIZADO',   label:'Finalizado',   color:'#a8a8a7' },
    { val:'RECHAZADO',    label:'Rechazado',    color:'#6c757d' },
  ];

  let map, markersLayer;

  // ── Proyectos ────────────────────────────────────────────────
  async function cargarProyectos() {
    const params = new URLSearchParams();
    Object.entries(filtros).forEach(([k,v]) => { if(v) params.set(k,v); });
    const data = await fetchAPI('/api/mapa/proyectos/?' + params.toString());
    total = data.features?.length ?? 0;

    markersLayer.clearLayers();
    (data.features || []).forEach(f => {
      const [lng, lat] = f.geometry.coordinates;
      const p = f.properties;
      const L = window._L;
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:18px;height:18px;border-radius:50%;background:${p.color};border:2.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.35);cursor:pointer;"></div>`,
        iconSize: [18,18], iconAnchor: [9,9],
      });
      const marker = L.marker([lat, lng], { icon });
      marker.on('click', () => {
        proySeleccionado = p; modalTab = 'general'; fotoActiva = 0;
        lightboxAbierto = false; docAbierto = null; modalDocs = [];
      });
      marker.bindTooltip(p.nombre_corto, { direction:'top', offset:[0,-10] });
      markersLayer.addLayer(marker);
    });
  }

  // ── Capa NBI/INEC ───────────────────────────────────────────
  // Paleta pastel (tonos tierra/durazno) — más suave que YlOrRd
  function getNBIColor(pct) {
    if (pct >= 80) return '#c96f6f';
    if (pct >= 65) return '#e08a7d';
    if (pct >= 50) return '#eaa98a';
    if (pct >= 40) return '#f2c19a';
    if (pct >= 30) return '#f5d4a8';
    if (pct >= 20) return '#f7e3b8';
    return '#f0ead2';
  }

  // Cache del geojson de cantones (viene con dpa_canton ya inyectado)
  let cantonesGeo = null;

  // Bounds cacheados por feature (evitar recomputar en cada moveend)
  const featureBoundsCache = new WeakMap();
  function getFeatureBounds(L, feature) {
    let b = featureBoundsCache.get(feature);
    if (b) return b;
    b = L.geoJSON(feature).getBounds();
    featureBoundsCache.set(feature, b);
    return b;
  }

  function filtrarFeaturesPorVista(L) {
    if (!cantonesGeo || !map) return cantonesGeo?.features ?? [];
    if (nbiCargaTodo) return cantonesGeo.features;
    const view = map.getBounds();
    return cantonesGeo.features.filter(f => view.intersects(getFeatureBounds(L, f)));
  }

  async function cargarCantonesNBI() {
    const L = window._L;
    if (!map || !nbiByCanton) return;
    nbiAviso = 'Cargando capa NBI…';
    try {
      if (!cantonesGeo) {
        const res = await fetch('/geo/cantones_ec.geojson');
        if (!res.ok) throw new Error(`HTTP ${res.status} al leer /geo/cantones_ec.geojson`);
        cantonesGeo = await res.json();
      }
      renderNBILayer();
    } catch (e) {
      console.error('[NBI]', e);
      nbiAviso = `Error al cargar capa NBI: ${e.message || e}`;
    }
  }

  function renderNBILayer() {
    const L = window._L;
    if (!map || !cantonesGeo || !nbiByCanton) return;
    if (nbiLayer) { map.removeLayer(nbiLayer); nbiLayer = null; }
    const feats = filtrarFeaturesPorVista(L);
    let matched = 0;
    nbiLayer = L.geoJSON({ type:'FeatureCollection', features: feats }, {
      style: (feature) => {
        const p = feature.properties || {};
        const entry = p.dpa_canton ? nbiByCanton[p.dpa_canton] : null;
        const pct = entry?.nbi_pct ?? null;
        if (pct !== null) matched++;
        return {
          weight: 0.6, opacity: 0.8, color: '#333',
          fillOpacity: pct !== null ? 0.65 : 0.15,
          fillColor: pct !== null ? getNBIColor(pct) : '#d0d0d0',
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        const entry = p.dpa_canton ? nbiByCanton[p.dpa_canton] : null;
        const nombre = entry?.canton || p.canton || '';
        const prov = entry?.provincia || p.province || '';
        const pct = entry?.nbi_pct;
        const notaHist = p.canton_original
          ? `<br><i style="color:#888;font-size:.72rem">Zona ${p.canton_original} · asignada a ${nombre}</i>`
          : '';
        layer.bindTooltip(
          `<b>Cantón:</b> ${nombre}<br><b>Provincia:</b> ${prov}<br>` +
          (pct != null ? `<b>NBI 2022:</b> ${pct}%` : '<i>Sin dato NBI</i>') +
          notaHist,
          { sticky: true, direction: 'top' }
        );
      },
    }).addTo(map);
    const modo = nbiCargaTodo ? 'toda la capa' : 'solo vista actual';
    nbiAviso = `${matched} cantones (${modo})`;
  }

  function toggleNbiCargaTodo() {
    nbiCargaTodo = !nbiCargaTodo;
    if (nbiLayer) renderNBILayer();
  }

  function centrarEnQuevedo() {
    if (!map) return;
    map.setView([QUEVEDO.lat, QUEVEDO.lng], QUEVEDO.zoom);
  }

  function agregarLeyendaNBI() {
    const L = window._L;
    if (nbiLeyenda) return;
    nbiLeyenda = L.control({ position: 'bottomright' });
    nbiLeyenda.onAdd = () => {
      const div = L.DomUtil.create('div', 'nbi-leyenda');
      div.innerHTML = `
        <b>NBI 2022 (%)</b>
        <div><span style="background:#c96f6f"></span>≥ 80%</div>
        <div><span style="background:#e08a7d"></span>65 – 79%</div>
        <div><span style="background:#eaa98a"></span>50 – 64%</div>
        <div><span style="background:#f2c19a"></span>40 – 49%</div>
        <div><span style="background:#f5d4a8"></span>30 – 39%</div>
        <div><span style="background:#f7e3b8"></span>20 – 29%</div>
        <div><span style="background:#f0ead2"></span>&lt; 20%</div>
      `;
      return div;
    };
    nbiLeyenda.addTo(map);
  }

  async function toggleNBI(activo) {
    if (activo) {
      if (!nbiByCanton) {
        nbiByCanton = await fetchAPI('/api/capa-pobreza/');
      }
      await cargarCantonesNBI();
      agregarLeyendaNBI();
    } else {
      if (nbiLayer)   { map.removeLayer(nbiLayer); nbiLayer = null; }
      if (nbiLeyenda) { map.removeControl(nbiLeyenda); nbiLeyenda = null; }
      nbiAviso = '';
    }
  }

  // ── Mount ────────────────────────────────────────────────────
  onMount(async () => {
    // Inicia mapa inmediatamente mientras cargan los filtros en paralelo
    const Lprom = import('leaflet').then(m => m.default);

    const [L, facs, carrs, pers] = await Promise.all([
      Lprom,
      fetchAPI('/api/facultades/'),
      fetchAPI('/api/carreras/'),
      fetchAPI('/api/periodos/'),
    ]);
    facultades = facs;
    carreras   = carrs;
    periodos   = pers;

    try { const a = await fetchAPI('/api/mapa/anios/'); anios = a.anios || a; } catch {}

    window._L = L;
    map = L.map('map', { zoomControl: false }).setView([-1.5, -78.5], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    L.control.zoom({ position: 'topleft' }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);

    // Re-renderizar capa NBI en modo "solo vista" al mover/zoom
    let mvTimer;
    map.on('moveend zoomend', () => {
      if (!nbiLayer || nbiCargaTodo) return;
      clearTimeout(mvTimer);
      mvTimer = setTimeout(renderNBILayer, 120);
    });

    await cargarProyectos();

    // Suscribir al store DESPUÉS de que el mapa esté listo
    const unsubNBI = capaNBIActiva.subscribe(activo => toggleNBI(activo));
    return () => unsubNBI();
  });

  async function filtrar() { await cargarProyectos(); }
  function limpiar() {
    filtros = { facultad:'', carrera:'', periodo:'', estado:'', anio:'', buscar:'' };
    cargarProyectos();
  }

  let carrerasFiltradas = $derived(
    filtros.facultad
      ? carreras.filter(c => String(c.id_facultad) === String(filtros.facultad))
      : carreras
  );
</script>

<svelte:head><title>Mapa — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Mapa</span><span class="sep">/</span>
  </nav>
</div>

<div class="mapa-layout">
  <div class="mapa-right">

    <!-- FILTROS -->
    <div class="filtros-bar">
      <div class="filtros-inner">

        <select class="fsel" bind:value={filtros.facultad} onchange={() => { filtros.carrera=''; }}>
          <option value="">Facultad</option>
          {#each facultades as f}
            <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
          {/each}
        </select>

        <select class="fsel" bind:value={filtros.carrera}>
          <option value="">Carrera</option>
          {#each carrerasFiltradas as c}
            <option value={c.id_carrera}>{c.nombre}</option>
          {/each}
        </select>

        <select class="fsel" bind:value={filtros.periodo}>
          <option value="">Período</option>
          {#each periodos as p}
            <option value={p.id_periodo}>{p.nombre}</option>
          {/each}
        </select>

        <select class="fsel" bind:value={filtros.estado}>
          <option value="">Estado</option>
          {#each ESTADOS as e}
            <option value={e.val}>{e.label}</option>
          {/each}
        </select>

        <select class="fsel fsel-sm" bind:value={filtros.anio}>
          <option value="">Año</option>
          {#each anios as a}
            <option value={a}>{a}</option>
          {/each}
        </select>

        <div class="buscar-wrap">
          <i class="bi bi-search buscar-ico"></i>
          <input class="fbuscar" bind:value={filtros.buscar} placeholder="Buscar..." />
        </div>

        <button class="btn-quevedo" onclick={centrarEnQuevedo} title="Centrar en Quevedo">
          <i class="bi bi-geo-alt-fill"></i> Quevedo
        </button>

        <label class="nbi-switch" title="OFF: solo cantones visibles · ON: toda la capa">
          <input type="checkbox" checked={nbiCargaTodo} onchange={toggleNbiCargaTodo} />
          <span class="ns-slider"></span>
          <span class="ns-label">Toda la capa</span>
        </label>

        {#if nbiAviso}
          <span class="nbi-aviso">{nbiAviso}</span>
        {/if}

        <div class="factions">
          <span class="total-badge">{total} proy.</span>
          <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
          <button class="btn-filtrar" onclick={filtrar}>Filtrar</button>
        </div>

      </div>
    </div>

    <!-- MAPA -->
    <div id="map" style="flex:1;width:100%;min-height:300px;"></div>
  </div>
</div>

<!-- MODAL -->
{#if proySeleccionado}
  {@const p = proySeleccionado}
  {@const fotos = (p.fotos && p.fotos.length ? p.fotos : (p.foto_url ? [p.foto_url] : []))}
  {@const TABS = [
    { id:'general',    label:'General',    icon:'bi-info-circle' },
    { id:'ubicacion',  label:'Ubicación',  icon:'bi-geo-alt' },
    { id:'cronograma', label:'Cronograma', icon:'bi-calendar-range' },
    { id:'documentos', label:'Documentos', icon:'bi-file-earmark-pdf' },
    { id:'notas',      label:'Notas',      icon:'bi-journal-text', hidden: !p.observaciones && !p.motivo_detencion && !p.ods },
  ].filter(t => !t.hidden)}
  <div class="modal-overlay" onclick={() => proySeleccionado = null}>
    <div class="modal-box wide" onclick={(e) => e.stopPropagation()}>
      <button class="modal-close" onclick={() => proySeleccionado = null}>
        <i class="bi bi-x-lg"></i>
      </button>

      <div class="modal-split">
        <!-- COLUMNA IZQUIERDA: foto + header -->
        <aside class="msp-left">
          <div class="msp-foto">
            {#if fotos.length}
              {#key fotoActiva}
                <img
                  src={fotos[fotoActiva]}
                  alt="Foto {fotoActiva+1}"
                  onerror={(e) => { e.currentTarget.style.display='none'; e.currentTarget.parentElement.querySelector('.msp-fallback').style.display='flex'; }}
                />
              {/key}
              <div class="msp-fallback" style="display:none">
                <i class="bi bi-image-alt"></i>
                <small>Imagen no encontrada</small>
              </div>
              <button class="msp-expand" onclick={() => lightboxAbierto = true} title="Ver en grande">
                <i class="bi bi-arrows-fullscreen"></i>
              </button>
              {#if fotos.length > 1}
                <button class="msp-nav prev" onclick={() => fotoActiva = (fotoActiva - 1 + fotos.length) % fotos.length}>
                  <i class="bi bi-chevron-left"></i>
                </button>
                <button class="msp-nav next" onclick={() => fotoActiva = (fotoActiva + 1) % fotos.length}>
                  <i class="bi bi-chevron-right"></i>
                </button>
                <span class="msp-counter">{fotoActiva+1} / {fotos.length}</span>
              {/if}
            {:else}
              <div class="msp-fallback">
                <i class="bi bi-image"></i>
                <small>Sin fotos</small>
              </div>
            {/if}
          </div>

          <div class="msp-head">
            <div class="modal-estado" style="background:{p.color}20;color:{p.color}">
              {p.estado?.replace('_',' ')}
            </div>
            <h2 class="msp-title">{p.nombre}</h2>
            <span class="msp-code">{p.codigo}</span>
          </div>

          {#if fotos.length > 1}
            <div class="msp-thumbs">
              {#each fotos as f, i}
                <button
                  class="msp-thumb"
                  class:active={i === fotoActiva}
                  onclick={() => fotoActiva = i}
                  title="Ver foto {i+1}"
                >
                  <img src={f} alt="thumb {i+1}" onerror={(e) => { e.currentTarget.style.opacity=.3; }} />
                </button>
              {/each}
            </div>
          {/if}

          <!-- TABS -->
          <nav class="msp-tabs">
            {#each TABS as t}
              <button class="msp-tab" class:active={modalTab === t.id} onclick={() => modalTab = t.id}>
                <i class="bi {t.icon}"></i> {t.label}
              </button>
            {/each}
          </nav>
        </aside>

        <!-- COLUMNA DERECHA: contenido del tab -->
        <div class="msp-right">
          {#if modalTab === 'general'}
            {#if p.descripcion}
              <p class="msp-desc">{p.descripcion}</p>
            {/if}

            <h5 class="msp-h5">Académico</h5>
            <div class="msp-grid">
              <div class="mi"><i class="bi bi-mortarboard-fill"></i><div><span class="mi-l">Facultad</span><span class="mi-v">{p.facultad}</span></div></div>
              <div class="mi"><i class="bi bi-book-fill"></i><div><span class="mi-l">Carrera</span><span class="mi-v">{p.carrera}</span></div></div>
              {#if p.programa}<div class="mi full"><i class="bi bi-diagram-3"></i><div><span class="mi-l">Programa</span><span class="mi-v">{p.programa}</span></div></div>{/if}
              {#if p.linea_vinculacion}<div class="mi full"><i class="bi bi-link-45deg"></i><div><span class="mi-l">Línea de vinculación</span><span class="mi-v">{p.linea_vinculacion}</span></div></div>{/if}
              {#if p.area_conocimiento}<div class="mi"><i class="bi bi-lightbulb"></i><div><span class="mi-l">Área</span><span class="mi-v">{p.area_conocimiento}</span></div></div>{/if}
              {#if p.sub_area_conocimiento}<div class="mi"><i class="bi bi-lightbulb-off"></i><div><span class="mi-l">Sub-área</span><span class="mi-v">{p.sub_area_conocimiento}</span></div></div>{/if}
              {#if p.alcance}<div class="mi"><i class="bi bi-arrows-fullscreen"></i><div><span class="mi-l">Alcance</span><span class="mi-v">{p.alcance}</span></div></div>{/if}
            </div>

            {#if p.objetivo_general || p.objetivos_especificos}
              <h5 class="msp-h5">Objetivos</h5>
              {#if p.objetivo_general}
                <div class="mi-block"><span class="mi-l">General</span><p class="mi-p">{p.objetivo_general}</p></div>
              {/if}
              {#if p.objetivos_especificos}
                <div class="mi-block"><span class="mi-l">Específicos</span><p class="mi-p">{p.objetivos_especificos}</p></div>
              {/if}
            {/if}

            {#if p.director_nombre || p.director_correo || p.resolucion_aprobacion || p.fecha_aprobacion || p.presupuesto_planificado != null}
              <h5 class="msp-h5">Dirección y aprobación</h5>
              <div class="msp-grid">
                {#if p.director_nombre}<div class="mi"><i class="bi bi-person"></i><div><span class="mi-l">Director/a</span><span class="mi-v">{p.director_nombre}</span></div></div>{/if}
                {#if p.director_correo}<div class="mi"><i class="bi bi-envelope"></i><div><span class="mi-l">Correo</span><span class="mi-v">{p.director_correo}</span></div></div>{/if}
                {#if p.resolucion_aprobacion}<div class="mi full"><i class="bi bi-file-earmark-check"></i><div><span class="mi-l">Resolución</span><span class="mi-v">{p.resolucion_aprobacion}</span></div></div>{/if}
                {#if p.fecha_aprobacion}<div class="mi"><i class="bi bi-calendar2-check"></i><div><span class="mi-l">Fecha aprobación</span><span class="mi-v">{p.fecha_aprobacion}</span></div></div>{/if}
                {#if p.presupuesto_planificado != null}<div class="mi"><i class="bi bi-currency-dollar"></i><div><span class="mi-l">Presupuesto</span><span class="mi-v">$ {p.presupuesto_planificado.toLocaleString('es-EC',{minimumFractionDigits:2})}</span></div></div>{/if}
              </div>
            {/if}

          {:else if modalTab === 'ubicacion'}
            <div class="msp-grid">
              <div class="mi"><i class="bi bi-pin-map"></i><div><span class="mi-l">Provincia</span><span class="mi-v">{p.provincia || '—'}</span></div></div>
              <div class="mi"><i class="bi bi-pin-map-fill"></i><div><span class="mi-l">Cantón</span><span class="mi-v">{p.canton || '—'}</span></div></div>
              {#if p.parroquia}<div class="mi"><i class="bi bi-signpost"></i><div><span class="mi-l">Parroquia</span><span class="mi-v">{p.parroquia}</span></div></div>{/if}
              {#if p.sector}<div class="mi"><i class="bi bi-house"></i><div><span class="mi-l">Sector</span><span class="mi-v">{p.sector}</span></div></div>{/if}
            </div>

          {:else if modalTab === 'cronograma'}
            <div class="msp-grid">
              <div class="mi"><i class="bi bi-calendar3"></i><div><span class="mi-l">Período inicio</span><span class="mi-v">{p.periodo}</span></div></div>
              {#if p.periodo_fin}<div class="mi"><i class="bi bi-calendar3"></i><div><span class="mi-l">Período fin</span><span class="mi-v">{p.periodo_fin}</span></div></div>{/if}
              {#if p.fecha_inicio}<div class="mi"><i class="bi bi-play-circle"></i><div><span class="mi-l">Inicio</span><span class="mi-v">{p.fecha_inicio}</span></div></div>{/if}
              {#if p.fecha_fin_planificada}<div class="mi"><i class="bi bi-flag"></i><div><span class="mi-l">Fin planificado</span><span class="mi-v">{p.fecha_fin_planificada}</span></div></div>{/if}
              {#if p.fecha_fin_real}<div class="mi"><i class="bi bi-flag-fill"></i><div><span class="mi-l">Fin real</span><span class="mi-v">{p.fecha_fin_real}</span></div></div>{/if}
            </div>

          {:else if modalTab === 'documentos'}
            {#if modalDocsLoad}
              <div class="msp-empty"><i class="bi bi-arrow-repeat spin"></i> Cargando documentos...</div>
            {:else if !modalDocs.length}
              <div class="msp-empty">
                <i class="bi bi-folder2-open" style="font-size:2rem;color:#ccc;display:block;margin-bottom:8px"></i>
                Este proyecto no tiene documentos cargados.
              </div>
            {:else}
              <ul class="msp-docs">
                {#each modalDocs as d}
                  {@const ext = (d.nombre?.split('.').pop() || '').toLowerCase()}
                  {@const isPdf = ext === 'pdf'}
                  {@const kb = d.tamanio_kb ? (d.tamanio_kb > 1024 ? (d.tamanio_kb/1024).toFixed(1)+' MB' : d.tamanio_kb+' KB') : ''}
                  <li class="msp-doc">
                    <i class="bi bi-file-earmark-{isPdf ? 'pdf' : (['jpg','jpeg','png','gif','webp'].includes(ext) ? 'image' : (['doc','docx'].includes(ext) ? 'word' : (['xls','xlsx'].includes(ext) ? 'excel' : 'text')))}"></i>
                    <div class="msp-doc-info">
                      <span class="msp-doc-name" title={d.nombre}>{d.nombre}</span>
                      <span class="msp-doc-meta">{d.tipo}{kb ? ' · '+kb : ''}</span>
                    </div>
                    <div class="msp-doc-acts">
                      <button class="msp-doc-btn" onclick={() => docAbierto = { url:d.url, nombre:d.nombre, extension:ext }} title="Ver aquí">
                        <i class="bi bi-eye"></i>
                      </button>
                      <a class="msp-doc-btn" href={d.url} target="_blank" rel="noopener" title="Abrir en nueva pestaña">
                        <i class="bi bi-box-arrow-up-right"></i>
                      </a>
                    </div>
                  </li>
                {/each}
              </ul>
            {/if}

          {:else if modalTab === 'notas'}
            {#if p.ods}
              <div class="mi-block"><span class="mi-l">ODS</span><p class="mi-p">{p.ods}</p></div>
            {/if}
            {#if p.motivo_detencion}
              <div class="mi-block warn"><span class="mi-l">Motivo detención</span><p class="mi-p">{p.motivo_detencion}</p></div>
            {/if}
            {#if p.observaciones}
              <div class="mi-block"><span class="mi-l">Observaciones</span><p class="mi-p">{p.observaciones}</p></div>
            {/if}
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- LIGHTBOX FOTOS -->
  {#if lightboxAbierto && fotos.length}
    <div class="lightbox" onclick={() => lightboxAbierto = false}>
      <button class="lb-close"><i class="bi bi-x-lg"></i></button>
      <img src={fotos[fotoActiva]} alt="Foto {fotoActiva+1}" onclick={(e) => e.stopPropagation()} />
      {#if fotos.length > 1}
        <button class="lb-nav prev" onclick={(e) => { e.stopPropagation(); fotoActiva = (fotoActiva - 1 + fotos.length) % fotos.length; }}>
          <i class="bi bi-chevron-left"></i>
        </button>
        <button class="lb-nav next" onclick={(e) => { e.stopPropagation(); fotoActiva = (fotoActiva + 1) % fotos.length; }}>
          <i class="bi bi-chevron-right"></i>
        </button>
        <span class="lb-counter">{fotoActiva+1} / {fotos.length}</span>
      {/if}
    </div>
  {/if}

  <!-- VISOR DE DOCUMENTOS -->
  {#if docAbierto}
    <div class="doc-viewer" onclick={() => docAbierto = null}>
      <div class="dv-box" onclick={(e) => e.stopPropagation()}>
        <header class="dv-head">
          <span title={docAbierto.nombre}><i class="bi bi-file-earmark"></i> {docAbierto.nombre}</span>
          <div class="dv-acts">
            <a href={docAbierto.url} target="_blank" rel="noopener" class="dv-btn" title="Abrir aparte"><i class="bi bi-box-arrow-up-right"></i></a>
            <a href={docAbierto.url} download class="dv-btn" title="Descargar"><i class="bi bi-download"></i></a>
            <button class="dv-btn" onclick={() => docAbierto = null} title="Cerrar"><i class="bi bi-x-lg"></i></button>
          </div>
        </header>
        <div class="dv-body">
          {#if ['jpg','jpeg','png','gif','webp'].includes(docAbierto.extension)}
            <img src={docAbierto.url} alt={docAbierto.nombre} />
          {:else if docAbierto.extension === 'pdf'}
            <iframe
              src={docAbierto.url + (docAbierto.url.includes('?') ? '&' : '?') + '_=' + Date.now() + '#toolbar=1&navpanes=0'}
              title={docAbierto.nombre}
            ></iframe>
          {:else}
            <div class="dv-empty">
              <i class="bi bi-file-earmark-arrow-down"></i>
              <p>Este tipo de archivo (.{docAbierto.extension}) no se puede previsualizar aquí.</p>
              <a href={docAbierto.url} download class="dv-download"><i class="bi bi-download"></i> Descargar</a>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
{/if}

<style>
/* ── LAYOUT ── */
.mapa-layout {
  display: flex;
  height: calc(100vh - 56px - 36px - 37px);
  overflow: hidden;
  padding: 12px 12px 12px 4px;
}

/* ── PANEL PRINCIPAL ── */
.mapa-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,.10);
  background: #fff;
  overflow: hidden;
}
/* ── FILTROS rediseñados ── */
.filtros-bar {
  background: #fff;
  border-bottom: 1px solid var(--borde);
  padding: 10px 14px;
  border-radius: 16px 16px 0 0;
}
.filtros-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.fsel {
  border: 1.5px solid var(--borde);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: .8rem;
  font-family: inherit;
  font-weight: 600;
  color: #444;
  background: #fafafa;
  outline: none;
  cursor: pointer;
  transition: border-color .2s, background .2s;
  appearance: auto;
  min-width: 130px;
}
.fsel:focus, .fsel:hover { border-color: var(--verde); background: #fff; }
.fsel-sm { min-width: 90px; }

/* Buscador con ícono */
.buscar-wrap {
  display: flex; align-items: center; gap: 7px;
  border: 1.5px solid var(--borde); border-radius: 20px;
  padding: 6px 14px; background: #fafafa;
  transition: border-color .2s;
}
.buscar-wrap:focus-within { border-color: var(--verde); background: #fff; }
.buscar-ico { color: #9999bb; font-size: .85rem; flex-shrink: 0; }
.fbuscar {
  border: none; background: transparent; outline: none;
  font-size: .8rem; font-family: inherit; font-weight: 600;
  color: #444; width: 140px;
}

.factions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.total-badge {
  background: var(--verde-claro); color: var(--verde);
  font-size: .75rem; font-weight: 800;
  padding: 4px 12px; border-radius: 20px; border: 1px solid #c3e6b0;
  white-space: nowrap;
}
.btn-limpiar {
  background: #fff; border: 1.5px solid var(--borde); border-radius: 20px;
  padding: 6px 16px; font-size: .8rem; font-weight: 700; color: #555;
  cursor: pointer; transition: border-color .2s; font-family: inherit;
}
.btn-limpiar:hover { border-color: #aaa; }
.btn-filtrar {
  background: var(--verde); border: none; border-radius: 20px;
  padding: 7px 20px; font-size: .8rem; font-weight: 800;
  color: #fff; cursor: pointer; transition: background .2s; font-family: inherit;
}
.btn-filtrar:hover { background: #155e04; }

/* ── MAPA ── */
:global(#map) { flex: 1; width: 100%; min-height: 300px; }
:global(.leaflet-container) { font-family: 'Nunito', sans-serif; }
:global(.leaflet-tooltip) { font-family: 'Nunito', sans-serif; font-weight: 700; font-size: .78rem; }

/* ── Leyenda NBI ── */
:global(.nbi-leyenda) {
  background: rgba(255,255,255,.95) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  font-size: .73rem;
  font-family: 'Nunito', sans-serif;
  box-shadow: 0 4px 16px rgba(0,0,0,.18) !important;
  line-height: 1.9;
  z-index: 1000 !important;
  border: 1px solid #e0e0e0;
}
:global(.nbi-leyenda b) { display:block; font-size:.72rem; color:#333; margin-bottom:4px; font-weight:800; }
:global(.nbi-leyenda div) { display:flex; align-items:center; gap:7px; }
:global(.nbi-leyenda span) { display:inline-block; width:13px; height:13px; border-radius:3px; flex-shrink:0; }

/* Botón Quevedo */
.btn-quevedo {
  display:inline-flex;align-items:center;gap:6px;
  background:#fff;border:1.5px solid var(--verde);color:var(--verde);
  border-radius:20px;padding:6px 14px;font-size:.78rem;font-weight:800;
  cursor:pointer;font-family:inherit;transition:background .18s,color .18s;
}
.btn-quevedo:hover { background:var(--verde);color:#fff; }
.btn-quevedo i { font-size:.85rem; }

/* Switch "Toda la capa" */
.nbi-switch {
  display:inline-flex;align-items:center;gap:8px;cursor:pointer;
  padding:5px 10px;border-radius:20px;background:#fafafa;border:1.5px solid var(--borde);
}
.nbi-switch input { display:none; }
.ns-slider {
  width:32px;height:18px;background:#ccc;border-radius:20px;position:relative;transition:background .18s;
}
.ns-slider::after {
  content:'';position:absolute;top:2px;left:2px;width:14px;height:14px;
  background:#fff;border-radius:50%;transition:transform .18s;box-shadow:0 1px 3px rgba(0,0,0,.3);
}
.nbi-switch input:checked ~ .ns-slider { background:var(--verde); }
.nbi-switch input:checked ~ .ns-slider::after { transform:translateX(14px); }
.ns-label { font-size:.75rem;font-weight:700;color:#555; }

/* Aviso NBI en sidebar */
.nbi-aviso {
  margin-top: 6px;
  font-size: .68rem;
  color: #888;
  background: #f5f5f5;
  border-radius: 6px;
  padding: 5px 8px;
  line-height: 1.4;
}

/* ── MODAL ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: #fff;
  border-radius: 18px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
  position: relative;
  animation: pop .2s ease;
}
.modal-box.wide { max-width: 880px; }
@keyframes pop { from { transform: scale(.92); opacity:0; } to { transform: scale(1); opacity:1; } }

.modal-close {
  position: absolute;
  top: 12px; right: 12px;
  background: rgba(0,0,0,.4);
  border: none;
  border-radius: 50%;
  width: 32px; height: 32px;
  color: #fff;
  font-size: .9rem;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  z-index: 1;
  transition: background .2s;
}
.modal-close:hover { background: rgba(0,0,0,.6); }

/* ── Split 2 columnas ── */
.modal-split { display:grid;grid-template-columns:280px 1fr;height:min(90vh,620px); }
@media (max-width:720px) { .modal-split { grid-template-columns:1fr;height:90vh; } }

.msp-left {
  display:flex;flex-direction:column;
  background:#f9fafb;border-right:1px solid #ececec;
  padding:0;overflow:hidden;
}
.msp-foto { position:relative;width:100%;height:180px;background:#eee;flex-shrink:0;overflow:hidden; }
.msp-foto img { width:100%;height:100%;object-fit:cover;display:block; }
.msp-fallback {
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;
  background:#f6f7f4;color:#b8b8b8;
}
.msp-fallback i { font-size:2.2rem; }
.msp-fallback small { font-size:.7rem;font-weight:700; }

.msp-expand, .msp-nav {
  position:absolute;background:rgba(0,0,0,.45);color:#fff;border:none;border-radius:50%;
  width:28px;height:28px;display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:.75rem;transition:background .18s;
}
.msp-expand:hover, .msp-nav:hover { background:rgba(0,0,0,.7); }
.msp-expand { top:8px;right:8px; }
.msp-nav.prev { top:50%;left:6px;transform:translateY(-50%); }
.msp-nav.next { top:50%;right:6px;transform:translateY(-50%); }
.msp-counter {
  position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.55);color:#fff;font-size:.68rem;font-weight:700;
  padding:2px 8px;border-radius:10px;
}

.msp-head { padding:14px 16px 10px;border-bottom:1px solid #f0f0f0; }
.msp-title { font-size:.9rem;font-weight:900;color:#1a1a1a;line-height:1.3;margin:6px 0 3px; }
.msp-code  { font-size:.68rem;font-weight:700;color:var(--gris);display:block; }

.msp-thumbs {
  display:flex;gap:5px;padding:8px 12px;border-bottom:1px solid #f0f0f0;
  overflow-x:auto;
}
.msp-thumbs::-webkit-scrollbar { height:4px; }
.msp-thumb {
  padding:0;border:2px solid transparent;border-radius:6px;background:none;cursor:pointer;
  flex-shrink:0;transition:border-color .18s;
}
.msp-thumb:hover { border-color:#c3e6b0; }
.msp-thumb.active { border-color:var(--verde); }
.msp-thumb img { width:40px;height:40px;object-fit:cover;border-radius:4px;display:block; }

.msp-tabs { display:flex;flex-direction:column;padding:8px 0;flex:1;overflow-y:auto; }
.msp-tab {
  display:flex;align-items:center;gap:10px;
  padding:9px 16px;font-size:.78rem;font-weight:700;color:#555;
  background:none;border:none;border-left:3px solid transparent;
  cursor:pointer;font-family:inherit;text-align:left;
  transition:background .14s,color .14s,border-color .14s;
}
.msp-tab i { font-size:.9rem;color:#9999bb; }
.msp-tab:hover { background:#fff;color:var(--verde); }
.msp-tab:hover i { color:var(--verde); }
.msp-tab.active { background:#fff;color:var(--verde);border-left-color:var(--verde);font-weight:800; }
.msp-tab.active i { color:var(--verde); }

.msp-right {
  padding:20px 22px;overflow-y:auto;
}
.msp-right::-webkit-scrollbar { width:6px; }
.msp-right::-webkit-scrollbar-thumb { background:#ccc;border-radius:6px; }

.msp-desc {
  font-size:.82rem;color:#555;line-height:1.55;
  margin:0 0 14px;padding:10px 12px;background:#fafafa;
  border-left:3px solid var(--verde);border-radius:0 8px 8px 0;
}
.msp-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px 16px; }
.msp-grid .mi.full { grid-column:1/-1; }
@media (max-width:520px) { .msp-grid { grid-template-columns:1fr; } }
.msp-empty { grid-column:1/-1;color:#999;font-size:.82rem;text-align:center;padding:30px 20px; }
.msp-h5 { font-size:.65rem;font-weight:800;color:var(--verde);text-transform:uppercase;
  letter-spacing:.08em;margin:16px 0 8px;padding-bottom:5px;border-bottom:1px solid #f0f0f0; }
.msp-h5:first-child { margin-top:0; }

/* ── Documentos ── */
.msp-docs { list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px; }
.msp-doc {
  display:flex;align-items:center;gap:10px;
  padding:10px 12px;background:#fafafa;border:1px solid #f0f0f0;border-radius:10px;
  transition:border-color .18s,background .18s;
}
.msp-doc:hover { border-color:var(--verde);background:#f7fbf3; }
.msp-doc > i { font-size:1.4rem;color:var(--verde);flex-shrink:0; }
.msp-doc-info { flex:1;min-width:0;display:flex;flex-direction:column;gap:2px; }
.msp-doc-name { font-size:.82rem;font-weight:700;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.msp-doc-meta { font-size:.68rem;color:#888;font-weight:600; }
.msp-doc-acts { display:flex;gap:4px;flex-shrink:0; }
.msp-doc-btn {
  background:#fff;border:1px solid var(--borde);border-radius:8px;
  width:30px;height:30px;display:flex;align-items:center;justify-content:center;
  color:#666;font-size:.8rem;cursor:pointer;text-decoration:none;transition:all .18s;
}
.msp-doc-btn:hover { background:var(--verde);color:#fff;border-color:var(--verde); }

/* ── Lightbox ── */
.lightbox {
  position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:10000;
  display:flex;align-items:center;justify-content:center;padding:40px;
  animation:fadein .2s ease;
}
@keyframes fadein { from{opacity:0} to{opacity:1} }
.lightbox img { max-width:100%;max-height:100%;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,.5); }
.lb-close {
  position:absolute;top:20px;right:20px;background:rgba(255,255,255,.15);color:#fff;
  border:none;border-radius:50%;width:44px;height:44px;font-size:1.1rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background .18s;
}
.lb-close:hover { background:rgba(255,255,255,.28); }
.lb-nav {
  position:absolute;top:50%;transform:translateY(-50%);
  background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:50%;
  width:52px;height:52px;font-size:1.3rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background .18s;
}
.lb-nav:hover { background:rgba(255,255,255,.28); }
.lb-nav.prev { left:24px; } .lb-nav.next { right:24px; }
.lb-counter { position:absolute;bottom:24px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.5);color:#fff;font-size:.85rem;font-weight:700;padding:5px 14px;border-radius:20px; }

/* ── Visor de documentos ── */
.doc-viewer {
  position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:10001;
  display:flex;align-items:center;justify-content:center;padding:24px;
}
.dv-box {
  background:#fff;border-radius:14px;width:100%;max-width:1000px;height:90vh;
  display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.4);
}
.dv-head {
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:12px 18px;background:var(--verde);color:#fff;
}
.dv-head > span {
  display:flex;align-items:center;gap:8px;font-weight:700;font-size:.88rem;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.dv-acts { display:flex;gap:6px;flex-shrink:0; }
.dv-btn {
  background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:8px;
  width:34px;height:34px;display:flex;align-items:center;justify-content:center;
  font-size:.9rem;cursor:pointer;text-decoration:none;transition:background .18s;
}
.dv-btn:hover { background:rgba(255,255,255,.28); }
.dv-body { flex:1;overflow:hidden;background:#f4f4f4;display:flex;align-items:center;justify-content:center; }
.dv-body iframe { width:100%;height:100%;border:none;background:#fff; }
.dv-body img { max-width:100%;max-height:100%;object-fit:contain; }
.dv-empty { text-align:center;padding:40px;color:#666; }
.dv-empty i { font-size:3rem;color:#c8c8c8;display:block;margin-bottom:12px; }
.dv-empty p { font-size:.88rem;margin-bottom:14px; }
.dv-download {
  display:inline-flex;align-items:center;gap:8px;
  background:var(--verde);color:#fff;text-decoration:none;
  padding:9px 20px;border-radius:20px;font-size:.85rem;font-weight:800;
}
.dv-download:hover { background:#155e04; }

.modal-estado {
  display:inline-block;font-size:.62rem;font-weight:800;
  padding:3px 10px;border-radius:20px;
  text-transform:uppercase;letter-spacing:.05em;
}
.mi { display:flex;align-items:flex-start;gap:8px; }
.mi i { color:var(--verde);font-size:.95rem;margin-top:2px;flex-shrink:0; }
.mi > div { display:flex;flex-direction:column;min-width:0; }
.mi-l { font-size:.62rem;color:var(--gris);font-weight:800;text-transform:uppercase;letter-spacing:.05em; }
.mi-v { font-size:.82rem;color:var(--negro);font-weight:600;word-break:break-word; }
.mi-block { margin-bottom:12px; }
.mi-block:last-child { margin-bottom:0; }
.mi-block.warn { background:#fff8e6;border-left:3px solid #f5b400;padding:8px 12px;border-radius:0 6px 6px 0; }
.mi-p { font-size:.82rem;color:#444;line-height:1.55;margin:4px 0 0;white-space:pre-line; }
.modal-title {
  font-size: 1rem;
  font-weight: 900;
  color: var(--negro);
  line-height: 1.3;
  margin-bottom: 4px;
}
.modal-code {
  font-size: .72rem;
  font-weight: 700;
  color: var(--gris);
  display: block;
  margin-bottom: 14px;
}

.modal-grid { display:grid;grid-template-columns:1fr 1fr;gap:10px 14px; }
@media (max-width:520px) { .modal-grid { grid-template-columns:1fr; } }
</style>
