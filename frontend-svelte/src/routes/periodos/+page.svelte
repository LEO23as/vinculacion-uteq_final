<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

    let periodos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let toast = $state('');

  onMount(async () => {
    try { periodos = await fetchAPI('/api/periodos/'); }
    finally { loading = false; }
  });

  let filtered = $derived(periodos.filter(p =>
    p.nombre.toLowerCase().includes(q.toLowerCase()) ||
    p.codigo.toLowerCase().includes(q.toLowerCase())
  ));

  async function toggle(id, activo) {
    await fetch(`/api/periodos/${id}/`, {
      method:'PUT', credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({activo: !activo}),
    });
    periodos = periodos.map(p => p.id_periodo === id ? {...p, activo: !activo} : p);
    toast = activo ? 'Período desactivado' : 'Período activado';
    setTimeout(() => toast = '', 3000);
  }
</script>

<svelte:head><title>Períodos — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Períodos Académicos</span><span class="sep">/</span>
  </nav>
  <a href="/periodos/nuevo" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nuevo período</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-calendar3"></i> Períodos Académicos</h2>
      <p class="page-sub">Gestión de ciclos SPA y PPA</p>
    </div>
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar período..." />
    </div>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Inicio</th><th>Fin</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each filtered as p}
            <tr>
              <td><span class="code">{p.codigo}</span></td>
              <td>{p.nombre}</td>
              <td>
                <span class="badge {p.tipo === 'SPA' ? 'spa' : 'ppa'}">{p.tipo}</span>
              </td>
              <td class="txt-sm">{p.fecha_inicio || '—'}</td>
              <td class="txt-sm">{p.fecha_fin || '—'}</td>
              <td>
                <span class="badge" class:activo={p.activo} class:inactivo={!p.activo}>
                  {p.activo ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <td class="acciones">
                <a href="/periodos/{p.id_periodo}" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion {p.activo ? 'danger' : 'success'}"
                  onclick={() => toggle(p.id_periodo, p.activo)}
                  title={p.activo ? 'Desactivar' : 'Activar'}>
                  <i class="bi bi-{p.activo ? 'toggle-on' : 'toggle-off'}"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron períodos</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
    <div class="total">Total: <strong>{filtered.length}</strong> períodos</div>
  {/if}
</div>

{#if toast}<div class="toast">{toast}</div>{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

.txt-sm { font-size:.78rem; }
.acciones { display:flex;gap:6px; }
.badge.spa { background:#e8f0ff;color:#0d6efd; }
.badge.ppa { background:#fff8e1;color:#dba112; }
.badge.success { background:var(--verde-claro);color:var(--verde); }
</style>
