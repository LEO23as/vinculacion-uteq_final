<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';
  import MapaSelector from '$lib/MapaSelector.svelte';
  import OdsPicker from '$lib/OdsPicker.svelte';

  let facultades = $state([]);
  let periodos   = $state([]);
  let carrerasFil = $state([]);
  let ubicaciones = $state([]);

  let paso = $state(1);                 // 1..4
  let proyectoId = $state(null);        // se define al guardar el paso 1
  let saving = $state(false);
  let error  = $state('');

  const PASOS = [
    { n: 1, label: 'Datos del proyecto', icon: 'bi-clipboard-data' },
    { n: 2, label: 'Resolución de aprobación', icon: 'bi-file-earmark-check' },
    { n: 3, label: 'Planificación', icon: 'bi-diagram-3' },
    { n: 4, label: 'Convenios', icon: 'bi-people' },
  ];

  let form = $state({
    codigo:'', nombre:'', id_periodo_inicio:'', id_facultad:'', id_carrera:'',
    director_nombre:'', director_correo:'', estado:'EN_EJECUCION',
    linea_vinculacion:'', area_conocimiento:'', sub_area_conocimiento:'', programa:'',
    objetivo_general:'', fecha_inicio:'', fecha_fin_planificada:'', ods:'',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', observaciones:'', nombre_corto:'',
  });
  let fotos = $state([]);
  let previews = $state([]);
  let odsSeleccionados = $state([]);   // números de ODS elegidos

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    periodos = await fetchAPI('/api/periodos/');
  });

  async function onPeriodoChange() {
    form.id_facultad = ''; form.id_carrera = '';
    facultades = []; carrerasFil = [];
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

  // ── Paso 1: crear el proyecto ───────────────────────────────────
  async function guardarPaso1() {
    error = '';
    if (!form.codigo || !form.nombre || !form.id_facultad || !form.id_carrera || !form.id_periodo_inicio) {
      error = 'Código, título, período, facultad y carrera son obligatorios.';
      return;
    }
    if (!ubicaciones.length) { error = 'Agrega al menos una ubicación en el mapa.'; return; }
    const principal = ubicaciones.find(u => u.es_principal) || ubicaciones[0];
    form.latitud = principal.latitud; form.longitud = principal.longitud;
    form.provincia = principal.provincia || ''; form.canton = principal.canton || '';
    form.parroquia = principal.parroquia || ''; form.sector = principal.sector || '';
    form.ods = odsSeleccionados.map(n => 'ODS ' + n).join(', ');

    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      fd.append('ubicaciones', JSON.stringify(ubicaciones));
      fotos.forEach(f => fd.append('fotos', f));
      const res = await fetch('/api/proyectos/create/', { method:'POST', credentials:'include', body: fd });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear proyecto'; return; }
      proyectoId = data.id_proyecto;
      paso = 2;
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }

  function finalizar() { goto('/proyectos/' + proyectoId); }
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
  <!-- INDICADOR DE PASOS -->
  <div class="stepper">
    {#each PASOS as p}
      <div class="step" class:activo={paso === p.n} class:hecho={paso > p.n}>
        <div class="step-circle">
          {#if paso > p.n}<i class="bi bi-check-lg"></i>{:else}{p.n}{/if}
        </div>
        <span class="step-label">{p.label}</span>
      </div>
      {#if p.n < 4}<div class="step-line" class:hecho={paso > p.n}></div>{/if}
    {/each}
  </div>

  <div class="form-card">
    {#if error}<div class="alert-error">{error}</div>{/if}

    <!-- ══════════ PASO 1: FICHA ══════════ -->
    {#if paso === 1}
      <h2 class="form-title"><i class="bi bi-clipboard-data"></i> Datos del proyecto</h2>

      <div class="sec">
        <h4 class="sec-hdr">Identificación</h4>
        <div class="grid-row">
          <div class="field col-4">
            <label>Código *</label>
            <input bind:value={form.codigo} placeholder="PVSUTEQ-FCAP-02" />
            <small>Formato: PVSUTEQ-[COD_FAC]-[NUM]</small>
          </div>
          <div class="field col-8">
            <label>Título del proyecto *</label>
            <input bind:value={form.nombre} placeholder="Implementación de huertos productivos de plantas aromáticas…" />
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Clasificación</h4>
        <div class="grid-row">
          <div class="field col-6"><label>Línea de investigación</label><input bind:value={form.linea_vinculacion} placeholder="Agricultura, Silvicultura y Producción animal" /></div>
          <div class="field col-6"><label>Programa</label><input bind:value={form.programa} placeholder="Gestión de proyectos de vinculación con la sociedad" /></div>
          <div class="field col-6"><label>Campo amplio</label><input bind:value={form.area_conocimiento} placeholder="Agricultura, Silvicultura, Pesca y Veterinaria" /></div>
          <div class="field col-6"><label>Campo específico</label><input bind:value={form.sub_area_conocimiento} placeholder="Agricultura" /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Datos académicos</h4>
        <div class="grid-row">
          <div class="field col-3">
            <label>Período *</label>
            <select bind:value={form.id_periodo_inicio} onchange={onPeriodoChange}>
              <option value="">— Seleccionar —</option>
              {#each periodos as p}<option value={p.id_periodo}>{p.codigo}</option>{/each}
            </select>
            <small>Define la estructura histórica</small>
          </div>
          <div class="field col-5">
            <label>Facultad *</label>
            <select bind:value={form.id_facultad} onchange={onFacultadChange} disabled={!form.id_periodo_inicio}>
              <option value="">{form.id_periodo_inicio ? '— Seleccionar —' : '— Elija período primero —'}</option>
              {#each facultades as f}
                <option value={f.id_facultad}>{f.nombre} ({f.codigo})</option>
              {/each}
            </select>
          </div>
          <div class="field col-4">
            <label>Carrera *</label>
            <select bind:value={form.id_carrera} disabled={!carrerasFil.length}>
              <option value="">— Seleccionar facultad primero —</option>
              {#each carrerasFil as c}<option value={c.id_carrera}>{c.nombre}</option>{/each}
            </select>
          </div>
          <div class="field col-5"><label>Director del proyecto</label><input bind:value={form.director_nombre} placeholder="Ing. Moisés Menace, MSc." /></div>
          <div class="field col-4"><label>Correo del director</label><input type="email" bind:value={form.director_correo} placeholder="mmenace@uteq.edu.ec" /></div>
          <div class="field col-3">
            <label>Estado *</label>
            <select bind:value={form.estado}>{#each ESTADOS as e}<option value={e}>{ESTADOS_LABEL[e]}</option>{/each}</select>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Objetivo y fechas</h4>
        <div class="grid-row">
          <div class="field col-12"><label>Objetivo general</label><textarea rows="2" bind:value={form.objetivo_general} placeholder="Elaborar abonos orgánicos para producir huertos hortícolas…"></textarea></div>
          <div class="field col-4"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
          <div class="field col-4"><label>Fecha de finalización</label><input type="date" bind:value={form.fecha_fin_planificada} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Objetivos de Desarrollo Sostenible (ODS) <span class="sec-note">— marca los que atiende el proyecto</span></h4>
        <OdsPicker bind:seleccionados={odsSeleccionados} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Ubicación geográfica <span class="sec-note">— busca o marca en el mapa dónde se ejecuta (uno o varios lugares)</span></h4>
        <MapaSelector bind:ubicaciones={ubicaciones} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr">Evidencia fotográfica</h4>
        <label class="drop-zone">
          <input type="file" accept="image/*" multiple onchange={onFotosChange} />
          <i class="bi bi-cloud-arrow-up"></i>
          <span>Clic para subir fotos del proyecto</span>
          <small>JPG, PNG — múltiples archivos</small>
        </label>
        {#if previews.length}
          <div class="foto-previews">
            {#each previews as src, i}
              <div class="foto-prev-item"><img {src} alt="preview" /><button onclick={() => quitarFoto(i)}><i class="bi bi-x"></i></button></div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="form-actions">
        <a href="/proyectos" class="btn-cancel">Cancelar</a>
        <button class="btn-save" onclick={guardarPaso1} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- ══════════ PASOS 2-4: en construcción ══════════ -->
    {:else}
      <div class="paso-pendiente">
        <div class="pp-icon"><i class="bi bi-check-circle-fill"></i></div>
        <h2 class="form-title">Proyecto creado correctamente</h2>
        <p class="pp-sub">
          El paso <strong>{paso}</strong> ({PASOS[paso-1].label}) se está construyendo.
          Por ahora puedes finalizar y ver el proyecto; los pasos de documentos se habilitarán en la siguiente entrega.
        </p>
        <div class="pp-steps">
          {#each PASOS.slice(1) as p}
            <div class="pp-step">
              <i class="bi {p.icon}"></i>
              <span>{p.label}</span>
              <span class="pp-tag">próximo</span>
            </div>
          {/each}
        </div>
        <div class="form-actions center">
          <button class="btn-save" onclick={finalizar}>Ver el proyecto <i class="bi bi-arrow-right"></i></button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .sec-note { font-size:.72rem; font-weight:600; color:var(--gris); }

  /* Stepper */
  .stepper { display:flex; align-items:center; justify-content:center; gap:0; margin:0 auto 18px; max-width:820px; padding:0 10px; }
  .step { display:flex; flex-direction:column; align-items:center; gap:6px; flex-shrink:0; }
  .step-circle { width:34px; height:34px; border-radius:50%; background:#eee; color:#999; font-weight:800; font-size:.9rem;
    display:flex; align-items:center; justify-content:center; border:2px solid #e0e0e0; transition:all .2s; }
  .step-label { font-size:.72rem; font-weight:700; color:#aaa; text-align:center; max-width:96px; line-height:1.2; }
  .step.activo .step-circle { background:var(--verde); color:#fff; border-color:var(--verde); }
  .step.activo .step-label { color:var(--verde); }
  .step.hecho .step-circle { background:var(--verde-claro); color:var(--verde); border-color:var(--verde); }
  .step.hecho .step-label { color:var(--verde); }
  .step-line { flex:1; height:2px; background:#e0e0e0; margin:0 6px; margin-bottom:22px; min-width:24px; }
  .step-line.hecho { background:var(--verde); }

  .btn-save i { font-size:.9rem; }
  .form-actions.center { justify-content:center; }

  /* Pasos pendientes */
  .paso-pendiente { text-align:center; padding:20px 10px 10px; }
  .pp-icon { font-size:2.6rem; color:var(--verde); margin-bottom:8px; }
  .pp-sub { font-size:.86rem; color:#666; max-width:520px; margin:6px auto 20px; line-height:1.5; }
  .pp-steps { display:flex; flex-direction:column; gap:8px; max-width:360px; margin:0 auto 22px; }
  .pp-step { display:flex; align-items:center; gap:10px; padding:10px 14px; border:1px solid var(--borde); border-radius:10px; background:#fafbfa; }
  .pp-step i { color:var(--verde); font-size:1.05rem; }
  .pp-step span:nth-child(2) { flex:1; text-align:left; font-size:.85rem; font-weight:700; color:#444; }
  .pp-tag { font-size:.62rem; font-weight:800; color:var(--dorado); background:#fff8e6; padding:2px 8px; border-radius:20px; }
</style>
