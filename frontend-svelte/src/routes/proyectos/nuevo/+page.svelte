<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    let facultades = $state([]);
  let carreras   = $state([]);
  let periodos   = $state([]);
  let carrerasFil = $state([]);

  let saving = $state(false);
  let error  = $state('');

  let form = $state({
    codigo:'', nombre:'', nombre_corto:'', id_facultad:'', id_carrera:'',
    id_periodo_inicio:'', estado:'EN_EJECUCION',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', objetivo_general:'', ods:'', linea_vinculacion:'', observaciones:'',
  });
  let fotos = $state([]);
  let previews = $state([]);

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    [facultades, periodos] = await Promise.all([
      fetchAPI('/api/facultades/'),
      fetchAPI('/api/periodos/'),
    ]);
  });

  async function onFacultadChange() {
    form.id_carrera = '';
    if (!form.id_facultad) { carrerasFil = []; return; }
    const all = await fetchAPI('/api/carreras/');
    carrerasFil = all.filter(c => String(c.id_facultad) === String(form.id_facultad));
  }

  function onFotosChange(e) {
    const files = Array.from(e.target.files);
    fotos = [...fotos, ...files];
    files.forEach(f => {
      const reader = new FileReader();
      reader.onload = (ev) => { previews = [...previews, ev.target.result]; };
      reader.readAsDataURL(f);
    });
  }

  function quitarFoto(idx) {
    fotos = fotos.filter((_, i) => i !== idx);
    previews = previews.filter((_, i) => i !== idx);
  }

  async function guardar() {
    error = '';
    if (!form.codigo || !form.nombre || !form.id_facultad || !form.id_carrera || !form.id_periodo_inicio) {
      error = 'Código, nombre, facultad, carrera y período son obligatorios.';
      return;
    }
    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      fotos.forEach(f => fd.append('fotos', f));
      const res = await fetch('/api/proyectos/create/', {
        method: 'POST', credentials: 'include', body: fd,
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear proyecto'; return; }
      goto('/proyectos');
    } catch (e) {
      error = 'Error de conexión';
    } finally { saving = false; }
  }
</script>

<svelte:head><title>Nuevo Proyecto — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/proyectos">Proyectos</a><span class="sep">/</span>
    <span class="current">Nuevo</span><span class="sep">/</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-folder-plus"></i> Nuevo Proyecto de Vinculación</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <!-- Sección 1 -->
    <div class="sec">
      <h4 class="sec-hdr">Identificación del proyecto</h4>
      <div class="grid-row">
        <div class="field col-4">
          <label>Código *</label>
          <input bind:value={form.codigo} placeholder="PVSUTEQ-FCA-001" />
          <small>Formato: PVSUTEQ-[COD_FAC]-[NUM]</small>
        </div>
        <div class="field col-5">
          <label>Nombre completo *</label>
          <input bind:value={form.nombre} placeholder="Nombre completo del proyecto..." />
        </div>
        <div class="field col-3">
          <label>Nombre corto</label>
          <input bind:value={form.nombre_corto} placeholder="Nombre abreviado..." />
        </div>
      </div>
    </div>

    <!-- Sección 2 -->
    <div class="sec">
      <h4 class="sec-hdr">Datos académicos</h4>
      <div class="grid-row">
        <div class="field col-4">
          <label>Facultad *</label>
          <select bind:value={form.id_facultad} onchange={onFacultadChange}>
            <option value="">— Seleccionar —</option>
            {#each facultades as f}
              <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4">
          <label>Carrera *</label>
          <select bind:value={form.id_carrera} disabled={!carrerasFil.length}>
            <option value="">— Seleccionar facultad primero —</option>
            {#each carrerasFil as c}
              <option value={c.id_carrera}>{c.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-2">
          <label>Período *</label>
          <select bind:value={form.id_periodo_inicio}>
            <option value="">— Seleccionar —</option>
            {#each periodos as p}
              <option value={p.id_periodo}>{p.codigo}</option>
            {/each}
          </select>
        </div>
        <div class="field col-2">
          <label>Estado *</label>
          <select bind:value={form.estado}>
            {#each ESTADOS as e}
              <option value={e}>{ESTADOS_LABEL[e]}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- Sección 3 -->
    <div class="sec">
      <h4 class="sec-hdr">Ubicación geográfica</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Provincia</label><input bind:value={form.provincia} /></div>
        <div class="field col-3"><label>Cantón</label><input bind:value={form.canton} /></div>
        <div class="field col-3"><label>Parroquia</label><input bind:value={form.parroquia} /></div>
        <div class="field col-3"><label>Sector/Comunidad</label><input bind:value={form.sector} /></div>
        <div class="field col-2">
          <label>Latitud *</label>
          <input type="number" step="0.0000001" bind:value={form.latitud} placeholder="-1.5637..." />
          <small>Del pin de WhatsApp</small>
        </div>
        <div class="field col-2">
          <label>Longitud *</label>
          <input type="number" step="0.0000001" bind:value={form.longitud} placeholder="-79.4601..." />
        </div>
      </div>
    </div>

    <!-- Sección 4 -->
    <div class="sec">
      <h4 class="sec-hdr">Descripción e información adicional</h4>
      <div class="grid-row">
        <div class="field col-6"><label>Descripción</label><textarea rows="3" bind:value={form.descripcion}></textarea></div>
        <div class="field col-6"><label>Objetivo general</label><textarea rows="3" bind:value={form.objetivo_general}></textarea></div>
        <div class="field col-4"><label>ODS</label><input bind:value={form.ods} placeholder="ODS 1, ODS 4..." /></div>
        <div class="field col-4"><label>Línea de vinculación</label><input bind:value={form.linea_vinculacion} /></div>
        <div class="field col-4"><label>Observaciones</label><input bind:value={form.observaciones} /></div>
      </div>
    </div>

    <!-- Sección 5 -->
    <div class="sec">
      <h4 class="sec-hdr">Evidencia fotográfica</h4>
      <label class="drop-zone">
        <input type="file" accept="image/*" multiple onchange={onFotosChange} />
        <i class="bi bi-cloud-arrow-up"></i>
        <span>Clic para subir fotos del proyecto</span>
        <small>JPG, PNG — múltiples archivos permitidos</small>
      </label>
      {#if previews.length}
        <div class="foto-previews">
          {#each previews as src, i}
            <div class="foto-prev-item">
              <img {src} alt="preview" />
              <button onclick={() => quitarFoto(i)}><i class="bi bi-x"></i></button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Botones -->
    <div class="form-actions">
      <a href="/proyectos" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Crear proyecto{/if}
      </button>
    </div>
  </div>
</div>

<style>

</style>
