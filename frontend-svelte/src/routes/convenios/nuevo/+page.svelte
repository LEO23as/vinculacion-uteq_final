<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    let proyectos = $state([]);
  let entidades = $state([]);
  let periodos = $state([]);
  let saving = $state(false);
  let error = $state('');

  let form = $state({
    id_proyecto:'', id_entidad:'', id_periodo:'', numero_memorando:'',
    estado:'VIGENTE', fecha_firma:'', fecha_inicio:'', fecha_fin:'',
    duracion_anios:2, estudiantes_asignados:'', observaciones:'',
  });

  const ESTADOS = ['VIGENTE','VENCIDO','RENOVADO','CANCELADO'];

  onMount(async () => {
    [proyectos, entidades, periodos] = await Promise.all([
      fetchAPI('/api/proyectos/'),
      fetchAPI('/api/entidades/'),
      fetchAPI('/api/periodos/'),
    ]);
    // Pre-seleccionar proyecto desde query param
    const proyId = $page.url.searchParams.get('proyecto');
    if (proyId) form.id_proyecto = proyId;
  });

  async function guardar() {
    error = '';
    if (!form.id_proyecto || !form.id_entidad) {
      error = 'Proyecto y entidad son obligatorios.';
      return;
    }
    saving = true;
    try {
      const res = await fetch('/api/convenios/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear convenio'; return; }
      goto('/convenios/' + data.id_convenio);
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Nuevo Convenio — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/convenios">Convenios</a><span class="sep">/</span>
    <span class="current">Nuevo</span><span class="sep">/</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-file-earmark-plus"></i> Nuevo Convenio</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Vinculación</h4>
      <div class="grid-row">
        <div class="field col-6">
          <label>Proyecto *</label>
          <select bind:value={form.id_proyecto}>
            <option value="">— Seleccionar proyecto —</option>
            {#each proyectos as p}
              <option value={p.id_proyecto}>{p.codigo} — {p.nombre_corto || p.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-6">
          <label>Entidad Cooperante *</label>
          <select bind:value={form.id_entidad}>
            <option value="">— Seleccionar entidad —</option>
            {#each entidades as e}
              <option value={e.id_entidad}>{e.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4">
          <label>Período Académico</label>
          <select bind:value={form.id_periodo}>
            <option value="">— Seleccionar —</option>
            {#each periodos as p}
              <option value={p.id_periodo}>{p.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4">
          <label>N° Memorando</label>
          <input bind:value={form.numero_memorando} placeholder="VCL-2025-001" />
        </div>
        <div class="field col-4">
          <label>Estado *</label>
          <select bind:value={form.estado}>
            {#each ESTADOS as e}
              <option value={e}>{e}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Fechas y duración</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Fecha de firma</label><input type="date" bind:value={form.fecha_firma} /></div>
        <div class="field col-3"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
        <div class="field col-3"><label>Fecha de fin</label><input type="date" bind:value={form.fecha_fin} /></div>
        <div class="field col-3"><label>Duración (años)</label><input type="number" min="1" max="10" bind:value={form.duracion_anios} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Participantes y observaciones</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Estudiantes asignados</label><input type="number" min="0" bind:value={form.estudiantes_asignados} /></div>
        <div class="field col-9"><label>Observaciones</label><textarea rows="2" bind:value={form.observaciones}></textarea></div>
      </div>
    </div>

    <div class="form-actions">
      <a href="/convenios" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Crear convenio{/if}
      </button>
    </div>
  </div>
</div>

<style>

</style>
