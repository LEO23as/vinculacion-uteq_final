<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

    const id = $derived($page.params.id);
  let tipos = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({
    nombre:'', nombre_corto:'', id_tipo:'', ruc:'', sector:'', telefono:'', correo:'', pagina_web:'',
    representante_legal:'', cargo_representante:'',
    provincia:'', canton:'', parroquia:'', direccion:'', observaciones:'', activo:true,
  });

  onMount(async () => {
    try {
      const [tipoData, data] = await Promise.all([
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
        fetch(`/api/entidades/${id}/`, { credentials:'include' }).then(r => r.json()),
      ]);
      tipos = tipoData.tipos || [];
      form = {
        nombre: data.nombre, nombre_corto: data.nombre_corto || '', id_tipo: String(data.id_tipo || ''),
        ruc: data.ruc || '', sector: data.sector || '', telefono: data.telefono || '',
        correo: data.correo || '', pagina_web: data.pagina_web || '',
        representante_legal: data.representante_legal || '', cargo_representante: data.cargo_representante || '',
        provincia: data.provincia || '', canton: data.canton || '', parroquia: data.parroquia || '',
        direccion: data.direccion || '', observaciones: data.observaciones || '', activo: data.activo,
      };
    } finally { loading = false; }
  });

  async function guardar() {
    error = ''; saving = true;
    try {
      const res = await fetch(`/api/entidades/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/entidades');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Entidad — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/entidades">Entidades</a><span class="sep">/</span>
    <span class="current">Editar</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-building"></i> Editar Entidad Cooperante</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Información general</h4>
      <div class="grid-row">
        <div class="field col-6"><label>Nombre completo *</label><input bind:value={form.nombre} /></div>
        <div class="field col-3"><label>Nombre corto</label><input bind:value={form.nombre_corto} /></div>
        <div class="field col-3">
          <label>Tipo *</label>
          <select bind:value={form.id_tipo}>
            {#each tipos as t}
              <option value={String(t.id_tipo)}>{t.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-3"><label>RUC</label><input bind:value={form.ruc} /></div>
        <div class="field col-3"><label>Sector</label><input bind:value={form.sector} /></div>
        <div class="field col-3"><label>Teléfono</label><input bind:value={form.telefono} /></div>
        <div class="field col-3"><label>Correo</label><input type="email" bind:value={form.correo} /></div>
        <div class="field col-4"><label>Página web</label><input bind:value={form.pagina_web} /></div>
      </div>
    </div>

    <div class="sec">
      <h4 class="sec-hdr">Representante</h4>
      <div class="grid-row">
        <div class="field col-5"><label>Representante legal</label><input bind:value={form.representante_legal} /></div>
        <div class="field col-4"><label>Cargo</label><input bind:value={form.cargo_representante} /></div>
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
      <h4 class="sec-hdr">Estado</h4>
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
        {#if saving}<i class="bi bi-arrow-repeat spin"></i>{:else}Guardar cambios{/if}
      </button>
    </div>
  </div>
</div>
{/if}

<style>

.loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);padding:40px;justify-content:center; }
.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
