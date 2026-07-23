<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import WizardEstructura from '$lib/WizardEstructura.svelte';

    const id = $derived($page.params.id);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({ codigo:'', nombre:'', tipo:'SPA', fecha_inicio:'', fecha_fin:'', activo:true });

  // Estructura histórica del período
  let estructura = $state(null);       // { tiene_snapshot, facultades: [...] }
  let cargandoEst = $state(true);
  let wizardAbierto = $state(false);
  let toast = $state('');

  onMount(async () => {
    const res = await fetch(`/api/periodos/${id}/`, { credentials:'include' });
    const data = await res.json();
    form = { codigo:data.codigo, nombre:data.nombre, tipo:data.tipo,
             fecha_inicio:data.fecha_inicio, fecha_fin:data.fecha_fin, activo:data.activo };
    loading = false;
    await cargarEstructura();
  });

  async function cargarEstructura() {
    cargandoEst = true;
    try {
      const res = await fetch(`/api/estructura/periodo/${id}/`, { credentials:'include' });
      estructura = await res.json();
    } catch { estructura = null; }
    finally { cargandoEst = false; }
  }

  function onEstructuraConfirmada(resumen) {
    wizardAbierto = false;
    toast = `Estructura guardada: ${resumen?.facultades ?? 0} facultades, ${resumen?.carreras ?? 0} carreras.`;
    setTimeout(() => toast = '', 4000);
    cargarEstructura();
  }

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

  <!-- ESTRUCTURA ACADÉMICA HISTÓRICA -->
  <div class="form-card est-card">
    <div class="est-head">
      <div>
        <h2 class="form-title"><i class="bi bi-diagram-3"></i> Estructura académica del período</h2>
        <p class="est-sub">Facultades y carreras tal como se ofertaron en este período.</p>
      </div>
      <button class="btn-recon" onclick={() => wizardAbierto = true}>
        <i class="bi bi-arrow-repeat"></i>
        {estructura?.tiene_snapshot ? 'Reconciliar estructura' : 'Definir estructura'}
      </button>
    </div>

    {#if cargandoEst}
      <div class="est-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando estructura…</div>
    {:else if !estructura?.tiene_snapshot}
      <div class="est-empty">
        <i class="bi bi-exclamation-circle"></i>
        Este período aún no tiene una estructura definida.
        Pulsa <strong>Definir estructura</strong> para registrarla.
      </div>
    {:else}
      <div class="est-grid">
        {#each estructura.facultades as f}
          <div class="est-fac" class:no-vig={!f.vigente}>
            <div class="est-fac-top">
              <span class="est-code">{f.codigo}</span>
              <span class="est-fac-nom">{f.nombre}</span>
              {#if !f.vigente}<span class="est-tag off">No ofertada</span>{/if}
              <span class="est-ncar">{f.carreras.length}</span>
            </div>
            {#if f.carreras.length}
              <ul class="est-cars">
                {#each f.carreras as c}
                  <li class:no-vig={!c.vigente}>{c.nombre}{#if !c.vigente} <span class="est-tag off sm">no vig.</span>{/if}</li>
                {/each}
              </ul>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
{/if}

{#if wizardAbierto}
  <WizardEstructura
    periodoId={id}
    periodoNombre={form.nombre}
    onConfirmado={onEstructuraConfirmada}
    onCancelar={() => wizardAbierto = false}
  />
{/if}

{#if toast}<div class="toast-ok"><i class="bi bi-check-circle-fill"></i> {toast}</div>{/if}

<style>

.loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center; }
.check-label { display:flex;align-items:center;gap:8px;font-size:.82rem;font-weight:700;color:#444;cursor:pointer;margin-top:22px; }
.check-label input { accent-color:var(--verde);width:16px;height:16px; }

.est-card { margin-top:18px; }
.est-head { display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px; }
.est-sub { font-size:.78rem;color:var(--gris);font-weight:600;margin-top:2px; }
.btn-recon { background:var(--verde-claro);color:var(--verde);border:1.5px solid #cfe6c2;font-weight:800;
             border-radius:10px;padding:9px 16px;font-size:.82rem;display:flex;align-items:center;gap:7px;flex-shrink:0; }
.btn-recon:hover { background:#dcefd0; }
.est-loading, .est-empty { display:flex;align-items:center;gap:9px;color:var(--gris);font-weight:600;
             font-size:.85rem;padding:20px;justify-content:center;background:#fafbfa;border-radius:12px; }
.est-empty { color:#8a6d1a;background:#fff8e6; }
.est-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px; }
.est-fac { border:1px solid var(--borde);border-radius:12px;padding:10px 12px;background:#fff; }
.est-fac.no-vig { opacity:.55;background:#fafafa; }
.est-fac-top { display:flex;align-items:center;gap:8px; }
.est-code { font-size:.62rem;font-weight:800;color:var(--verde);background:var(--verde-claro);padding:2px 7px;border-radius:5px;flex-shrink:0; }
.est-fac-nom { font-size:.8rem;font-weight:800;color:var(--negro);flex:1;line-height:1.2; }
.est-ncar { font-size:.68rem;font-weight:800;color:#fff;background:var(--verde);border-radius:20px;
            min-width:20px;height:20px;display:flex;align-items:center;justify-content:center;padding:0 6px;flex-shrink:0; }
.est-tag { font-size:.6rem;font-weight:800;border-radius:20px;padding:2px 7px; }
.est-tag.off { color:#c0392b;background:#fdecec; }
.est-tag.off.sm { font-size:.55rem;padding:1px 5px; }
.est-cars { list-style:none;margin:8px 0 0;padding:8px 0 0;border-top:1px dashed #eee;display:flex;flex-direction:column;gap:4px; }
.est-cars li { font-size:.75rem;color:#444;font-weight:600;padding-left:12px;position:relative; }
.est-cars li::before { content:'';position:absolute;left:0;top:7px;width:5px;height:5px;border-radius:50%;background:var(--dorado); }
.est-cars li.no-vig { opacity:.5;text-decoration:line-through; }

.toast-ok { position:fixed;bottom:24px;right:24px;background:var(--verde);color:#fff;font-weight:700;font-size:.82rem;
            padding:11px 18px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.2);display:flex;align-items:center;gap:8px;z-index:600; }

@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
