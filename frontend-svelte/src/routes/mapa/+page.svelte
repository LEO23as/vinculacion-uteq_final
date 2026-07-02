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

  // Capa NBI (estado en store compartido con layout)
  let nbiAviso    = $state('');
  let nbiByCanton = null;
  let nbiLayer    = null;
  let nbiLeyenda  = null;

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
      marker.on('click', () => { proySeleccionado = p; });
      marker.bindTooltip(p.nombre_corto, { direction:'top', offset:[0,-10] });
      markersLayer.addLayer(marker);
    });
  }

  // ── Capa NBI/INEC ───────────────────────────────────────────
  function getNBIColor(pct) {
    if (pct >= 80) return '#800026';
    if (pct >= 65) return '#bd0026';
    if (pct >= 50) return '#e31a1c';
    if (pct >= 40) return '#fc4e2a';
    if (pct >= 30) return '#fd8d3c';
    if (pct >= 20) return '#feb24c';
    return '#fed976';
  }

  async function cargarSectoresViewport() {
    const L = window._L;
    if (!map || !nbiByCanton) return;
    const zoom = map.getZoom();
    if (zoom < 11) {
      nbiAviso = 'Acércate más (zoom ≥ 11) para ver la capa NBI por sector.';
      return;
    }
    nbiAviso = 'Cargando sectores INEC…';
    const b = map.getBounds();
    const geom = `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`;
    const url = `https://idgn.ecuadorencifras.gob.ec/server/rest/services/WMS_MGN2025/MapServer/1/query?geometry=${geom}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=sec,parroquia&returnGeometry=true&f=geojson`;
    try {
      const res = await fetch(url);
      const gj  = await res.json();
      if (nbiLayer) { map.removeLayer(nbiLayer); nbiLayer = null; }
      nbiLayer = L.geoJSON(gj, {
        style: (feature) => {
          const sec   = feature.properties?.sec || '';
          const dpa   = sec.substring(0, 4);
          const entry = nbiByCanton[dpa];
          const pct   = entry?.nbi_pct ?? null;
          return {
            weight: 0.3, opacity: 0.6, color: '#555',
            fillOpacity: pct !== null ? 0.65 : 0,
            fillColor: pct !== null ? getNBIColor(pct) : 'transparent',
          };
        },
        onEachFeature: (feature, layer) => {
          const sec   = feature.properties?.sec || '';
          const parr  = feature.properties?.parroquia || '';
          const dpa   = sec.substring(0, 4);
          const entry = nbiByCanton[dpa];
          if (entry) {
            layer.bindTooltip(
              `<b>Sector:</b> ${sec}<br><b>Cantón:</b> ${entry.canton}<br><b>Provincia:</b> ${entry.provincia}<br><b>NBI 2022:</b> ${entry.nbi_pct}%`,
              { sticky: true, direction: 'top' }
            );
          }
        },
      }).addTo(map);
      nbiAviso = `${gj.features?.length ?? 0} sectores cargados (NBI Censo 2022)`;
    } catch {
      nbiAviso = 'Error al cargar sectores INEC.';
    }
  }

  function agregarLeyendaNBI() {
    const L = window._L;
    if (nbiLeyenda) return;
    nbiLeyenda = L.control({ position: 'bottomright' });
    nbiLeyenda.onAdd = () => {
      const div = L.DomUtil.create('div', 'nbi-leyenda');
      div.innerHTML = `
        <b>NBI 2022 (%)</b>
        <div><span style="background:#800026"></span>≥ 80%</div>
        <div><span style="background:#bd0026"></span>65 – 79%</div>
        <div><span style="background:#e31a1c"></span>50 – 64%</div>
        <div><span style="background:#fc4e2a"></span>40 – 49%</div>
        <div><span style="background:#fd8d3c"></span>30 – 39%</div>
        <div><span style="background:#feb24c"></span>20 – 29%</div>
        <div><span style="background:#fed976"></span>&lt; 20%</div>
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
      await cargarSectoresViewport();
      agregarLeyendaNBI();
      map.on('moveend', cargarSectoresViewport);
    } else {
      map.off('moveend', cargarSectoresViewport);
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
  <div class="modal-overlay" onclick={() => proySeleccionado = null}>
    <div class="modal-box" onclick={(e) => e.stopPropagation()}>
      <button class="modal-close" onclick={() => proySeleccionado = null}>
        <i class="bi bi-x-lg"></i>
      </button>

      {#if proySeleccionado.foto_url}
        <img src={proySeleccionado.foto_url} alt="Foto" class="modal-foto" />
      {:else}
        <div class="modal-foto-placeholder">
          <i class="bi bi-image"></i>
        </div>
      {/if}

      <div class="modal-body">
        <div class="modal-estado" style="background:{proySeleccionado.color}20;color:{proySeleccionado.color}">
          {proySeleccionado.estado?.replace('_',' ')}
        </div>
        <h2 class="modal-title">{proySeleccionado.nombre_corto}</h2>
        <span class="modal-code">{proySeleccionado.codigo}</span>

        <div class="modal-grid">
          <div class="modal-item">
            <i class="bi bi-mortarboard-fill"></i>
            <div>
              <span class="mi-label">Facultad</span>
              <span class="mi-val">{proySeleccionado.facultad}</span>
            </div>
          </div>
          <div class="modal-item">
            <i class="bi bi-book-fill"></i>
            <div>
              <span class="mi-label">Carrera</span>
              <span class="mi-val">{proySeleccionado.carrera}</span>
            </div>
          </div>
          <div class="modal-item">
            <i class="bi bi-calendar3"></i>
            <div>
              <span class="mi-label">Período</span>
              <span class="mi-val">{proySeleccionado.periodo}</span>
            </div>
          </div>
          <div class="modal-item">
            <i class="bi bi-geo-alt-fill"></i>
            <div>
              <span class="mi-label">Ubicación</span>
              <span class="mi-val">{proySeleccionado.canton}, {proySeleccionado.provincia}</span>
            </div>
          </div>
          {#if proySeleccionado.fecha_inicio}
          <div class="modal-item">
            <i class="bi bi-calendar-check"></i>
            <div>
              <span class="mi-label">Inicio</span>
              <span class="mi-val">{proySeleccionado.fecha_inicio}</span>
            </div>
          </div>
          {/if}
          {#if proySeleccionado.ods}
          <div class="modal-item full">
            <i class="bi bi-globe2"></i>
            <div>
              <span class="mi-label">ODS</span>
              <span class="mi-val">{proySeleccionado.ods}</span>
            </div>
          </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
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
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
  position: relative;
  animation: pop .2s ease;
}
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

.modal-foto {
  width: 100%;
  height: 180px;
  object-fit: cover;
}
.modal-foto-placeholder {
  width: 100%;
  height: 120px;
  background: var(--verde-claro);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c3e6b0;
  font-size: 2.5rem;
}

.modal-body { padding: 18px 20px 22px; }

.modal-estado {
  display: inline-block;
  font-size: .7rem;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: .05em;
}
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

.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.modal-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.modal-item.full { grid-column: 1/-1; }
.modal-item i {
  color: var(--verde);
  font-size: .95rem;
  margin-top: 2px;
  flex-shrink: 0;
}
.mi-label {
  font-size: .65rem;
  color: var(--gris);
  font-weight: 700;
  text-transform: uppercase;
  display: block;
}
.mi-val {
  font-size: .82rem;
  color: var(--negro);
  font-weight: 600;
  display: block;
}
</style>
