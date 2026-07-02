<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';

    const id = $derived($page.params.id);
  let periodos = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');

  let form = $state({
    numero_memorando:'', estado:'VIGENTE', fecha_firma:'', fecha_inicio:'', fecha_fin:'',
    duracion_anios:2, estudiantes_asignados:'', observaciones:'', id_periodo:'',
  });

  const ESTADOS = ['VIGENTE','VENCIDO','RENOVADO','CANCELADO'];

  onMount(async () => {
    try {
      const [pers, data] = await Promise.all([
        fetchAPI('/api/periodos/'),
        fetch(`/api/convenios/${id}/`, { credentials:'include' }).then(r => r.json()),
      ]);
      periodos = pers;
      form = {
        numero_memorando: data.numero_memorando || '',
        estado: data.estado,
        fecha_firma: data.fecha_firma || '',
        fecha_inicio: data.fecha_inicio || '',
        fecha_fin: data.fecha_fin || '',
        duracion_anios: data.duracion_anios || 2,
        estudiantes_asignados: data.estudiantes_asignados || '',
        observaciones: data.observaciones || '',
        id_periodo: String(data.id_periodo || ''),
      };
    } finally { loading = false; }
  });

  async function guardar() {
    error = ''; saving = true;
    try {
      const res = await fetch(`/api/convenios/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/convenios/' + id);
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Convenio — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <a href="/convenios">Convenios</a><span class="sep">/</span>
    <a href="/convenios/{id}">Detalle</a><span class="sep">/</span>
    <span class="current">Editar</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="lw"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title"><i class="bi bi-file-earmark-text"></i> Editar Convenio</h2>
    {#if error}<div class="alert-error">{error}</div>{/if}

    <div class="sec">
      <h4 class="sec-hdr">Datos del convenio</h4>
      <div class="grid-row">
        <div class="field col-4"><label>N° Memorando</label><input bind:value={form.numero_memorando} /></div>
        <div class="field col-4">
          <label>Estado</label>
          <select bind:value={form.estado}>
            {#each ESTADOS as e}
              <option value={e}>{e}</option>
            {/each}
          </select>
        </div>
        <div class="field col-4">
          <label>Período</label>
          <select bind:value={form.id_periodo}>
            <option value="">— Sin período —</option>
            {#each periodos as p}
              <option value={String(p.id_periodo)}>{p.nombre}</option>
            {/each}
          </select>
        </div>
        <div class="field col-3"><label>Fecha firma</label><input type="date" bind:value={form.fecha_firma} /></div>
        <div class="field col-3"><label>Fecha inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
        <div class="field col-3"><label>Fecha fin</label><input type="date" bind:value={form.fecha_fin} /></div>
        <div class="field col-3"><label>Duración (años)</label><input type="number" min="1" max="10" bind:value={form.duracion_anios} /></div>
        <div class="field col-3"><label>Estudiantes asignados</label><input type="number" min="0" bind:value={form.estudiantes_asignados} /></div>
        <div class="field col-9"><label>Observaciones</label><textarea rows="2" bind:value={form.observaciones}></textarea></div>
      </div>
    </div>

    <div class="form-actions">
      <a href="/convenios/{id}" class="btn-cancel">Cancelar</a>
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
