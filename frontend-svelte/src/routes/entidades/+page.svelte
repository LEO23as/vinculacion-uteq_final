<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

    let items = $state([]);
  let tipos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let filtTipo = $state('');
  let filtEstado = $state('');
  let toast = $state('');

  onMount(async () => {
    try {
      const [ents, tipoData] = await Promise.all([
        fetchAPI('/api/entidades/'),
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
      ]);
      items = ents;
      tipos = tipoData.tipos || [];
    } finally { loading = false; }
  });

  let filtered = $derived(items.filter(e => {
    const matchQ = !q ||
      e.nombre.toLowerCase().includes(q.toLowerCase()) ||
      (e.ruc || '').includes(q);
    const matchT = !filtTipo || String(e.id_tipo) === filtTipo;
    const matchE = !filtEstado ||
      (filtEstado === 'activa' && e.activo) ||
      (filtEstado === 'inactiva' && !e.activo);
    return matchQ && matchT && matchE;
  }));

  function limpiar() { q = ''; filtTipo = ''; filtEstado = ''; }

  async function toggle(id, activo) {
    await fetch(`/api/entidades/${id}/`, {
      method:'PUT', credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({activo: !activo}),
    });
    items = items.map(e => e.id_entidad === id ? {...e, activo: !activo} : e);
    toast = activo ? 'Entidad desactivada' : 'Entidad activada';
    setTimeout(() => toast = '', 3000);
  }
</script>

<svelte:head><title>Entidades — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Entidades</span><span class="sep">/</span>
  </nav>
  <a href="/entidades/nueva" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nueva entidad</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-building"></i> Entidades Cooperantes</h2>
      <p class="page-sub">GADs, hospitales, escuelas, empresas y más</p>
    </div>
  </div>

  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar por nombre..." />
    </div>
    <select bind:value={filtTipo}>
      <option value="">Todos los tipos</option>
      {#each tipos as t}
        <option value={String(t.id_tipo)}>{t.nombre}</option>
      {/each}
    </select>
    <select bind:value={filtEstado}>
      <option value="">Todos los estados</option>
      <option value="activa">Activas</option>
      <option value="inactiva">Inactivas</option>
    </select>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr><th>Nombre</th><th>Tipo</th><th>Representante</th><th>Ubicación</th><th>RUC</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each filtered as e}
            <tr>
              <td>
                <span class="nombre-p">{e.nombre}</span>
                {#if e.nombre_corto}<span class="nombre-s">{e.nombre_corto}</span>{/if}
              </td>
              <td><span class="tipo-badge">{e.tipo_nombre}</span></td>
              <td>
                {e.representante_legal || '—'}
                {#if e.cargo_representante}<span class="sec-txt">{e.cargo_representante}</span>{/if}
              </td>
              <td class="txt-sm">{e.canton || '—'}{e.provincia ? ', ' + e.provincia : ''}</td>
              <td class="txt-sm mono">{e.ruc || '—'}</td>
              <td>
                <span class="badge" class:activo={e.activo} class:inactivo={!e.activo}>
                  {e.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td class="acciones">
                <a href="/entidades/{e.id_entidad}" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion {e.activo ? 'danger' : 'success'}"
                  onclick={() => toggle(e.id_entidad, e.activo)}
                  title={e.activo ? 'Desactivar' : 'Activar'}>
                  <i class="bi bi-{e.activo ? 'toggle-on' : 'toggle-off'}"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron entidades</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
    <div class="total">{filtered.length} entidad(es) encontrada(s)</div>
  {/if}
</div>

{#if toast}<div class="toast">{toast}</div>{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

.nombre-p { font-weight:700; }
.nombre-s { display:block;font-size:.72rem;color:var(--gris);margin-top:1px; }
.tipo-badge { font-size:.72rem;font-weight:700;color:var(--verde);background:var(--verde-claro);padding:2px 8px;border-radius:6px; }
.sec-txt { display:block;font-size:.72rem;color:var(--gris);margin-top:1px; }
.txt-sm { font-size:.78rem; }
.mono { font-family:monospace; }
.acciones { display:flex;gap:6px; }
</style>
