<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

    let items = $state([]);
  let periodos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let filtEst = $state('');
  let filtPer = $state('');
  let confirmEliminar = $state(null);
  let toast = $state('');

  const ESTADOS = {
    VIGENTE:   { label:'Vigente',   cls:'vigente'  },
    VENCIDO:   { label:'Vencido',   cls:'vencido'  },
    RENOVADO:  { label:'Renovado',  cls:'renovado' },
    CANCELADO: { label:'Cancelado', cls:'cancelado'},
  };

  async function cargar() {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (filtEst) params.set('estado', filtEst);
    if (filtPer) params.set('periodo', filtPer);
    const data = await fetch('/api/convenios/list/?' + params, { credentials:'include' }).then(r => r.json());
    items = data.results || [];
  }

  onMount(async () => {
    try {
      [periodos] = await Promise.all([
        fetchAPI('/api/periodos/'),
      ]);
      await cargar();
    } finally { loading = false; }
  });

  function limpiar() { q = ''; filtEst = ''; filtPer = ''; cargar(); }

  async function eliminar(id) {
    await fetch(`/api/convenios/${id}/`, { method:'DELETE', credentials:'include' });
    items = items.filter(c => c.id_convenio !== id);
    confirmEliminar = null;
    toast = 'Convenio eliminado';
    setTimeout(() => toast = '', 3000);
  }
</script>

<svelte:head><title>Convenios — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Convenios</span><span class="sep">/</span>
  </nav>
  <a href="/convenios/nuevo" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nuevo convenio</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-file-earmark-text"></i> Gestión de Convenios</h2>
      <p class="page-sub">Acuerdos con entidades cooperantes</p>
    </div>
  </div>

  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar entidad, proyecto o memorando..." onkeydown={(e) => e.key === 'Enter' && cargar()} />
    </div>
    <select bind:value={filtEst}>
      <option value="">Todos los estados</option>
      {#each Object.entries(ESTADOS) as [val, info]}
        <option value={val}>{info.label}</option>
      {/each}
    </select>
    <select bind:value={filtPer}>
      <option value="">Todos los períodos</option>
      {#each periodos as p}
        <option value={p.id_periodo}>{p.nombre}</option>
      {/each}
    </select>
    <button class="btn-filtrar" onclick={cargar}>Filtrar</button>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr><th>N° Memorando</th><th>Entidad</th><th>Proyecto</th><th>Período</th><th>Firma</th><th>Estudiantes</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {#each items as c}
            <tr>
              <td><strong class="code">{c.numero_memorando || 'Sin Nro.'}</strong></td>
              <td class="td-truncate">{c.entidad_nombre}</td>
              <td class="td-truncate">{c.proyecto_nombre}</td>
              <td class="txt-sm">{c.periodo_nombre}</td>
              <td class="txt-sm">{c.fecha_firma || '—'}</td>
              <td class="txt-sm center">{c.estudiantes_asignados || 0}</td>
              <td>
                <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
                  {ESTADOS[c.estado]?.label || c.estado}
                </span>
              </td>
              <td class="acciones">
                <a href="/convenios/{c.id_convenio}" class="btn-accion" title="Ver detalle">
                  <i class="bi bi-eye"></i>
                </a>
                <a href="/convenios/{c.id_convenio}/editar" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion danger" onclick={() => confirmEliminar = c} title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if items.length === 0}
            <tr><td colspan="8" class="empty">No se encontraron convenios</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
    <div class="total">{items.length} convenio(s) encontrado(s)</div>
  {/if}
</div>

<!-- Modal confirmar eliminar -->
{#if confirmEliminar}
  <div class="modal-overlay" onclick={() => confirmEliminar = null}>
    <div class="modal-confirm" onclick={(e) => e.stopPropagation()}>
      <i class="bi bi-exclamation-triangle modal-icon"></i>
      <h3>¿Eliminar convenio?</h3>
      <p>Se eliminará el convenio <strong>{confirmEliminar.numero_memorando || 'sin número'}</strong> con <em>{confirmEliminar.entidad_nombre}</em>. Esta acción no se puede deshacer.</p>
      <div class="modal-btns">
        <button class="btn-cancel-modal" onclick={() => confirmEliminar = null}>Cancelar</button>
        <button class="btn-delete-modal" onclick={() => eliminar(confirmEliminar.id_convenio)}>Eliminar</button>
      </div>
    </div>
  </div>
{/if}

{#if toast}<div class="toast">{toast}</div>{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

.td-truncate { max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.txt-sm { font-size:.78rem; }
.center { text-align:center; }
.acciones { display:flex;gap:6px; }

/* Modal */
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999; }
.modal-confirm { background:#fff;border-radius:16px;padding:32px 28px;max-width:380px;width:90%;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.18); }
.modal-icon { font-size:2.4rem;color:#dc3545;margin-bottom:12px;display:block; }
.modal-confirm h3 { font-size:1.1rem;font-weight:900;margin-bottom:10px; }
.modal-confirm p { font-size:.85rem;color:#555;line-height:1.5;margin-bottom:20px; }
.modal-btns { display:flex;gap:10px;justify-content:center; }
.btn-cancel-modal { background:#fff;border:1.5px solid var(--borde);border-radius:9px;padding:9px 22px;font-size:.85rem;font-weight:700;cursor:pointer; }
.btn-delete-modal { background:#dc3545;color:#fff;border:none;border-radius:9px;padding:9px 22px;font-size:.85rem;font-weight:800;cursor:pointer; }
</style>
