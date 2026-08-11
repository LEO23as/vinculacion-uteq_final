<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';

  const API_BASE = 'http://127.0.0.1:8000';
  const id = $derived($page.params.id);

  let proy = $state(null);
  let loading = $state(true);
  let fotoActiva = $state(null);

  let documentos = $state([]);
  let tiposDoc = $state([]);
  let codigoTipoSubir = $state('');
  let archivoSubir = $state(null);
  let subiendoDoc = $state(false);

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
      [proy, tiposDoc] = await Promise.all([
        fetchAPI(`/api/proyectos/${id}/detalle/`),
        fetchAPI('/api/tipos-documento/'),
      ]);
      await cargarDocumentos();
    } finally { loading = false; }
  });

  async function cargarDocumentos() {
    try { documentos = await fetchAPI(`/api/proyectos/${id}/documentos/`); } catch { documentos = []; }
  }

  function onArchivoSubirChange(e) { archivoSubir = e.target.files[0] || null; }

  async function subirDocumento() {
    if (!codigoTipoSubir || !archivoSubir) { toast.error('Selecciona el tipo de documento y el archivo.'); return; }
    subiendoDoc = true;
    try {
      const fd = new FormData();
      fd.append('codigo_tipo', codigoTipoSubir);
      fd.append('archivo', archivoSubir);
      const res = await fetch(`/api/proyectos/${id}/documentos/subir/`, { method:'POST', credentials:'include', body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { toast.error(data.error || 'Error al subir el documento'); return; }
      archivoSubir = null; codigoTipoSubir = '';
      await cargarDocumentos();
      toast.success('Documento subido');
    } catch { toast.error('Error de conexión'); }
    finally { subiendoDoc = false; }
  }

  async function eliminarDocumento(idDoc) {
    try {
      await fetch(`/api/documentos/${idDoc}/`, { method:'DELETE', credentials:'include' });
      await cargarDocumentos();
      toast.success('Documento eliminado');
    } catch { toast.error('No se pudo eliminar'); }
  }
</script>

<svelte:head><title>{proy?.nombre || 'Proyecto'} — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/proyectos">Proyectos</a>
    <span class="sep">/</span>
    <span class="current">Detalle</span><span class="sep">/</span>
  </nav>
  {#if proy}
    <a href="/proyectos/{id}/editar" class="btn-editar">
      <i class="bi bi-pencil"></i> Editar
    </a>
  {/if}
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando proyecto...</div>
{:else if proy}
  <div class="detalle-wrap">

    <!-- HEADER CARD -->
    <div class="header-card">
      <div class="hc-left">
        <span class="hc-code">{proy.codigo}</span>
        <h1 class="hc-title">{proy.nombre}</h1>
        {#if proy.nombre_corto}
          <p class="hc-short">{proy.nombre_corto}</p>
        {/if}
      </div>
      <div class="hc-right">
        <span class="badge est-{ESTADOS[proy.estado]?.cls}">
          {ESTADOS[proy.estado]?.label || proy.estado}
        </span>
      </div>
    </div>

    <div class="detalle-grid">
      <!-- COLUMNA PRINCIPAL -->
      <div class="col-main">

        <!-- Información General -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-info-circle-fill"></i> Información General</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Facultad</span>
              <span class="info-val">{proy.facultad}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Carrera</span>
              <span class="info-val">{proy.carrera}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Período de inicio</span>
              <span class="info-val">{proy.periodo}</span>
            </div>
            {#if proy.linea_vinculacion}
            <div class="info-item">
              <span class="info-label">Línea de vinculación</span>
              <span class="info-val">{proy.linea_vinculacion}</span>
            </div>
            {/if}
            {#if proy.ods}
            <div class="info-item">
              <span class="info-label">ODS</span>
              <span class="info-val">{proy.ods}</span>
            </div>
            {/if}
            {#if proy.alcance}
            <div class="info-item">
              <span class="info-label">Alcance</span>
              <span class="info-val">{proy.alcance}</span>
            </div>
            {/if}
            {#if proy.fecha_inicio}
            <div class="info-item">
              <span class="info-label">Fecha inicio</span>
              <span class="info-val">{proy.fecha_inicio}</span>
            </div>
            {/if}
            {#if proy.fecha_fin_planificada}
            <div class="info-item">
              <span class="info-label">Fecha fin planificada</span>
              <span class="info-val">{proy.fecha_fin_planificada}</span>
            </div>
            {/if}
            {#if proy.provincia}
            <div class="info-item full">
              <span class="info-label">Ubicación</span>
              <span class="info-val">{proy.canton}, {proy.parroquia ? proy.parroquia + ', ' : ''}{proy.provincia}</span>
            </div>
            {/if}
            {#if proy.presupuesto_planificado}
            <div class="info-item">
              <span class="info-label">Presupuesto planificado</span>
              <span class="info-val">$ {proy.presupuesto_planificado}</span>
            </div>
            {/if}
            {#if proy.resolucion_aprobacion}
            <div class="info-item">
              <span class="info-label">Resolución de aprobación</span>
              <span class="info-val">{proy.resolucion_aprobacion}</span>
            </div>
            {/if}
          </div>
          {#if proy.descripcion}
            <div class="sec-section">
              <span class="info-label">Descripción</span>
              <p class="info-text">{proy.descripcion}</p>
            </div>
          {/if}
          {#if proy.objetivo_general}
            <div class="sec-section">
              <span class="info-label">Objetivo general</span>
              <p class="info-text">{proy.objetivo_general}</p>
            </div>
          {/if}
          {#if proy.terminos_negociacion}
            <div class="sec-section">
              <span class="info-label">Términos de negociación</span>
              <p class="info-text">{proy.terminos_negociacion}</p>
            </div>
          {/if}
        </div>

        <!-- Fotos -->
        {#if proy.fotos?.length}
          <div class="sec-card">
            <h3 class="sec-title"><i class="bi bi-images"></i> Evidencia fotográfica ({proy.fotos.length})</h3>
            <div class="fotos-grid">
              {#each proy.fotos as foto}
                <button class="foto-thumb" onclick={() => fotoActiva = foto}>
                  <img src={API_BASE + foto.url} alt={foto.titulo} />
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Documentos del portafolio -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-folder-fill"></i> Documentos del portafolio ({documentos.length})</h3>
          {#if documentos.length}
            <div class="docs-list">
              {#each documentos as d}
                <div class="doc-row">
                  <i class="bi bi-file-earmark-pdf"></i>
                  <div class="doc-info">
                    <a href={API_BASE + d.url} target="_blank">{d.tipo}</a>
                    <span class="doc-meta">{d.codigo_tipo} — {d.nombre} · {d.tamanio_kb} KB</span>
                  </div>
                  <button class="doc-del" onclick={() => eliminarDocumento(d.id)} title="Eliminar"><i class="bi bi-trash"></i></button>
                </div>
              {/each}
            </div>
          {:else}
            <p class="empty-side">Aún no se han subido documentos.</p>
          {/if}

          <div class="doc-upload">
            <select bind:value={codigoTipoSubir}>
              <option value="">— Tipo de documento —</option>
              {#each tiposDoc as t}<option value={t.codigo}>{t.numero_carpeta}. {t.nombre}</option>{/each}
            </select>
            <input type="file" accept="application/pdf,image/*" onchange={onArchivoSubirChange} />
            <button class="btn-side-add" onclick={subirDocumento} disabled={subiendoDoc}>
              {#if subiendoDoc}<i class="bi bi-arrow-repeat spin"></i>{:else}<i class="bi bi-cloud-arrow-up"></i> Subir{/if}
            </button>
          </div>
        </div>

      </div>

      <!-- COLUMNA LATERAL -->
      <div class="col-side">
        <!-- Convenios -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-file-earmark-text-fill"></i> Convenios ({proy.convenios_count})</h3>
          {#if proy.convenios_count > 0}
            <a href="/convenios?proyecto={id}" class="link-ver">Ver convenios del proyecto</a>
          {:else}
            <p class="empty-side">No hay convenios registrados</p>
          {/if}
          <a href="/convenios/nuevo?proyecto={id}" class="btn-side-add">
            <i class="bi bi-plus-lg"></i> Agregar convenio
          </a>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="loading-wrap">Proyecto no encontrado</div>
{/if}

<!-- LIGHTBOX -->
{#if fotoActiva}
  <div class="lightbox" onclick={() => fotoActiva = null}>
    <button class="lb-close" onclick={() => fotoActiva = null}><i class="bi bi-x-lg"></i></button>
    <img src={API_BASE + fotoActiva.url} alt={fotoActiva.titulo} onclick={(e) => e.stopPropagation()} />
    {#if fotoActiva.titulo}<p class="lb-caption">{fotoActiva.titulo}</p>{/if}
  </div>
{/if}

<style>
.subbar {
  display:flex;align-items:center;justify-content:space-between;
  padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde);
}
.btn-editar:hover { background:var(--verde);color:#fff; }

.loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center;font-size:.9rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }

.detalle-wrap { padding:20px 24px; }

.header-card {
  background:#fff;border-radius:14px;border:1px solid var(--borde);
  padding:20px 24px;box-shadow:var(--sombra);margin-bottom:18px;
  display:flex;align-items:flex-start;justify-content:space-between;gap:16px;
}
.hc-code {
  background:var(--verde-claro);color:var(--verde);font-size:.75rem;font-weight:800;
  padding:3px 10px;border-radius:6px;display:inline-block;margin-bottom:8px;
}
.hc-title { font-size:1.2rem;font-weight:900;color:var(--negro);line-height:1.3;margin-bottom:4px; }
.hc-short { font-size:.82rem;color:var(--gris);font-weight:600; }
.hc-right { flex-shrink:0; }

.badge { padding:4px 14px;border-radius:20px;font-size:.75rem;font-weight:800; }
.est-ejecucion  { background:#e8f4e8;color:#1b7505; }
.est-propuesto  { background:#fff8e1;color:#dba112; }
.est-aprobado   { background:#e8f0ff;color:#0d6efd; }
.est-cierre     { background:#fff3e0;color:#fd7e14; }
.est-detenido   { background:#fff0f0;color:#dc3545; }
.est-finalizado { background:#f4f4f4;color:#a8a8a7; }
.est-rechazado  { background:#f4f4f4;color:#6c757d; }

.detalle-grid { display:grid;grid-template-columns:1fr 280px;gap:18px; }
@media (max-width:900px) { .detalle-grid { grid-template-columns:1fr; } }

.sec-card {
  background:#fff;border-radius:14px;border:1px solid var(--borde);
  padding:18px 20px;box-shadow:var(--sombra);margin-bottom:0;
}
.col-main { display:flex;flex-direction:column;gap:16px; }
.col-side { display:flex;flex-direction:column;gap:16px; }

.sec-title {
  font-size:.88rem;font-weight:800;color:var(--negro);
  display:flex;align-items:center;gap:8px;margin-bottom:14px;
}
.sec-title i { color:var(--verde); }

.info-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:12px; }
.info-item { display:flex;flex-direction:column;gap:2px; }
.info-item.full { grid-column:1/-1; }
.info-label { font-size:.65rem;font-weight:800;color:var(--gris);text-transform:uppercase;letter-spacing:.05em; }
.info-val { font-size:.85rem;color:var(--negro);font-weight:600; }
.sec-section { margin-top:10px;border-top:1px solid #f0f0f0;padding-top:10px; }
.info-text { font-size:.83rem;color:#444;line-height:1.6;margin-top:4px; }

.fotos-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px; }
.foto-thumb {
  border:none;background:none;padding:0;cursor:pointer;border-radius:8px;overflow:hidden;
  aspect-ratio:4/3;transition:transform .2s;
}
.foto-thumb:hover { transform:scale(1.04); }
.foto-thumb img { width:100%;height:100%;object-fit:cover;display:block; }

.empty-side { font-size:.8rem;color:var(--gris);padding:6px 0; }

.docs-list { display:flex;flex-direction:column;gap:8px;margin-bottom:14px; }
.doc-row { display:flex;align-items:center;gap:10px;background:#f6fbf2;border:1px solid #cfe6c2;border-radius:10px;padding:8px 12px; }
.doc-row > i { color:#c0392b;font-size:1.1rem;flex-shrink:0; }
.doc-info { flex:1;display:flex;flex-direction:column;gap:1px;min-width:0; }
.doc-info a { font-size:.83rem;font-weight:700;color:var(--verde);text-decoration:none; }
.doc-info a:hover { text-decoration:underline; }
.doc-meta { font-size:.7rem;color:var(--gris);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.doc-del { background:none;border:none;color:#bbb;font-size:.9rem;cursor:pointer;padding:4px;border-radius:6px;flex-shrink:0; }
.doc-del:hover { background:#fdecec;color:#dc3545; }
.doc-upload { display:flex;flex-wrap:wrap;gap:8px;align-items:center; }
.doc-upload select { flex:1;min-width:180px;padding:8px 10px;border:1px solid var(--borde);border-radius:8px;font-size:.82rem;font-family:inherit; }
.doc-upload input[type=file] { flex:1;min-width:160px;font-size:.78rem; }
.doc-upload .btn-side-add { border:none;cursor:pointer;font-family:inherit;margin-top:0; }
.doc-upload .btn-side-add:disabled { opacity:.6;cursor:not-allowed; }
.link-ver { display:block;font-size:.82rem;color:var(--verde);font-weight:700;margin-bottom:8px;text-decoration:none; }
.link-ver:hover { text-decoration:underline; }
.btn-side-add {
  display:flex;align-items:center;gap:6px;
  background:var(--verde-claro);color:var(--verde);border-radius:8px;
  padding:7px 14px;font-size:.8rem;font-weight:800;text-decoration:none;
  transition:background .2s;margin-top:8px;
}
.btn-side-add:hover { background:#c8e6b0; }

/* LIGHTBOX */
.lightbox {
  position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;
  display:flex;align-items:center;justify-content:center;flex-direction:column;gap:10px;cursor:pointer;
}
.lb-close {
  position:absolute;top:16px;right:16px;background:rgba(255,255,255,.15);
  border:none;border-radius:50%;width:38px;height:38px;
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:1rem;cursor:pointer;
}
.lightbox img { max-width:90vw;max-height:80vh;border-radius:8px;cursor:default; }
.lb-caption { color:rgba(255,255,255,.8);font-size:.82rem; }
</style>
