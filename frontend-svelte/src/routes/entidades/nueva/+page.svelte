<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

    let tipos = $state([]);
  let saving = $state(false);
  let error = $state('');

  let form = $state({
    nombre:'', nombre_corto:'', id_tipo:'', ruc:'', sector:'', telefono:'', correo:'', pagina_web:'',
    representante_legal:'', cargo_representante:'',
    provincia:'', canton:'', parroquia:'', direccion:'', observaciones:'', activo:true,
  });

  onMount(async () => {
    const res = await fetch('/api/entidades/create/', { credentials:'include' });
    const data = await res.json();
    tipos = data.tipos || [];
  });

  async function guardar() {
    error = '';
    if (!form.nombre || !form.id_tipo) { error = 'Nombre y tipo son obligatorios.'; return; }
    saving = true;
    try {
      const res = await fetch('/api/entidades/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear entidad'; return; }
      goto('/entidades');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Nueva Entidad — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/entidades">Entidades</a><span class="sep">/</span>
    <span class="current">Nueva</span><span class="sep">/</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-building-add"></i> Nueva Entidad Cooperante</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Información general</h4>
      <div class="grid-row">
        <div class="field col-6"><label>Nombre completo *</label><input bind:value={form.nombre} placeholder="Nombre de la entidad..." /></div>
        <div class="field col-3"><label>Nombre corto / Siglas</label><input bind:value={form.nombre_corto} placeholder="GADM, MIN..." /></div>
        <div class="field col-3">
          <label>Tipo de entidad *</label>
          <select bind:value={form.id_tipo}>
            <option value="">— Seleccionar —</option>
            {#each tipos as t}
              <option value={t.id_tipo}>{t.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-3"><label>RUC</label><input bind:value={form.ruc} maxlength="15" placeholder="1234567890001" /></div>
        <div class="field col-3"><label>Sector</label><input bind:value={form.sector} placeholder="Público, Privado..." /></div>
        <div class="field col-3"><label>Teléfono</label><input bind:value={form.telefono} /></div>
        <div class="field col-3"><label>Correo electrónico</label><input type="email" bind:value={form.correo} /></div>
        <div class="field col-4"><label>Página web</label><input bind:value={form.pagina_web} placeholder="https://..." /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Representante legal</h4>
      <div class="grid-row">
        <div class="field col-5"><label>Nombre del representante</label><input bind:value={form.representante_legal} /></div>
        <div class="field col-4"><label>Cargo</label><input bind:value={form.cargo_representante} placeholder="Alcalde, Director..." /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Ubicación</h4>
      <div class="grid-row">
        <div class="field col-3"><label>Provincia</label><input bind:value={form.provincia} /></div>
        <div class="field col-3"><label>Cantón</label><input bind:value={form.canton} /></div>
        <div class="field col-3"><label>Parroquia</label><input bind:value={form.parroquia} /></div>
        <div class="field col-6"><label>Dirección</label><input bind:value={form.direccion} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Observaciones y estado</h4>
      <div class="grid-row">
        <div class="field col-8"><label>Observaciones</label><textarea rows="2" bind:value={form.observaciones}></textarea></div>
        <div class="field col-4" style="justify-content:flex-end;padding-bottom:6px">
          <label class="check-label">
            <input type="checkbox" bind:checked={form.activo} />Entidad activa
          </label>
        </div>
      </div>
    </div>

    <div class="form-actions">
      <a href="/entidades" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}Crear entidad{/if}
      </button>
    </div>
  </div>
</div>

<style>

.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
</style>
