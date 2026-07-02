<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

    const id = $derived($page.params.id);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({ codigo:'', nombre:'', nombre_corto:'', campus:'', activo:true });

  onMount(async () => {
    const res = await fetch(`/api/facultades/${id}/`, { credentials:'include' });
    const data = await res.json();
    form = { codigo:data.codigo||'', nombre:data.nombre, nombre_corto:data.nombre_corto||'', campus:data.campus||'', activo:data.activo };
    loading = false;
  });

  async function guardar() {
    error = ''; saving = true;
    try {
      const res = await fetch(`/api/facultades/${id}/`, {
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

<svelte:head><title>Editar Facultad — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/facultades">Facultades</a><span class="sep">/</span>
    <span class="current">Editar</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="lw"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-bank"></i> Editar Facultad</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}
    <div class="sec">
      <h4 class="sec-hdr">Datos de la facultad</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Código *</label><input bind:value={form.codigo} /></div>
        <div class="field col-9"><label>Nombre completo *</label><input bind:value={form.nombre} /></div>
        <div class="field col-6"><label>Nombre corto</label><input bind:value={form.nombre_corto} /></div>
        <div class="field col-6"><label>Campus</label><input bind:value={form.campus} /></div>
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
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
