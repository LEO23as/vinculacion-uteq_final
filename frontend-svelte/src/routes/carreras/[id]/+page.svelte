<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    const id = $derived($page.params.id);
  let facultades = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({ nombre:'', codigo:'', id_facultad:'', horas_vinculacion:160, area_conocimiento:'', activo:true });

  onMount(async () => {
    try {
      const [facs, data] = await Promise.all([
        fetchAPI('/api/facultades/'),
        fetch(`/api/carreras/${id}/`, { credentials:'include' }).then(r => r.json()),
      ]);
      facultades = facs;
      form = {
        nombre:data.nombre, codigo:data.codigo||'',
        id_facultad:String(data.id_facultad||''),
        horas_vinculacion:data.horas_vinculacion||160,
        area_conocimiento:data.area_conocimiento||'', activo:data.activo,
      };
    } finally { loading = false; }
  });

  async function guardar() {
    error = ''; saving = true;
    try {
      const res = await fetch(`/api/carreras/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/facultades');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Carrera — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/facultades">Facultades</a><span class="sep">/</span>
    <span class="current">Editar carrera</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="lw"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-book"></i> Editar Carrera</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}
    <div class="sec">
      <h4 class="sec-hdr">Datos de la carrera</h4>
      <div class="grid-row">
        <div class="field col-8"><label>Nombre *</label><input bind:value={form.nombre} /></div>
        <div class="field col-4"><label>Código</label><input bind:value={form.codigo} /></div>
        <div class="field col-8">
          <label>Facultad *</label>
          <select bind:value={form.id_facultad}>
            {#each facultades as f}
              <option value={String(f.id_facultad)}>{f.nombre_corto || f.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4"><label>Horas vinculación</label><input type="number" bind:value={form.horas_vinculacion} /></div>
        <div class="field col-12"><label>Área de conocimiento</label><input bind:value={form.area_conocimiento} /></div>
        <div class="field col-4" style="justify-content:flex-end;padding-bottom:4px">
          <label class="check-label"><input type="checkbox" bind:checked={form.activo} />Carrera activa</label>
        </div>
      </div>
    </div>
    <div class="form-actions">
      <a href="/facultades" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i>{:else}Guardar cambios{/if}
      </button>
    </div>
  </div>
</div>
{/if}

<style>

.lw { display:flex;align-items:center;gap:10px;color:var(--gris);padding:40px;justify-content:center; }
.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
