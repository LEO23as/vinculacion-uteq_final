<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    let facultades = $state([]);
  let saving = $state(false);
  let error = $state('');
  let form = $state({ nombre:'', codigo:'', id_facultad:'', horas_vinculacion:160, area_conocimiento:'', activo:true });

  onMount(async () => { facultades = await fetchAPI('/api/facultades/'); });

  async function guardar() {
    error = '';
    if (!form.nombre || !form.id_facultad) { error = 'Nombre y facultad son obligatorios.'; return; }
    saving = true;
    try {
      const res = await fetch('/api/carreras/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear carrera'; return; }
      goto('/facultades');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Nueva Carrera — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/facultades">Facultades</a><span class="sep">/</span>
    <span class="current">Nueva carrera</span><span class="sep">/</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-book-fill"></i> Nueva Carrera</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}
    <div class="sec">
      <h4 class="sec-hdr">Datos de la carrera</h4>
      <div class="grid-row">
        <div class="field col-8"><label>Nombre de la carrera *</label><input bind:value={form.nombre} placeholder="Ej: Ingeniería en Sistemas" /></div>
        <div class="field col-4"><label>Código</label><input bind:value={form.codigo} placeholder="Ej: ISI" /></div>
        <div class="field col-8">
          <label>Facultad *</label>
          <select bind:value={form.id_facultad}>
            <option value="">— Seleccionar —</option>
            {#each facultades as f}
              <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4"><label>Horas de vinculación</label><input type="number" bind:value={form.horas_vinculacion} placeholder="160" /></div>
        <div class="field col-12"><label>Área de conocimiento</label><input bind:value={form.area_conocimiento} placeholder="Ej: Tecnologías de la Información" /></div>
        <div class="field col-4" style="justify-content:flex-end;padding-bottom:4px">
          <label class="check-label"><input type="checkbox" bind:checked={form.activo} />Carrera activa</label>
        </div>
      </div>
    </div>
    <div class="form-actions">
      <a href="/facultades" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i>{:else}Crear carrera{/if}
      </button>
    </div>
  </div>
</div>

<style>

.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
</style>
