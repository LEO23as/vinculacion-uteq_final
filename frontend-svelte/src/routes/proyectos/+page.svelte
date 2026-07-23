<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

  let items     = $state([]);
  let facultades = $state([]);
  let loading   = $state(true);

  let q         = $state('');
  let filtEst   = $state('');
  let filtFac   = $state('');

  const ESTADOS = {
    EN_EJECUCION: { label:'En ejecución', cls:'ejecucion' },
    PROPUESTO:    { label:'Propuesto',    cls:'propuesto'  },
    APROBADO:     { label:'Aprobado',     cls:'aprobado'   },
    EN_CIERRE:    { label:'En cierre',    cls:'cierre'     },
    DETENIDO:     { label:'Detenido',     cls:'detenido'   },
    FINALIZADO:   { label:'Finalizado',   cls:'finalizado' },
    RECHAZADO:    { label:'Rechazado',    cls:'rechazado'  },
  };

  onMount(async () => {
    try {
      [items, facultades] = await Promise.all([
        fetchAPI('/api/proyectos/'),
        fetchAPI('/api/facultades/'),
      ]);
    } finally { loading = false; }
  });

  let filtered = $derived(items.filter(p => {
    const matchQ = !q ||
      p.nombre.toLowerCase().includes(q.toLowerCase()) ||
      p.codigo.toLowerCase().includes(q.toLowerCase());
    const matchE = !filtEst || p.estado === filtEst;
    const matchF = !filtFac || String(p.facultad_nombre) === String(
      facultades.find(f => String(f.id_facultad) === filtFac)?.nombre || filtFac
    );
    return matchQ && matchE && matchF;
  }));

  function limpiar() { q = ''; filtEst = ''; filtFac = ''; }

  // ── Eliminar proyecto ──────────────────────────────────
  let porEliminar = $state(null);   // proyecto seleccionado para borrar
  let eliminando  = $state(false);
  let toast       = $state('');

  async function confirmarEliminar() {
    if (!porEliminar) return;
    eliminando = true;
    try {
      const res = await fetch(`/api/proyectos/${porEliminar.id_proyecto}/eliminar/`, {
        method: 'DELETE', credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) { toast = data.error || 'No se pudo eliminar'; }
      else {
        items = items.filter(p => p.id_proyecto !== porEliminar.id_proyecto);
        toast = 'Proyecto eliminado';
      }
    } catch { toast = 'Error de conexión'; }
    finally {
      eliminando = false; porEliminar = null;
      setTimeout(() => toast = '', 3500);
    }
  }
</script>

<svelte:head><title>Proyectos — SGV</title></svelte:head>

<!-- SUBBAR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Proyectos</span><span class="sep">/</span>
  </nav>
  <a href="/proyectos/nuevo" class="btn-nuevo">
    <i class="bi bi-plus-lg"></i> Nuevo proyecto
  </a>
</div>

<div class="page-wrap">
  <!-- CABECERA -->
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-folder2-open"></i> Proyectos de Vinculación</h2>
      <p class="page-sub">Registro y seguimiento de proyectos</p>
    </div>
  </div>

  <!-- FILTROS -->
  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar por nombre o código…" />
    </div>
    <select bind:value={filtFac}>
      <option value="">Todas las facultades</option>
      {#each facultades as f}
        <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
      {/each}
    </select>
    <select bind:value={filtEst}>
      <option value="">Todos los estados</option>
      {#each Object.entries(ESTADOS) as [val, info]}
        <option value={val}>{info.label}</option>
      {/each}
    </select>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Código</th><th>Nombre</th><th>Facultad / Carrera</th>
            <th>Período</th><th>Ubicación</th><th>Estado</th><th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as p}
            <tr>
              <td><span class="code">{p.codigo}</span></td>
              <td class="nombre-cell">
                <span class="nombre-principal">{p.nombre_corto || p.nombre}</span>
                {#if p.nombre_corto}
                  <span class="nombre-sec">{p.nombre}</span>
                {/if}
              </td>
              <td>
                <span class="fac-badge">{p.facultad_nombre}</span>
                <span class="carrera-sec">{p.carrera_nombre}</span>
              </td>
              <td class="txt-small">{p.periodo_inicio_nombre}</td>
              <td class="txt-small">{p.canton || '—'}{p.provincia ? ', ' + p.provincia : ''}</td>
              <td>
                <span class="badge est-{(ESTADOS[p.estado]?.cls) || 'finalizado'}">
                  {ESTADOS[p.estado]?.label || p.estado}
                </span>
              </td>
              <td class="acciones">
                <a href="/proyectos/{p.id_proyecto}" class="btn-accion" title="Ver detalle">
                  <i class="bi bi-eye"></i>
                </a>
                <a href="/proyectos/{p.id_proyecto}/editar" class="btn-accion editar" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion eliminar" title="Eliminar" onclick={() => porEliminar = p}>
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron proyectos</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
    <div class="total">{filtered.length} proyecto(s) encontrado(s)</div>
  {/if}
</div>

<!-- MODAL CONFIRMAR ELIMINAR -->
{#if porEliminar}
  <div class="del-overlay" onclick={() => porEliminar = null}>
    <div class="del-box" onclick={(e) => e.stopPropagation()}>
      <div class="del-ico"><i class="bi bi-exclamation-triangle-fill"></i></div>
      <h3>Eliminar proyecto</h3>
      <p>¿Seguro que deseas eliminar <strong>{porEliminar.nombre_corto || porEliminar.nombre}</strong>
      ({porEliminar.codigo})? Se borrarán también sus ubicaciones, fotos, convenios y documentos. Esta acción no se puede deshacer.</p>
      <div class="del-actions">
        <button class="del-cancel" onclick={() => porEliminar = null} disabled={eliminando}>Cancelar</button>
        <button class="del-confirm" onclick={confirmarEliminar} disabled={eliminando}>
          {#if eliminando}<i class="bi bi-arrow-repeat spin"></i> Eliminando…{:else}<i class="bi bi-trash"></i> Sí, eliminar{/if}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if toast}<div class="toast-del">{toast}</div>{/if}

<style>
/* Solo estilos específicos de esta página */
.nombre-cell { max-width: 260px; }
.nombre-principal { display:block;font-weight:700;color:#222; }
.nombre-sec { display:block;font-size:.72rem;color:var(--gris); }
.fac-badge { display:block;background:var(--verde-claro);color:var(--verde);font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:6px;width:fit-content; }
.carrera-sec { display:block;font-size:.72rem;color:var(--gris);margin-top:2px; }
.txt-small { font-size:.78rem; }
.acciones { display:flex;gap:6px; }

/* Estado badges de proyecto */
.est-ejecucion  { background:#e8f4e8;color:#1b7505; }
.est-propuesto  { background:#fff8e1;color:#dba112; }
.est-aprobado   { background:#e8f0ff;color:#0d6efd; }
.est-cierre     { background:#fff3e0;color:#fd7e14; }
.est-detenido   { background:#fff0f0;color:#dc3545; }
.est-finalizado { background:#f4f4f4;color:#a8a8a7; }
.est-rechazado  { background:#f4f4f4;color:#6c757d; }

/* Botón eliminar */
.btn-accion.eliminar:hover { background:#fdecec;color:#dc3545;border-color:#f5c6c6; }

/* Modal eliminar */
.del-overlay { position:fixed;inset:0;background:rgba(13,25,16,.5);z-index:600;display:flex;align-items:center;justify-content:center;padding:20px; }
.del-box { background:#fff;border-radius:16px;max-width:420px;width:100%;padding:24px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3); }
.del-ico { font-size:2.4rem;color:#dc3545;margin-bottom:8px; }
.del-box h3 { font-size:1.15rem;font-weight:900;color:var(--negro);margin-bottom:8px; }
.del-box p { font-size:.85rem;color:#555;line-height:1.5;margin-bottom:20px; }
.del-actions { display:flex;gap:10px;justify-content:center; }
.del-cancel { background:#fff;border:1.5px solid var(--borde);color:#555;font-weight:700;border-radius:10px;padding:9px 18px;font-size:.85rem; }
.del-cancel:hover { border-color:#aaa; }
.del-confirm { background:#dc3545;border:none;color:#fff;font-weight:800;border-radius:10px;padding:9px 20px;font-size:.85rem;display:flex;align-items:center;gap:7px; }
.del-confirm:hover { background:#b02a37; }
.del-confirm:disabled,.del-cancel:disabled { opacity:.6; }
.toast-del { position:fixed;bottom:24px;right:24px;background:var(--negro);color:#fff;font-weight:700;font-size:.82rem;padding:11px 18px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.25);z-index:700; }
</style>
