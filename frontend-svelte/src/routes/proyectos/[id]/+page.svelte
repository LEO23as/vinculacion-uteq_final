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
    <span class="current">Detalle</span>
  </nav>
  {#if proy}
    <a href="/proyectos/{id}/editar" class="btn-editar">
      <i class="bi bi-pencil-square"></i> Editar proyecto
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
        <span class="hc-code"><i class="bi bi-bookmark-fill"></i> {proy.codigo}</span>
        <h1 class="hc-title">{proy.nombre}</h1>
        {#if proy.nombre_corto}
          <p class="hc-short">{proy.nombre_corto}</p>
        {/if}
      </div>
      <div class="hc-right">
        <span class="badge est-{ESTADOS[proy.estado]?.cls}">
          <span class="dot"></span>
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
              <span class="info-label">ODS Atendidos</span>
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
              <span class="info-label">Fecha de inicio</span>
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
              <span class="info-label">Ubicación geográfica</span>
              <span class="info-val"><i class="bi bi-geo-alt-fill text-verde"></i> {proy.canton}, {proy.parroquia ? proy.parroquia + ', ' : ''}{proy.provincia}</span>
            </div>
            {/if}
            {#if proy.presupuesto_planificado}
            <div class="info-item">
              <span class="info-label">Presupuesto planificado</span>
              <span class="info-val text-verde font-bold">$ {proy.presupuesto_planificado}</span>
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
              <span class="info-label">Descripción del proyecto</span>
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
                  <i class="bi bi-file-earmark-pdf-fill"></i>
                  <div class="doc-info">
                    <a href={API_BASE + d.url} target="_blank">{d.tipo}</a>
                    <span class="doc-meta">{d.codigo_tipo} — {d.nombre} · {d.tamanio_kb} KB</span>
                  </div>
                  <button class="doc-del" onclick={() => eliminarDocumento(d.id)} title="Eliminar"><i class="bi bi-trash"></i></button>
                </div>
              {/each}
            </div>
          {:else}
            <p class="empty-side">Aún no se han subido documentos al portafolio.</p>
          {/if}

          <div class="doc-upload">
            <select bind:value={codigoTipoSubir}>
              <option value="">— Tipo de documento —</option>
              {#each tiposDoc as t}<option value={t.codigo}>{t.numero_carpeta}. {t.nombre}</option>{/each}
            </select>
            <input type="file" accept="application/pdf,image/*" onchange={onArchivoSubirChange} />
            <button class="btn-side-add primary" onclick={subirDocumento} disabled={subiendoDoc}>
              {#if subiendoDoc}<i class="bi bi-arrow-repeat spin"></i>{:else}<i class="bi bi-cloud-arrow-up"></i> Subir{/if}
            </button>
          </div>
        </div>

      </div>

      <!-- COLUMNA LATERAL -->
      <div class="col-side">
        <!-- Convenios -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-file-earmark-text-fill"></i> Convenios vinculados</h3>
          {#if proy.convenios && proy.convenios.length > 0}
            <div class="convenios-list">
              {#each proy.convenios as conv}
                <div class="conv-card">
                  <div class="conv-head">
                    <span class="conv-entidad"><i class="bi bi-building"></i> {conv.entidad_nombre}</span>
                    <span class="conv-badge {conv.estado.toLowerCase()}">{conv.estado}</span>
                  </div>
                  {#if conv.numero_memorando}
                    <div class="conv-memo"><i class="bi bi-file-text"></i> Memo: {conv.numero_memorando}</div>
                  {/if}
                  <div class="conv-dates">
                    <span>Firma: {conv.fecha_firma || 'N/A'}</span> · <span>Vence: {conv.fecha_fin || 'N/A'}</span>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="empty-side">No hay convenios registrados para este proyecto.</p>
          {/if}
          <a href="/convenios/nuevo?proyecto={id}" class="btn-side-add primary block">
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
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; background: #fff; border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: var(--gris, #777); font-weight: 700; }
  .breadcrumb a { color: var(--gris, #777); text-decoration: none; transition: color 0.2s; }
  .breadcrumb a:hover { color: var(--verde, #1b5e20); }
  .breadcrumb .sep { color: #ccc; }
  .breadcrumb .current { color: var(--verde, #1b5e20); font-weight: 800; }

  .btn-editar {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--verde, #1b5e20); color: #fff; border-radius: 9px;
    padding: 9px 20px; font-size: 0.84rem; font-weight: 800; text-decoration: none;
    box-shadow: 0 3px 10px rgba(27, 94, 32, 0.2); transition: all 0.2s ease;
  }
  .btn-editar:hover {
    background: #134217; color: #fff; transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(27, 94, 32, 0.3);
  }

  .loading-wrap { display: flex; align-items: center; gap: 10px; color: var(--gris, #777); font-weight: 700; padding: 60px; justify-content: center; font-size: 0.9rem; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }

  .detalle-wrap { padding: 24px; }

  .header-card {
    background: #fff; border-radius: 16px; border: 1px solid #e3eee5;
    padding: 22px 26px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); margin-bottom: 20px;
    display: flex; align-items: flex-start; justify-content: space-between; gap: 18px;
  }
  .hc-code {
    background: #e8f5e9; color: var(--verde, #1b5e20); font-size: 0.78rem; font-weight: 800;
    padding: 4px 12px; border-radius: 8px; border: 1px solid #c8e6c9; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 10px;
  }
  .hc-title { font-size: 1.25rem; font-weight: 900; color: #111; line-height: 1.3; margin: 0 0 6px 0; }
  .hc-short { font-size: 0.85rem; color: #666; font-weight: 600; margin: 0; }
  .hc-right { flex-shrink: 0; }

  .badge {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 16px; border-radius: 20px; font-size: 0.78rem; font-weight: 800;
  }
  .badge .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
  .est-ejecucion  { background: #e8f5e9; color: #1b7505; border: 1px solid #c8e6c9; }
  .est-propuesto  { background: #fff8e1; color: #dba112; border: 1px solid #ffe082; }
  .est-aprobado   { background: #e8f0ff; color: #0d6efd; border: 1px solid #b6d4fe; }
  .est-cierre     { background: #fff3e0; color: #fd7e14; border: 1px solid #ffe0b2; }
  .est-detenido   { background: #ffebee; color: #dc3545; border: 1px solid #ffcdd2; }
  .est-finalizado { background: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; }
  .est-rechazado  { background: #f5f5f5; color: #757575; border: 1px solid #e0e0e0; }

  .detalle-grid { display: grid; grid-template-columns: 1fr 310px; gap: 20px; }
  @media (max-width: 960px) { .detalle-grid { grid-template-columns: 1fr; } }

  .sec-card {
    background: #fff; border-radius: 14px; border: 1px solid #e5efe7;
    padding: 22px 24px; box-shadow: 0 3px 14px rgba(0,0,0,0.04);
  }
  .col-main { display: flex; flex-direction: column; gap: 20px; }
  .col-side { display: flex; flex-direction: column; gap: 20px; }

  .sec-title {
    font-size: 0.88rem; font-weight: 800; color: #222; text-transform: uppercase; letter-spacing: 0.04em;
    display: flex; align-items: center; gap: 10px; margin-bottom: 18px;
    border-bottom: 1.5px dashed #e5efe7; padding-bottom: 10px;
  }
  .sec-title i {
    font-size: 0.95rem; color: var(--verde, #1b5e20); background: #e8f5e9;
    padding: 5px 8px; border-radius: 7px; flex-shrink: 0;
  }

  .info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .info-item {
    display: flex; flex-direction: column; gap: 4px;
    background: #fafdfa; border: 1px solid #edf5ee; border-radius: 9px; padding: 12px 14px;
  }
  .info-item.full { grid-column: 1 / -1; }
  .info-label { font-size: 0.68rem; font-weight: 800; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
  .info-val { font-size: 0.86rem; color: #111; font-weight: 700; word-break: break-word; }
  .text-verde { color: var(--verde, #1b5e20); }
  .font-bold { font-weight: 900; }

  .sec-section { margin-top: 14px; background: #fafdfa; border: 1px solid #edf5ee; border-radius: 9px; padding: 12px 16px; }
  .sec-section .info-label { display: block; margin-bottom: 6px; }
  .info-text { font-size: 0.86rem; color: #333; line-height: 1.6; margin: 0; }

  .fotos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; }
  .foto-thumb {
    border: none; background: none; padding: 0; cursor: pointer; border-radius: 10px; overflow: hidden;
    aspect-ratio: 4/3; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  .foto-thumb:hover { transform: scale(1.03); box-shadow: 0 4px 14px rgba(0,0,0,0.18); }
  .foto-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }

  .empty-side { font-size: 0.83rem; color: #888; font-weight: 600; padding: 8px 0; margin: 0; }

  .docs-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
  .doc-row { display: flex; align-items: center; gap: 12px; background: #f6fbf2; border: 1px solid #cfe6c2; border-radius: 10px; padding: 10px 14px; }
  .doc-row > i { color: #c0392b; font-size: 1.2rem; flex-shrink: 0; }
  .doc-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .doc-info a { font-size: 0.85rem; font-weight: 800; color: var(--verde, #1b5e20); text-decoration: none; }
  .doc-info a:hover { text-decoration: underline; }
  .doc-meta { font-size: 0.72rem; color: #666; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .doc-del { background: none; border: none; color: #aaa; font-size: 0.95rem; cursor: pointer; padding: 4px; border-radius: 6px; flex-shrink: 0; transition: all 0.2s; }
  .doc-del:hover { background: #fdecec; color: #dc3545; }

  .doc-upload { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; background: #fafafa; padding: 12px; border-radius: 10px; border: 1px solid #eee; }
  .doc-upload select { flex: 1; min-width: 180px; height: 38px; padding: 0 12px; border: 1.5px solid var(--borde, #ccc); border-radius: 8px; font-size: 0.83rem; font-family: inherit; }
  .doc-upload input[type=file] { flex: 1; min-width: 160px; font-size: 0.78rem; }
  
  .convenios-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
  .conv-card { background: #fafdfa; border: 1px solid #edf5ee; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 5px; }
  .conv-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .conv-entidad { font-size: 0.84rem; font-weight: 800; color: #222; display: flex; align-items: center; gap: 6px; }
  .conv-entidad i { color: var(--verde, #1b5e20); }
  .conv-badge { font-size: 0.68rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; text-transform: uppercase; }
  .conv-badge.vigente { background: #e8f5e9; color: #1b7505; }
  .conv-badge.vencido { background: #ffebee; color: #c0392b; }
  .conv-memo { font-size: 0.76rem; color: #555; font-weight: 700; }
  .conv-dates { font-size: 0.72rem; color: #777; font-weight: 600; }

  .btn-side-add {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    background: #f0f4f1; color: var(--verde, #1b5e20); border-radius: 9px; border: none;
    padding: 10px 18px; font-size: 0.83rem; font-weight: 800; text-decoration: none; cursor: pointer;
    transition: all 0.2s ease;
  }
  .btn-side-add:hover { background: #e2ede4; }
  .btn-side-add.primary { background: var(--verde, #1b5e20); color: #fff; box-shadow: 0 3px 10px rgba(27, 94, 32, 0.18); }
  .btn-side-add.primary:hover:not(:disabled) { background: #134217; }
  .btn-side-add.block { width: 100%; box-sizing: border-box; }

  .lightbox {
    position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); z-index: 9999;
    display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 10px; cursor: pointer;
    backdrop-filter: blur(3px);
  }
  .lb-close {
    position: absolute; top: 16px; right: 16px; background: rgba(255, 255, 255, 0.15);
    border: none; border-radius: 50%; width: 38px; height: 38px;
    display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1rem; cursor: pointer;
  }
  .lightbox img { max-width: 90vw; max-height: 80vh; border-radius: 10px; cursor: default; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
  .lb-caption { color: #fff; font-size: 0.9rem; font-weight: 700; margin: 0; }
</style>
