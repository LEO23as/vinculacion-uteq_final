<script>
  import { goto } from '$app/navigation';

    let saving = $state(false);
  let error = $state('');
  let form = $state({ codigo:'', nombre:'', tipo:'SPA', fecha_inicio:'', fecha_fin:'', activo:true });

  async function guardar() {
    error = '';
    if (!form.codigo || !form.nombre || !form.tipo || !form.fecha_inicio || !form.fecha_fin) {
      error = 'Todos los campos obligatorios deben completarse.';
      return;
    }
    saving = true;
    try {
      const res = await fetch('/api/periodos/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear período'; return; }
      goto('/periodos');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Nuevo Período — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/periodos">Períodos</a><span class="sep">/</span>
    <span class="current">Nuevo</span><span class="sep">/</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-calendar-plus"></i> Nuevo Período Académico</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Datos del período</h4>
      <div class="grid-row">
        <div class="field col-4">
          <label>Código *</label>
          <input bind:value={form.codigo} placeholder="Ej: SPA-2025-2026" />
        </div>
        <div class="field col-2">
          <label>Tipo *</label>
          <select bind:value={form.tipo}>
            <option value="SPA">SPA</option>
            <option value="PPA">PPA</option>
          </select>
        </div>
        <div class="field col-12">
          <label>Nombre completo *</label>
          <input bind:value={form.nombre} placeholder="Ej: Segundo Período Académico 2025-2026" />
        </div>
        <div class="field col-4">
          <label>Fecha de inicio *</label>
          <input type="date" bind:value={form.fecha_inicio} />
        </div>
        <div class="field col-4">
          <label>Fecha de fin *</label>
          <input type="date" bind:value={form.fecha_fin} />
        </div>
        <div class="field col-4" style="justify-content:flex-end;padding-bottom:4px">
          <label class="check-label">
            <input type="checkbox" bind:checked={form.activo} />
            Período activo
          </label>
        </div>
      </div>
    </div>

    <div class="form-actions">
      <a href="/periodos" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Crear período{/if}
      </button>
    </div>
  </div>
</div>

<style>

.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
</style>
