<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

    const id = $derived($page.params.id);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({ codigo:'', nombre:'', tipo:'SPA', fecha_inicio:'', fecha_fin:'', activo:true });

  onMount(async () => {
    const res = await fetch(`/api/periodos/${id}/`, { credentials:'include' });
    const data = await res.json();
    form = { codigo:data.codigo, nombre:data.nombre, tipo:data.tipo,
             fecha_inicio:data.fecha_inicio, fecha_fin:data.fecha_fin, activo:data.activo };
    loading = false;
  });

  async function guardar() {
    error = '';
    saving = true;
    try {
      const res = await fetch(`/api/periodos/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/periodos');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Período — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/periodos">Períodos</a><span class="sep">/</span>
    <span class="current">Editar</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-calendar-check"></i> Editar Período Académico</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}
    <div class="sec">
      <h4 class="sec-hdr">Datos del período</h4>
      <div class="grid-row">
        <div class="field col-4"><label>Código *</label><input bind:value={form.codigo} /></div>
        <div class="field col-2">
          <label>Tipo *</label>
          <select bind:value={form.tipo}>
            <option value="SPA">SPA</option>
            <option value="PPA">PPA</option>
          </select>
        </div>
        <div class="field col-12"><label>Nombre completo *</label><input bind:value={form.nombre} /></div>
        <div class="field col-4"><label>Fecha inicio *</label><input type="date" bind:value={form.fecha_inicio} /></div>
        <div class="field col-4"><label>Fecha fin *</label><input type="date" bind:value={form.fecha_fin} /></div>
        <div class="field col-4" style="justify-content:flex-end;padding-bottom:4px">
          <label class="check-label">
            <input type="checkbox" bind:checked={form.activo} />Período activo
          </label>
        </div>
      </div>
    </div>
    <div class="form-actions">
      <a href="/periodos" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Guardar cambios{/if}
      </button>
    </div>
  </div>
</div>
{/if}

<style>

.loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center; }
.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
