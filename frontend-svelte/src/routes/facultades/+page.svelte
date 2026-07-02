<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

    let facultades = $state([]);
  let carreras   = $state([]);
  let loading    = $state(true);
  let tab        = $state('facultades');
  let q          = $state('');
  let toast      = $state('');

  onMount(async () => {
    try {
      [facultades, carreras] = await Promise.all([
        fetchAPI('/api/facultades/'),
        fetchAPI('/api/carreras/'),
      ]);
    } finally { loading = false; }
  });

  let filtFacs = $derived(facultades.filter(f =>
    !q || f.nombre.toLowerCase().includes(q.toLowerCase()) || (f.codigo || '').toLowerCase().includes(q.toLowerCase())
  ));

  let filtCarr = $derived(carreras.filter(c =>
    !q || c.nombre.toLowerCase().includes(q.toLowerCase()) || (c.codigo || '').toLowerCase().includes(q.toLowerCase())
  ));

  async function toggleFac(id, activo) {
    await fetch(`/api/facultades/${id}/`, {
      method:'PUT', credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({activo: !activo}),
    });
    facultades = facultades.map(f => f.id_facultad === id ? {...f, activo: !activo} : f);
    toast = activo ? 'Facultad desactivada' : 'Facultad activada';
    setTimeout(() => toast = '', 3000);
  }

  async function toggleCarr(id, activo) {
    await fetch(`/api/carreras/${id}/`, {
      method:'PUT', credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({activo: !activo}),
    });
    carreras = carreras.map(c => c.id_carrera === id ? {...c, activo: !activo} : c);
    toast = activo ? 'Carrera desactivada' : 'Carrera activada';
    setTimeout(() => toast = '', 3000);
  }
</script>

<svelte:head><title>Facultades y Carreras — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Facultades y Carreras</span><span class="sep">/</span>
  </nav>
  {#if tab === 'carreras'}
    <a href="/carreras/nueva" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nueva carrera</a>
  {/if}
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-mortarboard-fill"></i> Facultades y Carreras</h2>
      <p class="page-sub">Estructura académica de la UTEQ</p>
    </div>
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar..." />
    </div>
  </div>

  <!-- TABS -->
  <div class="tabs">
    <button class="tab" class:active={tab === 'facultades'} onclick={() => { tab='facultades'; q=''; }}>
      <i class="bi bi-bank"></i> Facultades ({facultades.length})
    </button>
    <button class="tab" class:active={tab === 'carreras'} onclick={() => { tab='carreras'; q=''; }}>
      <i class="bi bi-book"></i> Carreras ({carreras.length})
    </button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
  {:else if tab === 'facultades'}
    <div class="table-card">
      <table>
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Nombre corto</th><th>Campus</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each filtFacs as f}
            <tr>
              <td><span class="code">{f.codigo}</span></td>
              <td class="nombre-p">{f.nombre}</td>
              <td class="txt-sm">{f.nombre_corto || '—'}</td>
              <td class="txt-sm">{f.campus || '—'}</td>
              <td>
                <span class="badge" class:activo={f.activo} class:inactivo={!f.activo}>
                  {f.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td class="acciones">
                <a href="/facultades/{f.id_facultad}" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion {f.activo ? 'danger':'success'}"
                  onclick={() => toggleFac(f.id_facultad, f.activo)}>
                  <i class="bi bi-{f.activo ? 'toggle-on':'toggle-off'}"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if filtFacs.length === 0}
            <tr><td colspan="6" class="empty">No se encontraron facultades</td></tr>
          {/if}
        </tbody>
      </table>
    </div>

  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Facultad</th><th>Horas Vinc.</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each filtCarr as c}
            <tr>
              <td><span class="code">{c.codigo || '—'}</span></td>
              <td>{c.nombre}</td>
              <td><span class="fac-b">{c.facultad_nombre}</span></td>
              <td class="txt-sm center">{c.horas_vinculacion || '—'}h</td>
              <td>
                <span class="badge" class:activo={c.activo} class:inactivo={!c.activo}>
                  {c.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td class="acciones">
                <a href="/carreras/{c.id_carrera}" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion {c.activo ? 'danger':'success'}"
                  onclick={() => toggleCarr(c.id_carrera, c.activo)}>
                  <i class="bi bi-{c.activo ? 'toggle-on':'toggle-off'}"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if filtCarr.length === 0}
            <tr><td colspan="6" class="empty">No se encontraron carreras</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
  {/if}

  <div class="total">
    {tab === 'facultades' ? filtFacs.length + ' facultad(es)' : filtCarr.length + ' carrera(s)'}
  </div>
</div>

{#if toast}<div class="toast">{toast}</div>{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

.tabs { display:flex;gap:4px;margin-bottom:16px; }
.tab {
  background:#fff;border:1.5px solid var(--borde);border-radius:9px;
  padding:8px 18px;font-size:.83rem;font-weight:700;font-family:inherit;
  color:#666;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:6px;
}
.tab:hover { border-color:var(--verde);color:var(--verde); }
.tab.active { background:var(--verde);color:#fff;border-color:var(--verde); }

.fac-b { font-size:.75rem;font-weight:700;color:var(--verde);background:var(--verde-claro);padding:2px 8px;border-radius:6px; }
.txt-sm { font-size:.78rem; }
.center { text-align:center; }
.acciones { display:flex;gap:6px; }
.nombre-p { font-weight:700; }
</style>
