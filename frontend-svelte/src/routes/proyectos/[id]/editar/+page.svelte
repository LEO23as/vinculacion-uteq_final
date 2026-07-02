<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    const id = $derived($page.params.id);

  let facultades = $state([]);
  let carrerasFil = $state([]);
  let periodos = $state([]);
  let fotosExist = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');

  let form = $state({
    codigo:'', nombre:'', nombre_corto:'', id_facultad:'', id_carrera:'',
    id_periodo_inicio:'', estado:'EN_EJECUCION',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', objetivo_general:'', ods:'', linea_vinculacion:'', observaciones:'',
  });
  let nuevasFotos = $state([]);
  let previews = $state([]);

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    try {
      const [facs, pers, data] = await Promise.all([
        fetchAPI('/api/facultades/'),
        fetchAPI('/api/periodos/'),
        fetch(`/api/proyectos/${id}/edit/`, { credentials:'include' }).then(r => r.json()),
      ]);
      facultades = facs; periodos = pers;
      form.codigo = data.codigo;
      form.nombre = data.nombre;
      form.nombre_corto = data.nombre_corto || '';
      form.id_facultad = String(data.id_facultad || '');
      form.id_carrera = String(data.id_carrera || '');
      form.id_periodo_inicio = String(data.id_periodo_inicio || '');
      form.estado = data.estado;
      form.provincia = data.provincia || '';
      form.canton = data.canton || '';
      form.parroquia = data.parroquia || '';
      form.sector = data.sector || '';
      form.latitud = data.latitud || '';
      form.longitud = data.longitud || '';
      form.descripcion = data.descripcion || '';
      form.objetivo_general = data.objetivo_general || '';
      form.ods = data.ods || '';
      form.linea_vinculacion = data.linea_vinculacion || '';
      form.observaciones = data.observaciones || '';
      fotosExist = data.fotos || [];
      if (form.id_facultad) {
        const all = await fetchAPI('/api/carreras/');
        carrerasFil = all.filter(c => String(c.id_facultad) === form.id_facultad);
      }
    } finally { loading = false; }
  });

  async function onFacultadChange() {
    form.id_carrera = '';
    if (!form.id_facultad) { carrerasFil = []; return; }
    const all = await fetchAPI('/api/carreras/');
    carrerasFil = all.filter(c => String(c.id_facultad) === String(form.id_facultad));
  }

  function onFotosChange(e) {
    const files = Array.from(e.target.files);
    nuevasFotos = [...nuevasFotos, ...files];
    files.forEach(f => {
      const reader = new FileReader();
      reader.onload = (ev) => { previews = [...previews, ev.target.result]; };
      reader.readAsDataURL(f);
    });
  }

  function quitarNueva(i) {
    nuevasFotos = nuevasFotos.filter((_,x) => x !== i);
    previews = previews.filter((_,x) => x !== i);
  }

  async function eliminarFotoExist(idFoto) {
    try {
      await fetch(`/api/proyectos/fotos/${idFoto}/`, { method:'DELETE', credentials:'include' });
      fotosExist = fotosExist.filter(f => f.id !== idFoto);
    } catch {}
  }

  async function guardar() {
    error = '';
    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      nuevasFotos.forEach(f => fd.append('fotos', f));
      const res = await fetch(`/api/proyectos/${id}/edit/`, {
        method:'POST', credentials:'include', body:fd,
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/proyectos/' + id);
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Proyecto — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/proyectos">Proyectos</a><span class="sep">/</span>
    <span class="current">Editar</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-pencil-square"></i> Editar Proyecto</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Identificación</h4>
      <div class="grid-row">
        <div class="field col-4"><label>Código *</label><input bind:value={form.codigo} /></div>
        <div class="field col-5"><label>Nombre completo *</label><input bind:value={form.nombre} /></div>
        <div class="field col-3"><label>Nombre corto</label><input bind:value={form.nombre_corto} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Datos académicos</h4>
      <div class="grid-row">
        <div class="field col-4">
          <label>Facultad *</label>
          <select bind:value={form.id_facultad} onchange={onFacultadChange}>
            <option value="">— Seleccionar —</option>
            {#each facultades as f}
              <option value={String(f.id_facultad)}>{f.nombre_corto || f.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4">
          <label>Carrera *</label>
          <select bind:value={form.id_carrera}>
            <option value="">— Seleccionar —</option>
            {#each carrerasFil as c}
              <option value={String(c.id_carrera)}>{c.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-2">
          <label>Período *</label>
          <select bind:value={form.id_periodo_inicio}>
            {#each periodos as p}
              <option value={String(p.id_periodo)}>{p.codigo}</option>
            {/each}
          </select>
        </div>
        <div class="field col-2">
          <label>Estado</label>
          <select bind:value={form.estado}>
            {#each ESTADOS as e}
              <option value={e}>{ESTADOS_LABEL[e]}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Ubicación</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Provincia</label><input bind:value={form.provincia} /></div>
        <div class="field col-3"><label>Cantón</label><input bind:value={form.canton} /></div>
        <div class="field col-3"><label>Parroquia</label><input bind:value={form.parroquia} /></div>
        <div class="field col-3"><label>Sector</label><input bind:value={form.sector} /></div>
        <div class="field col-2"><label>Latitud</label><input type="number" step="0.0000001" bind:value={form.latitud} /></div>
        <div class="field col-2"><label>Longitud</label><input type="number" step="0.0000001" bind:value={form.longitud} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Descripción</h4>
      <div class="grid-row">
        <div class="field col-6"><label>Descripción</label><textarea rows="3" bind:value={form.descripcion}></textarea></div>
        <div class="field col-6"><label>Objetivo general</label><textarea rows="3" bind:value={form.objetivo_general}></textarea></div>
        <div class="field col-4"><label>ODS</label><input bind:value={form.ods} /></div>
        <div class="field col-4"><label>Línea de vinculación</label><input bind:value={form.linea_vinculacion} /></div>
        <div class="field col-4"><label>Observaciones</label><input bind:value={form.observaciones} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Fotos existentes</h4>
      {#if fotosExist.length}
        <div class="fotos-existentes">
          {#each fotosExist as f}
            <div class="foto-exist">
              <img src={API + f.url} alt={f.titulo} />
              <button onclick={() => eliminarFotoExist(f.id)} title="Eliminar foto">
                <i class="bi bi-x"></i>
              </button>
            </div>
          {/each}
        </div>
      {:else}
        <p style="font-size:.8rem;color:var(--gris)">Sin fotos registradas.</p>
      {/if}
      <label class="drop-zone">
        <input type="file" accept="image/*" multiple onchange={onFotosChange} />
        <i class="bi bi-cloud-arrow-up"></i>
        <span>Agregar más fotos</span>
        <small>JPG, PNG — múltiples archivos</small>
      </label>
      {#if previews.length}
        <div class="foto-previews">
          {#each previews as src, i}
            <div class="foto-prev-item">
              <img {src} alt="preview" />
              <button onclick={() => quitarNueva(i)}><i class="bi bi-x"></i></button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="form-actions">
      <a href="/proyectos/{id}" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Guardar cambios{/if}
      </button>
    </div>
  </div>
</div>
{/if}

<style>

.loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center; }
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
