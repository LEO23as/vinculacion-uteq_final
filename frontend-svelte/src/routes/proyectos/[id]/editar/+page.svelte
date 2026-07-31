<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import MapaSelector from '$lib/MapaSelector.svelte';
  import OdsPicker from '$lib/OdsPicker.svelte';

  const id = $derived($page.params.id);

  let facultades = $state([]);
  let carrerasFil = $state([]);
  let periodos = $state([]);
  let fotosExist = $state([]);
  let ubicaciones = $state([]);
  let odsSeleccionados = $state([]);
  let documentos = $state([]);            // documentos ya subidos
  let loading = $state(true);
  let saving = $state(false);
  let subiendo = $state(false);
  let error = $state('');

  let paso = $state(1);

  const PASOS = [
    { n: 1, label: 'Datos del proyecto', icon: 'bi-clipboard-data' },
    { n: 2, label: 'Resolución de aprobación', icon: 'bi-file-earmark-check' },
    { n: 3, label: 'Planificación', icon: 'bi-diagram-3' },
    { n: 4, label: 'Convenios', icon: 'bi-people' },
  ];

  let form = $state({
    codigo:'', nombre:'', nombre_corto:'', id_facultad:'', id_carrera:'', id_periodo_inicio:'',
    director_nombre:'', director_correo:'', estado:'EN_EJECUCION',
    linea_vinculacion:'', programa:'', area_conocimiento:'', sub_area_conocimiento:'',
    objetivo_general:'', fecha_inicio:'', fecha_fin_planificada:'', ods:'',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', observaciones:'',
  });
  let nuevasFotos = $state([]);
  let previews = $state([]);
  let resolForm = $state({ resolucion_aprobacion:'', fecha_aprobacion:'' });
  let resolFile = $state(null);
  let planFile  = $state(null);

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    try {
      const [pers, data] = await Promise.all([
        fetchAPI('/api/periodos/'),
        fetch(`/api/proyectos/${id}/edit/`, { credentials:'include' }).then(r => r.json()),
      ]);
      periodos = pers;
      for (const k of Object.keys(form)) if (data[k] != null) form[k] = String(data[k] ?? '');
      form.id_facultad = String(data.id_facultad || '');
      form.id_carrera = String(data.id_carrera || '');
      form.id_periodo_inicio = String(data.id_periodo_inicio || '');
      fotosExist = data.fotos || [];
      ubicaciones = data.ubicaciones || [];
      odsSeleccionados = (String(data.ods || '').match(/\d+/g) || []).map(Number);
      resolForm.resolucion_aprobacion = data.resolucion_aprobacion || '';
      resolForm.fecha_aprobacion = data.fecha_aprobacion || '';
      if (form.id_periodo_inicio) {
        facultades = await fetchAPI(`/api/facultades-periodo/?periodo=${form.id_periodo_inicio}`);
        if (form.id_facultad)
          carrerasFil = await fetchAPI(`/api/carreras-periodo/?periodo=${form.id_periodo_inicio}&facultad=${form.id_facultad}`);
      }
      await cargarDocumentos();
    } catch { toast.error('No se pudo cargar el proyecto'); }
    finally { loading = false; }
  });

  async function cargarDocumentos() {
    try { documentos = await fetchAPI(`/api/proyectos/${id}/documentos/`); } catch { documentos = []; }
  }
  const docPorTipo = (codigo) => documentos.find(d => d.codigo_tipo === codigo);

  async function onPeriodoChange() {
    form.id_facultad = ''; form.id_carrera = ''; facultades = []; carrerasFil = [];
    if (!form.id_periodo_inicio) return;
    facultades = await fetchAPI(`/api/facultades-periodo/?periodo=${form.id_periodo_inicio}`);
  }
  async function onFacultadChange() {
    form.id_carrera = ''; carrerasFil = [];
    if (!form.id_facultad || !form.id_periodo_inicio) return;
    carrerasFil = await fetchAPI(`/api/carreras-periodo/?periodo=${form.id_periodo_inicio}&facultad=${form.id_facultad}`);
  }

  function onFotosChange(e) {
    const files = Array.from(e.target.files);
    nuevasFotos = [...nuevasFotos, ...files];
    files.forEach(f => { const r = new FileReader(); r.onload = ev => previews = [...previews, ev.target.result]; r.readAsDataURL(f); });
  }
  function quitarNueva(i) { nuevasFotos = nuevasFotos.filter((_,x)=>x!==i); previews = previews.filter((_,x)=>x!==i); }
  async function eliminarFotoExist(idFoto) {
    try { await fetch(`/api/proyectos/fotos/${idFoto}/`, { method:'DELETE', credentials:'include' });
      fotosExist = fotosExist.filter(f => f.id !== idFoto); toast.success('Foto eliminada');
    } catch { toast.error('No se pudo eliminar la foto'); }
  }

  function pickResol(e){ resolFile = e.target.files[0] || null; }
  function pickPlan(e){ planFile = e.target.files[0] || null; }

  // ── Paso 1: guardar la ficha ────────────────────────────────────
  async function guardarPaso1() {
    error = '';
    if (!form.codigo || !form.nombre || !form.id_facultad || !form.id_carrera || !form.id_periodo_inicio) {
      error = 'Código, título, período, facultad y carrera son obligatorios.'; toast.error(error); return;
    }
    if (form.fecha_inicio && form.fecha_fin_planificada && form.fecha_fin_planificada <= form.fecha_inicio) {
      error = 'La fecha de finalización debe ser posterior a la de inicio.'; toast.error(error); return;
    }
    if (ubicaciones.length) {
      const pr = ubicaciones.find(u => u.es_principal) || ubicaciones[0];
      form.latitud = pr.latitud; form.longitud = pr.longitud;
      form.provincia = pr.provincia || ''; form.canton = pr.canton || '';
      form.parroquia = pr.parroquia || ''; form.sector = pr.sector || '';
    }
    form.ods = odsSeleccionados.map(n => 'ODS ' + n).join(', ');
    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      fd.append('ubicaciones', JSON.stringify(ubicaciones));
      nuevasFotos.forEach(f => fd.append('fotos', f));
      const res = await fetch(`/api/proyectos/${id}/edit/`, { method:'POST', credentials:'include', body:fd });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; toast.error(error); return; }
      nuevasFotos = []; previews = [];
      toast.success('Datos del proyecto guardados');
      paso = 2;
    } catch { error = 'Error de conexión'; toast.error(error); }
    finally { saving = false; }
  }

  async function subirDoc(codigo_tipo, file, extra = {}) {
    const fd = new FormData();
    fd.append('codigo_tipo', codigo_tipo);
    if (file) fd.append('archivo', file);
    Object.entries(extra).forEach(([k,v]) => { if (v) fd.append(k, v); });
    const res = await fetch(`/api/proyectos/${id}/documentos/subir/`, { method:'POST', credentials:'include', body: fd });
    if (!res.ok) { const d = await res.json().catch(()=>({})); throw new Error(d.error || 'Error al subir'); }
    return res.json();
  }

  async function guardarPaso2() {
    error = '';
    if (!resolFile && !resolForm.resolucion_aprobacion && !resolForm.fecha_aprobacion) { paso = 3; return; }
    subiendo = true;
    try {
      await subirDoc('DOC_01', resolFile, { resolucion_aprobacion: resolForm.resolucion_aprobacion, fecha_aprobacion: resolForm.fecha_aprobacion });
      resolFile = null; await cargarDocumentos();
      toast.success('Resolución de aprobación guardada');
      paso = 3;
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  async function guardarPaso3() {
    error = ''; subiendo = true;
    try {
      if (planFile) { await subirDoc('DOC_02', planFile); planFile = null; await cargarDocumentos(); toast.success('Planificación guardada'); }
      paso = 4;
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  async function eliminarDoc(idDoc) {
    try { await fetch(`/api/documentos/${idDoc}/`, { method:'DELETE', credentials:'include' });
      await cargarDocumentos(); toast.success('Documento eliminado');
    } catch { toast.error('No se pudo eliminar'); }
  }

  function finalizar() { toast.success('Cambios guardados'); goto('/proyectos/' + id); }
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
  <div class="stepper">
    {#each PASOS as p}
      <button class="step" class:activo={paso === p.n} class:hecho={paso > p.n} onclick={() => paso = p.n}>
        <div class="step-circle">{#if paso > p.n}<i class="bi bi-check-lg"></i>{:else}{p.n}{/if}</div>
        <span class="step-label">{p.label}</span>
      </button>
      {#if p.n < 4}<div class="step-line" class:hecho={paso > p.n}></div>{/if}
    {/each}
  </div>

  <div class="form-card">
    {#if error}<div class="alert-error">{error}</div>{/if}

    <!-- PASO 1: FICHA -->
    {#if paso === 1}
      <h2 class="form-title"><i class="bi bi-pencil-square"></i> Datos del proyecto</h2>

      <div class="sec">
        <h4 class="sec-hdr">Identificación</h4>
        <div class="grid-row">
          <div class="field col-4"><label>Código *</label><input bind:value={form.codigo} /></div>
          <div class="field col-8"><label>Título del proyecto *</label><input bind:value={form.nombre} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Clasificación</h4>
        <div class="grid-row">
          <div class="field col-6"><label>Línea de investigación</label><input bind:value={form.linea_vinculacion} /></div>
          <div class="field col-6"><label>Programa</label><input bind:value={form.programa} /></div>
          <div class="field col-6"><label>Campo amplio</label><input bind:value={form.area_conocimiento} /></div>
          <div class="field col-6"><label>Campo específico</label><input bind:value={form.sub_area_conocimiento} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Datos académicos</h4>
        <div class="grid-row">
          <div class="field col-3">
            <label>Período *</label>
            <select bind:value={form.id_periodo_inicio} onchange={onPeriodoChange}>
              <option value="">— Seleccionar —</option>
              {#each periodos as p}<option value={String(p.id_periodo)}>{p.codigo}</option>{/each}
            </select>
          </div>
          <div class="field col-5">
            <label>Facultad *</label>
            <select bind:value={form.id_facultad} onchange={onFacultadChange} disabled={!form.id_periodo_inicio}>
              <option value="">— Seleccionar —</option>
              {#each facultades as f}<option value={String(f.id_facultad)}>{f.nombre} ({f.codigo})</option>{/each}
            </select>
          </div>
          <div class="field col-4">
            <label>Carrera *</label>
            <select bind:value={form.id_carrera} disabled={!carrerasFil.length}>
              <option value="">— Seleccionar —</option>
              {#each carrerasFil as c}<option value={String(c.id_carrera)}>{c.nombre}</option>{/each}
            </select>
          </div>
          <div class="field col-5"><label>Director del proyecto</label><input bind:value={form.director_nombre} /></div>
          <div class="field col-4"><label>Correo del director</label><input type="email" bind:value={form.director_correo} /></div>
          <div class="field col-3">
            <label>Estado</label>
            <select bind:value={form.estado}>{#each ESTADOS as e}<option value={e}>{ESTADOS_LABEL[e]}</option>{/each}</select>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Objetivo y fechas</h4>
        <div class="grid-row">
          <div class="field col-12"><label>Objetivo general</label><textarea rows="2" bind:value={form.objetivo_general}></textarea></div>
          <div class="field col-4"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
          <div class="field col-4"><label>Fecha de finalización</label><input type="date" bind:value={form.fecha_fin_planificada} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Objetivos de Desarrollo Sostenible (ODS)</h4>
        <OdsPicker bind:seleccionados={odsSeleccionados} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Ubicación geográfica <span class="sec-note">— busca o marca en el mapa (uno o varios lugares)</span></h4>
        <MapaSelector bind:ubicaciones={ubicaciones} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Fotos</h4>
        {#if fotosExist.length}
          <div class="fotos-existentes">
            {#each fotosExist as f}
              <div class="foto-exist"><img src={f.url} alt={f.titulo} /><button onclick={() => eliminarFotoExist(f.id)}><i class="bi bi-x"></i></button></div>
            {/each}
          </div>
        {/if}
        <label class="drop-zone">
          <input type="file" accept="image/*" multiple onchange={onFotosChange} />
          <i class="bi bi-cloud-arrow-up"></i><span>Agregar más fotos</span><small>JPG, PNG</small>
        </label>
        {#if previews.length}
          <div class="foto-previews">
            {#each previews as src, i}<div class="foto-prev-item"><img {src} alt="preview" /><button onclick={() => quitarNueva(i)}><i class="bi bi-x"></i></button></div>{/each}
          </div>
        {/if}
      </div>

      <div class="form-actions between">
        <a href="/proyectos/{id}" class="btn-cancel">Cancelar</a>
        <button class="btn-save" onclick={guardarPaso1} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- PASO 2: RESOLUCIÓN -->
    {:else if paso === 2}
      <h2 class="form-title"><i class="bi bi-file-earmark-check"></i> Resolución de aprobación</h2>
      <p class="paso-desc">Datos y PDF de la resolución que aprobó el proyecto (DOC_01).</p>
      {#if docPorTipo('DOC_01')}
        <div class="doc-existe">
          <i class="bi bi-file-earmark-pdf"></i>
          <a href={docPorTipo('DOC_01').url} target="_blank">{docPorTipo('DOC_01').nombre}</a>
          <span class="doc-kb">{docPorTipo('DOC_01').tamanio_kb} KB</span>
          <button class="doc-del" onclick={() => eliminarDoc(docPorTipo('DOC_01').id)} title="Eliminar"><i class="bi bi-trash"></i></button>
        </div>
      {/if}
      <div class="sec">
        <div class="grid-row">
          <div class="field col-8"><label>Referencia de la resolución</label><input bind:value={resolForm.resolucion_aprobacion} placeholder="Consejo Directivo FCA — Sesión 04/03/2021, Res. OCTAVA" /></div>
          <div class="field col-4"><label>Fecha de aprobación</label><input type="date" bind:value={resolForm.fecha_aprobacion} /></div>
        </div>
        <label class="drop-zone doc">
          <input type="file" accept="application/pdf,image/*" onchange={pickResol} />
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span>{resolFile ? resolFile.name : (docPorTipo('DOC_01') ? 'Reemplazar el PDF' : 'Subir el PDF de la resolución')}</span>
          <small>PDF o imagen</small>
        </label>
      </div>
      <div class="form-actions between">
        <button class="btn-cancel" onclick={() => paso = 1}><i class="bi bi-arrow-left"></i> Atrás</button>
        <button class="btn-save" onclick={guardarPaso2} disabled={subiendo}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- PASO 3: PLANIFICACIÓN -->
    {:else if paso === 3}
      <h2 class="form-title"><i class="bi bi-diagram-3"></i> Planificación de actividades</h2>
      <p class="paso-desc">PDF de la planificación de actividades (DOC_02).</p>
      {#if docPorTipo('DOC_02')}
        <div class="doc-existe">
          <i class="bi bi-file-earmark-pdf"></i>
          <a href={docPorTipo('DOC_02').url} target="_blank">{docPorTipo('DOC_02').nombre}</a>
          <span class="doc-kb">{docPorTipo('DOC_02').tamanio_kb} KB</span>
          <button class="doc-del" onclick={() => eliminarDoc(docPorTipo('DOC_02').id)} title="Eliminar"><i class="bi bi-trash"></i></button>
        </div>
      {/if}
      <div class="sec">
        <label class="drop-zone doc">
          <input type="file" accept="application/pdf,image/*" onchange={pickPlan} />
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span>{planFile ? planFile.name : (docPorTipo('DOC_02') ? 'Reemplazar el PDF' : 'Subir el PDF de planificación')}</span>
          <small>PDF o imagen</small>
        </label>
      </div>
      <div class="form-actions between">
        <button class="btn-cancel" onclick={() => paso = 2}><i class="bi bi-arrow-left"></i> Atrás</button>
        <button class="btn-save" onclick={guardarPaso3} disabled={subiendo}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- PASO 4: CONVENIOS -->
    {:else}
      <div class="paso-pendiente">
        <div class="pp-icon"><i class="bi bi-check-circle-fill"></i></div>
        <h2 class="form-title">Cambios guardados</h2>
        <p class="pp-sub">El paso de <strong>Convenios</strong> (buscar o crear entidad + subir el PDF del convenio) se habilita en la próxima entrega.</p>
        <div class="form-actions center">
          <button class="btn-cancel" onclick={() => paso = 3}><i class="bi bi-arrow-left"></i> Atrás</button>
          <button class="btn-save" onclick={finalizar}>Ver el proyecto <i class="bi bi-arrow-right"></i></button>
        </div>
      </div>
    {/if}
  </div>
</div>
{/if}

<style>
  .sec-note { font-size:.72rem; font-weight:600; color:var(--gris); }
  .loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center; }

  .stepper { display:flex; align-items:center; justify-content:center; margin:0 auto 18px; max-width:820px; padding:0 10px; }
  .step { display:flex; flex-direction:column; align-items:center; gap:6px; flex-shrink:0; background:none; border:none; cursor:pointer; font-family:inherit; }
  .step-circle { width:34px; height:34px; border-radius:50%; background:#eee; color:#999; font-weight:800; font-size:.9rem;
    display:flex; align-items:center; justify-content:center; border:2px solid #e0e0e0; transition:all .2s; }
  .step-label { font-size:.72rem; font-weight:700; color:#aaa; text-align:center; max-width:96px; line-height:1.2; }
  .step.activo .step-circle { background:var(--verde); color:#fff; border-color:var(--verde); }
  .step.activo .step-label { color:var(--verde); }
  .step.hecho .step-circle { background:var(--verde-claro); color:var(--verde); border-color:var(--verde); }
  .step.hecho .step-label { color:var(--verde); }
  .step-line { flex:1; height:2px; background:#e0e0e0; margin:0 6px 22px; min-width:24px; }
  .step-line.hecho { background:var(--verde); }

  .form-actions.between { justify-content:space-between; }
  .form-actions.center { justify-content:center; gap:12px; }
  .btn-save i, .btn-cancel i { font-size:.9rem; }
  .paso-desc { font-size:.86rem; color:#666; line-height:1.5; margin:-4px 0 14px; }
  .drop-zone.doc { margin-top:12px; }

  .doc-existe { display:flex; align-items:center; gap:10px; background:#f6fbf2; border:1px solid #cfe6c2; border-radius:10px; padding:10px 14px; margin-bottom:6px; }
  .doc-existe > i { color:#c0392b; font-size:1.2rem; }
  .doc-existe a { flex:1; font-size:.84rem; font-weight:700; color:var(--verde); text-decoration:none; word-break:break-all; }
  .doc-existe a:hover { text-decoration:underline; }
  .doc-kb { font-size:.7rem; color:var(--gris); font-weight:700; }
  .doc-del { background:none; border:none; color:#bbb; font-size:.9rem; cursor:pointer; padding:4px; border-radius:6px; }
  .doc-del:hover { background:#fdecec; color:#dc3545; }

  .paso-pendiente { text-align:center; padding:20px 10px 10px; }
  .pp-icon { font-size:2.6rem; color:var(--verde); margin-bottom:8px; }
  .pp-sub { font-size:.86rem; color:#666; max-width:520px; margin:6px auto 20px; line-height:1.5; }

  @keyframes spin { to { transform:rotate(360deg); } }
  .spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
