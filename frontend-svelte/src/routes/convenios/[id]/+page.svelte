<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

    const id = $derived($page.params.id);
  let c = $state(null);
  let loading = $state(true);
  let subiendoAnexo = $state(false);
  let archivoAnexo = $state(null);
  let tipoDoc = $state('');
  let descDoc = $state('');
  let toast = $state('');

  const ESTADOS = {
    VIGENTE:   { label:'Vigente',   cls:'vigente'  },
    VENCIDO:   { label:'Vencido',   cls:'vencido'  },
    RENOVADO:  { label:'Renovado',  cls:'renovado' },
    CANCELADO: { label:'Cancelado', cls:'cancelado'},
  };

  onMount(async () => {
    try {
      const res = await fetch(`/api/convenios/${id}/`, { credentials:'include' });
      c = await res.json();
    } finally { loading = false; }
  });

  function iconAnexo(nombre) {
    const ext = nombre.split('.').pop().toLowerCase();
    if (ext === 'pdf') return 'bi-file-pdf';
    if (['doc','docx'].includes(ext)) return 'bi-file-word';
    if (['xls','xlsx'].includes(ext)) return 'bi-file-excel';
    return 'bi-file-earmark';
  }

  async function subirAnexo(e) {
    const file = e.target.files[0];
    if (!file) return;
    archivoAnexo = file;
  }

  async function confirmarAnexo() {
    if (!archivoAnexo) return;
    subiendoAnexo = true;
    const fd = new FormData();
    fd.append('archivo', archivoAnexo);
    if (tipoDoc) fd.append('tipo_documento', tipoDoc);
    if (descDoc) fd.append('descripcion', descDoc);
    try {
      const res = await fetch(`/api/convenios/${id}/anexos/`, {
        method:'POST', credentials:'include', body:fd,
      });
      const data = await res.json();
      if (res.ok) {
        c.anexos = [...(c.anexos || []), data];
        archivoAnexo = null; tipoDoc = ''; descDoc = '';
        toast = 'Anexo subido correctamente';
        setTimeout(() => toast = '', 3000);
      }
    } finally { subiendoAnexo = false; }
  }

  async function eliminarAnexo(idAnexo) {
    await fetch(`/api/anexos/${idAnexo}/`, { method:'DELETE', credentials:'include' });
    c.anexos = c.anexos.filter(a => a.id_anexo !== idAnexo);
    toast = 'Anexo eliminado';
    setTimeout(() => toast = '', 2000);
  }
</script>

<svelte:head><title>Detalle Convenio — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/convenios">Convenios</a><span class="sep">/</span>
    <span class="current">Detalle</span><span class="sep">/</span>
  </nav>
  {#if c}
    <a href="/convenios/{id}/editar" class="btn-editar"><i class="bi bi-pencil"></i> Editar</a>
  {/if}
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else if c}
<div class="detalle-wrap">

  <!-- HEADER -->
  <div class="header-card">
    <div>
      <h1 class="hc-title">{c.numero_memorando || 'Sin número de memorando'}</h1>
      <p class="hc-sub">{c.entidad_nombre} · {c.periodo_nombre}</p>
    </div>
    <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
      {ESTADOS[c.estado]?.label || c.estado}
    </span>
  </div>

  <div class="detalle-grid">
    <!-- Datos del convenio -->
    <div class="sec-card">
      <h3 class="sec-title"><i class="bi bi-file-text-fill"></i> Datos del convenio</h3>
      <div class="info-grid">
        {#if c.numero_memorando}<div class="info-item"><span class="il">N° Memorando</span><span class="iv">{c.numero_memorando}</span></div>{/if}
        {#if c.fecha_firma}<div class="info-item"><span class="il">Fecha de firma</span><span class="iv">{c.fecha_firma}</span></div>{/if}
        {#if c.fecha_inicio}<div class="info-item"><span class="il">Fecha inicio</span><span class="iv">{c.fecha_inicio}</span></div>{/if}
        {#if c.fecha_fin}<div class="info-item"><span class="il">Fecha fin</span><span class="iv">{c.fecha_fin}</span></div>{/if}
        <div class="info-item"><span class="il">Duración</span><span class="iv">{c.duracion_anios} año(s)</span></div>
        <div class="info-item"><span class="il">Estudiantes asignados</span><span class="iv">{c.estudiantes_asignados}</span></div>
        {#if c.proyecto_nombre}
          <div class="info-item full"><span class="il">Proyecto</span><span class="iv">{c.proyecto_nombre}</span></div>
        {/if}
        {#if c.observaciones}
          <div class="info-item full"><span class="il">Observaciones</span><span class="iv">{c.observaciones}</span></div>
        {/if}
      </div>
    </div>

    <!-- Entidad cooperante -->
    <div class="sec-card">
      <h3 class="sec-title"><i class="bi bi-building-fill"></i> Entidad cooperante</h3>
      <div class="info-grid">
        <div class="info-item full"><span class="il">Nombre</span><span class="iv">{c.entidad_nombre}</span></div>
        {#if c.entidad_siglas}<div class="info-item"><span class="il">Siglas</span><span class="iv">{c.entidad_siglas}</span></div>{/if}
        {#if c.entidad_representante}<div class="info-item"><span class="il">Representante</span><span class="iv">{c.entidad_representante}</span></div>{/if}
        {#if c.entidad_cargo}<div class="info-item"><span class="il">Cargo</span><span class="iv">{c.entidad_cargo}</span></div>{/if}
        {#if c.entidad_provincia}<div class="info-item"><span class="il">Provincia</span><span class="iv">{c.entidad_provincia}</span></div>{/if}
        {#if c.entidad_canton}<div class="info-item"><span class="il">Cantón</span><span class="iv">{c.entidad_canton}</span></div>{/if}
        {#if c.entidad_telefono}<div class="info-item"><span class="il">Teléfono</span><span class="iv">{c.entidad_telefono}</span></div>{/if}
        {#if c.entidad_correo}<div class="info-item"><span class="il">Correo</span><span class="iv">{c.entidad_correo}</span></div>{/if}
      </div>
    </div>

    <!-- Anexos -->
    <div class="sec-card full-col">
      <h3 class="sec-title"><i class="bi bi-paperclip"></i> Anexos del convenio</h3>

      <!-- Subir -->
      <div class="anexo-form">
        <label class="anexo-file" class:selected={!!archivoAnexo}>
          <input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" onchange={subirAnexo} />
          <i class="bi bi-{archivoAnexo ? 'check-circle-fill' : 'cloud-arrow-up'}"></i>
          <span>{archivoAnexo ? archivoAnexo.name : 'Seleccionar archivo'}</span>
        </label>
        {#if archivoAnexo}
          <input class="anexo-input" bind:value={tipoDoc} placeholder="Tipo de documento (ej: Convenio firmado)" />
          <input class="anexo-input" bind:value={descDoc} placeholder="Descripción breve..." />
          <button class="btn-subir" onclick={confirmarAnexo} disabled={subiendoAnexo}>
            {#if subiendoAnexo}<i class="bi bi-arrow-repeat spin"></i>{:else}Subir{/if}
          </button>
        {/if}
      </div>

      <!-- Lista de anexos -->
      {#if c.anexos?.length}
        <div class="anexos-list">
          {#each c.anexos as a}
            <div class="anexo-item">
              <i class="bi {iconAnexo(a.nombre_archivo)} anexo-icon"></i>
              <div class="anexo-info">
                <span class="anexo-nombre">{a.nombre_archivo}</span>
                <span class="anexo-meta">
                  {a.tipo_documento || 'Sin tipo'} · {a.tamanio_kb} KB
                  {#if a.descripcion} · {a.descripcion}{/if}
                </span>
              </div>
              <a href={API + a.url} target="_blank" class="btn-dl" title="Descargar">
                <i class="bi bi-download"></i>
              </a>
              <button class="btn-del" onclick={() => eliminarAnexo(a.id_anexo)} title="Eliminar">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-side">Sin anexos registrados.</p>
      {/if}
    </div>
  </div>
</div>
{:else}
  <div class="loading-wrap">Convenio no encontrado</div>
{/if}

{#if toast}<div class="toast">{toast}</div>{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

</style>
