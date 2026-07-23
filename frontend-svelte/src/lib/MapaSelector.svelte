<script>
  import { onMount } from 'svelte';

  // ubicaciones: array bindable de puntos del proyecto.
  // Cada punto: { nombre_lugar, provincia, canton, parroquia, sector, latitud, longitud, es_principal }
  let { ubicaciones = $bindable([]) } = $props();

  let mapEl;
  let map, markersLayer, L;

  // Buscador
  let query = $state('');
  let resultados = $state([]);
  let buscando = $state(false);
  let sinResultados = $state(false);
  let debounceId;

  const CENTRO_EC = [-1.5, -78.5];

  onMount(async () => {
    L = (await import('leaflet')).default;
    map = L.map(mapEl, { zoomControl: true }).setView(CENTRO_EC, 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);

    // Clic en el mapa → coloca un punto nuevo
    map.on('click', async (e) => {
      await agregarPunto(e.latlng.lat, e.latlng.lng);
    });

    redibujar();
  });

  // ── Búsqueda con Nominatim (OpenStreetMap) ──────────────────────
  function onInput() {
    sinResultados = false;
    clearTimeout(debounceId);
    if (query.trim().length < 3) { resultados = []; return; }
    debounceId = setTimeout(buscar, 450);
  }

  async function buscar() {
    buscando = true; resultados = []; sinResultados = false;
    try {
      const url = 'https://nominatim.openstreetmap.org/search'
        + '?format=json&addressdetails=1&limit=6&countrycodes=ec'
        + '&q=' + encodeURIComponent(query.trim());
      const res = await fetch(url, { headers: { 'Accept-Language': 'es' } });
      const data = await res.json();
      resultados = data || [];
      sinResultados = resultados.length === 0;
    } catch {
      sinResultados = true;
    } finally {
      buscando = false;
    }
  }

  function elegirResultado(r) {
    const lat = parseFloat(r.lat), lng = parseFloat(r.lon);
    const a = r.address || {};
    const nombre = r.display_name?.split(',').slice(0, 2).join(',').trim() || 'Ubicación';
    agregarPunto(lat, lng, {
      nombre_lugar: nombre,
      provincia: a.state || a.region || '',
      canton: a.county || a.city || a.town || a.municipality || '',
      parroquia: a.suburb || a.village || a.city_district || '',
      sector: a.neighbourhood || a.hamlet || '',
    });
    query = ''; resultados = [];
    map.setView([lat, lng], 15);
  }

  // ── Agregar / gestionar puntos ──────────────────────────────────
  async function agregarPunto(lat, lng, meta = null) {
    let info = meta;
    if (!info) info = await reverseGeocode(lat, lng);
    const esPrimero = ubicaciones.length === 0;
    ubicaciones = [...ubicaciones, {
      nombre_lugar: info?.nombre_lugar || `Punto ${ubicaciones.length + 1}`,
      provincia: info?.provincia || '',
      canton: info?.canton || '',
      parroquia: info?.parroquia || '',
      sector: info?.sector || '',
      latitud: Number(lat).toFixed(7),
      longitud: Number(lng).toFixed(7),
      es_principal: esPrimero,
    }];
    redibujar();
    map.setView([lat, lng], Math.max(map.getZoom(), 13));
  }

  async function reverseGeocode(lat, lng) {
    try {
      const url = 'https://nominatim.openstreetmap.org/reverse'
        + `?format=json&addressdetails=1&lat=${lat}&lon=${lng}`;
      const res = await fetch(url, { headers: { 'Accept-Language': 'es' } });
      const r = await res.json();
      const a = r.address || {};
      return {
        nombre_lugar: r.display_name?.split(',').slice(0, 2).join(',').trim() || '',
        provincia: a.state || a.region || '',
        canton: a.county || a.city || a.town || a.municipality || '',
        parroquia: a.suburb || a.village || a.city_district || '',
        sector: a.neighbourhood || a.hamlet || '',
      };
    } catch { return null; }
  }

  function quitar(i) {
    const eraPrincipal = ubicaciones[i].es_principal;
    ubicaciones = ubicaciones.filter((_, idx) => idx !== i);
    if (eraPrincipal && ubicaciones.length) ubicaciones[0].es_principal = true;
    ubicaciones = ubicaciones;
    redibujar();
  }

  function marcarPrincipal(i) {
    ubicaciones = ubicaciones.map((u, idx) => ({ ...u, es_principal: idx === i }));
    redibujar();
  }

  function centrarEn(i) {
    const u = ubicaciones[i];
    map.setView([parseFloat(u.latitud), parseFloat(u.longitud)], 15);
  }

  // ── Dibujar marcadores ──────────────────────────────────────────
  function redibujar() {
    if (!markersLayer || !L) return;
    markersLayer.clearLayers();
    ubicaciones.forEach((u, i) => {
      const lat = parseFloat(u.latitud), lng = parseFloat(u.longitud);
      if (isNaN(lat) || isNaN(lng)) return;
      const color = u.es_principal ? '#1b7505' : '#dba112';
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:${color};border:2.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;">
                 <span style="transform:rotate(45deg);color:#fff;font-size:11px;font-weight:800;">${i + 1}</span>
               </div>`,
        iconSize: [22, 22], iconAnchor: [11, 22],
      });
      const marker = L.marker([lat, lng], { icon, draggable: true });
      marker.on('dragend', (e) => {
        const p = e.target.getLatLng();
        ubicaciones[i].latitud = p.lat.toFixed(7);
        ubicaciones[i].longitud = p.lng.toFixed(7);
        ubicaciones = ubicaciones;
      });
      marker.bindTooltip(u.nombre_lugar || `Punto ${i + 1}`, { direction: 'top', offset: [0, -20] });
      markersLayer.addLayer(marker);
    });
  }

  // Redibuja cuando cambia la lista desde fuera
  $effect(() => { ubicaciones; redibujar(); });
</script>

<div class="ms-wrap">
  <!-- BUSCADOR -->
  <div class="ms-search">
    <div class="ms-search-box">
      <i class="bi bi-search"></i>
      <input
        bind:value={query}
        oninput={onInput}
        placeholder="Buscar un lugar: 'centro de Quevedo', 'hospital IESS', 'GAD Mocache'..."
      />
      {#if buscando}<i class="bi bi-arrow-repeat spin"></i>{/if}
    </div>
    {#if resultados.length}
      <ul class="ms-results">
        {#each resultados as r}
          <li onclick={() => elegirResultado(r)}>
            <i class="bi bi-geo-alt"></i>
            <span>{r.display_name}</span>
          </li>
        {/each}
      </ul>
    {:else if sinResultados}
      <div class="ms-noresult">Sin resultados. Prueba con otro nombre o haz clic directo en el mapa.</div>
    {/if}
  </div>

  <!-- MAPA -->
  <div class="ms-map" bind:this={mapEl}></div>
  <p class="ms-hint"><i class="bi bi-info-circle"></i> Busca un lugar o haz clic en el mapa para agregar un punto. Arrastra un marcador para ajustarlo.</p>

  <!-- LISTA DE UBICACIONES -->
  {#if ubicaciones.length}
    <div class="ms-list">
      <div class="ms-list-hdr">
        <span>{ubicaciones.length} {ubicaciones.length === 1 ? 'ubicación' : 'ubicaciones'}</span>
        <span class="ms-list-hint">La estrella marca la ubicación principal</span>
      </div>
      {#each ubicaciones as u, i}
        <div class="ms-item" class:principal={u.es_principal}>
          <span class="ms-num" style="background:{u.es_principal ? '#1b7505' : '#dba112'}">{i + 1}</span>
          <div class="ms-item-body">
            <input class="ms-item-nom" bind:value={u.nombre_lugar} placeholder="Nombre del lugar" />
            <div class="ms-item-meta">
              {#if u.canton}<span>{u.canton}</span>{/if}
              {#if u.provincia}<span>· {u.provincia}</span>{/if}
              <span class="ms-coords">· {u.latitud}, {u.longitud}</span>
            </div>
          </div>
          <button type="button" class="ms-act" title="Centrar en el mapa" onclick={() => centrarEn(i)}>
            <i class="bi bi-crosshair"></i>
          </button>
          <button type="button" class="ms-act" class:on={u.es_principal} title="Marcar como principal" onclick={() => marcarPrincipal(i)}>
            <i class="bi bi-star{u.es_principal ? '-fill' : ''}"></i>
          </button>
          <button type="button" class="ms-act danger" title="Quitar" onclick={() => quitar(i)}>
            <i class="bi bi-trash"></i>
          </button>
        </div>
      {/each}
    </div>
  {:else}
    <div class="ms-empty">
      <i class="bi bi-geo-alt"></i>
      Aún no hay ubicaciones. Busca un lugar o haz clic en el mapa.
    </div>
  {/if}
</div>

<style>
  .ms-wrap { display: flex; flex-direction: column; gap: 10px; position: relative; }

  /* El buscador debe quedar POR ENCIMA del mapa para poder elegir resultados */
  .ms-search { position: relative; z-index: 1000; }
  .ms-search-box {
    display: flex; align-items: center; gap: 9px;
    border: 1.5px solid var(--borde); border-radius: 12px;
    padding: 9px 14px; background: #fafafa; transition: border-color .2s, background .2s;
  }
  .ms-search-box:focus-within { border-color: var(--verde); background: #fff; }
  .ms-search-box > .bi-search { color: #9999bb; font-size: .95rem; }
  .ms-search-box input {
    flex: 1; border: none; background: transparent; outline: none;
    font-size: .88rem; font-family: inherit; font-weight: 600; color: #333;
  }
  .ms-results {
    list-style: none; position: absolute; top: calc(100% + 4px); left: 0; right: 0;
    background: #fff; border: 1px solid var(--borde); border-radius: 12px;
    box-shadow: 0 8px 28px rgba(0,0,0,.14); z-index: 1200; overflow: hidden; max-height: 260px; overflow-y: auto;
  }
  .ms-results li {
    display: flex; align-items: flex-start; gap: 9px; padding: 9px 14px;
    font-size: .82rem; color: #444; cursor: pointer; border-bottom: 1px solid #f2f2f2; line-height: 1.35;
  }
  .ms-results li:last-child { border-bottom: none; }
  .ms-results li:hover { background: var(--verde-claro); color: var(--verde); }
  .ms-results li i { color: var(--dorado); margin-top: 2px; flex-shrink: 0; }
  .ms-noresult { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: #fff8e6;
    border: 1px solid #f0e0b0; border-radius: 10px; padding: 8px 14px; font-size: .78rem; color: #8a6d1a; z-index: 1200; }

  /* z-index:0 crea un contexto de apilamiento que CONTIENE los z-index internos de
     Leaflet (que llegan a ~1000), evitando que el mapa sobresalga por encima del footer. */
  .ms-map { width: 100%; height: 340px; border-radius: 12px; overflow: hidden;
    border: 1px solid var(--borde); position: relative; z-index: 0; }
  .ms-hint { font-size: .74rem; color: var(--gris); font-weight: 600; display: flex; align-items: center; gap: 6px; }

  .ms-list { display: flex; flex-direction: column; gap: 6px; }
  .ms-list-hdr { display: flex; align-items: center; justify-content: space-between; font-size: .78rem; font-weight: 800; color: var(--negro); padding: 2px 2px 4px; }
  .ms-list-hint { font-size: .68rem; font-weight: 600; color: var(--gris); }
  .ms-item {
    display: flex; align-items: center; gap: 10px;
    border: 1.5px solid var(--borde); border-radius: 12px; padding: 8px 10px; background: #fff;
  }
  .ms-item.principal { border-color: #cfe6c2; background: #f6fbf2; }
  .ms-num { width: 24px; height: 24px; border-radius: 50%; color: #fff; font-size: .74rem; font-weight: 800;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .ms-item-body { flex: 1; min-width: 0; }
  .ms-item-nom { width: 100%; border: none; background: transparent; outline: none; font-size: .85rem;
    font-weight: 700; color: #222; font-family: inherit; padding: 2px 0; }
  .ms-item-nom:focus { border-bottom: 1.5px solid var(--verde); }
  .ms-item-meta { font-size: .7rem; color: var(--gris); font-weight: 600; display: flex; flex-wrap: wrap; gap: 4px; }
  .ms-coords { color: #b0b0b0; font-family: monospace; font-size: .66rem; }
  .ms-act { background: none; border: none; color: #999; font-size: .95rem; width: 30px; height: 30px;
    border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .ms-act:hover { background: #f0f0f0; color: #555; }
  .ms-act.on { color: var(--dorado); }
  .ms-act.danger:hover { background: #fdecec; color: #dc3545; }

  .ms-empty { display: flex; align-items: center; gap: 9px; justify-content: center; padding: 16px;
    background: #fafbfa; border-radius: 12px; font-size: .82rem; color: var(--gris); font-weight: 600; }
  .ms-empty i { font-size: 1.1rem; color: #ccc; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin .7s linear infinite; color: var(--verde); }
</style>
