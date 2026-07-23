<script>
  import { onMount } from 'svelte';

  let { periodoId, periodoNombre = '', onConfirmado, onCancelar } = $props();

  let loading   = $state(true);
  let saving    = $state(false);
  let error     = $state('');
  let referencia = $state(null);
  let facultades = $state([]);
  let expandidas = $state({});      // id_facultad -> bool
  let soloCambios = $state(false);

  const ESTADO_META = {
    SIN_CAMBIO:  { label: 'Sin cambio',  color: '#a8a8a7', bg: '#f2f2f2', icon: 'bi-dash-circle' },
    RENOMBRADA:  { label: 'Renombrada',  color: '#dba112', bg: '#fff8e6', icon: 'bi-pencil-square' },
    NUEVA:       { label: 'Nueva',       color: '#1b7505', bg: '#e8f5e0', icon: 'bi-plus-circle' },
    DESACTIVADA: { label: 'Desactivada', color: '#dc3545', bg: '#fdecec', icon: 'bi-x-circle' },
  };

  onMount(cargar);

  async function cargar() {
    loading = true; error = '';
    try {
      const res = await fetch(`/api/estructura/comparar/${periodoId}/`, { credentials: 'include' });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'No se pudo comparar la estructura'; return; }
      referencia = data.periodo_referencia;
      // Normalizar: cada facultad/carrera arranca con tipo_cambio = estado_sugerido
      facultades = (data.facultades || []).map(f => ({
        ...f,
        tipo_cambio: f.estado_sugerido,
        carreras: (f.carreras || []).map(c => ({ ...c, tipo_cambio: c.estado_sugerido })),
      }));
    } catch { error = 'Error de conexión'; }
    finally { loading = false; }
  }

  function toggleExpand(id) { expandidas[id] = !expandidas[id]; }

  // Al editar el nombre de una facultad, si difiere del histórico -> RENOMBRADA
  function onNombreFacultad(f) {
    if (f.estado_sugerido === 'NUEVA') return;              // una nueva no se "renombra"
    if (f.nombre_referencia && f.nombre_sugerido.trim() !== f.nombre_referencia) {
      f.tipo_cambio = 'RENOMBRADA';
    } else if (f.nombre_referencia) {
      f.tipo_cambio = 'SIN_CAMBIO';
    }
    facultades = facultades;
  }

  function onNombreCarrera(c) {
    if (c.estado_sugerido === 'NUEVA') return;
    if (c.nombre_referencia && c.nombre_sugerido.trim() !== c.nombre_referencia) {
      c.tipo_cambio = 'RENOMBRADA';
    } else if (c.nombre_referencia) {
      c.tipo_cambio = 'SIN_CAMBIO';
    }
    facultades = facultades;
  }

  function toggleVigenteFac(f) {
    f.vigente = !f.vigente;
    f.tipo_cambio = f.vigente
      ? (f.estado_sugerido === 'NUEVA' ? 'NUEVA' : 'SIN_CAMBIO')
      : 'DESACTIVADA';
    // Al desactivar la facultad, sus carreras dejan de estar vigentes
    if (!f.vigente) f.carreras.forEach(c => { c.vigente = false; c.tipo_cambio = 'DESACTIVADA'; });
    facultades = facultades;
  }

  function toggleVigenteCar(f, c) {
    c.vigente = !c.vigente;
    c.tipo_cambio = c.vigente
      ? (c.estado_sugerido === 'NUEVA' ? 'NUEVA' : 'SIN_CAMBIO')
      : 'DESACTIVADA';
    facultades = facultades;
  }

  let resumen = $derived.by(() => {
    let fac = facultades.length, car = 0, cambios = 0;
    for (const f of facultades) {
      car += f.carreras.length;
      if (f.tipo_cambio !== 'SIN_CAMBIO') cambios++;
      for (const c of f.carreras) if (c.tipo_cambio !== 'SIN_CAMBIO') cambios++;
    }
    return { fac, car, cambios };
  });

  let visibles = $derived(
    soloCambios
      ? facultades.filter(f => f.tipo_cambio !== 'SIN_CAMBIO' || f.carreras.some(c => c.tipo_cambio !== 'SIN_CAMBIO'))
      : facultades
  );

  async function confirmar() {
    // Validación: ningún nombre vacío en elementos vigentes
    for (const f of facultades) {
      if (f.vigente && !f.nombre_sugerido.trim()) {
        error = `La facultad "${f.nombre_actual || f.nombre_referencia}" no puede quedar sin nombre.`;
        return;
      }
      for (const c of f.carreras) {
        if (c.vigente && !c.nombre_sugerido.trim()) {
          error = `Una carrera de "${f.nombre_sugerido}" no puede quedar sin nombre.`;
          return;
        }
      }
    }
    saving = true; error = '';
    try {
      const payload = {
        facultades: facultades.map(f => ({
          id_facultad: f.id_facultad,
          codigo: f.codigo,
          nombre_sugerido: f.nombre_sugerido,
          nombre_corto: f.nombre_corto,
          campus: f.campus,
          vigente: f.vigente,
          tipo_cambio: f.tipo_cambio,
          carreras: f.carreras.map(c => ({
            id_carrera: c.id_carrera,
            codigo: c.codigo,
            nombre_sugerido: c.nombre_sugerido,
            horas_vinculacion: c.horas_vinculacion,
            vigente: c.vigente,
            tipo_cambio: c.tipo_cambio,
          })),
        })),
      };
      const res = await fetch(`/api/estructura/periodo/${periodoId}/confirmar/`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'No se pudo guardar la estructura'; return; }
      onConfirmado?.(data.resumen);
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<div class="wz-overlay">
  <div class="wz-modal">

    <!-- HEADER -->
    <div class="wz-head">
      <div class="wz-head-txt">
        <h3><i class="bi bi-diagram-3"></i> Confirmar estructura académica</h3>
        <p>
          Período <strong>{periodoNombre || '—'}</strong>
          {#if referencia}· comparado con <strong>{referencia.codigo}</strong>{:else}· sin período previo de referencia{/if}
        </p>
      </div>
      <button class="wz-x" onclick={() => onCancelar?.()} title="Cancelar"><i class="bi bi-x-lg"></i></button>
    </div>

    {#if loading}
      <div class="wz-loading"><i class="bi bi-arrow-repeat spin"></i> Analizando cambios…</div>
    {:else if error && !facultades.length}
      <div class="wz-error"><i class="bi bi-exclamation-triangle"></i> {error}</div>
      <div class="wz-foot"><button class="wz-btn-ghost" onclick={() => onCancelar?.()}>Cerrar</button></div>
    {:else}

      <!-- RESUMEN -->
      <div class="wz-summary">
        <div class="wz-stat"><span class="wz-stat-n">{resumen.fac}</span><span class="wz-stat-l">Facultades</span></div>
        <div class="wz-stat"><span class="wz-stat-n">{resumen.car}</span><span class="wz-stat-l">Carreras</span></div>
        <div class="wz-stat wz-stat-hi">
          <span class="wz-stat-n">{resumen.cambios}</span><span class="wz-stat-l">Cambios detectados</span>
        </div>
        <label class="wz-filtro">
          <input type="checkbox" bind:checked={soloCambios} />
          Ver solo cambios
        </label>
      </div>

      <!-- LEYENDA -->
      <div class="wz-leyenda">
        {#each Object.entries(ESTADO_META) as [k, m]}
          <span class="wz-lg" style="--c:{m.color};--bg:{m.bg}"><i class="bi {m.icon}"></i>{m.label}</span>
        {/each}
      </div>

      {#if error}<div class="wz-error inline"><i class="bi bi-exclamation-triangle"></i> {error}</div>{/if}

      <!-- LISTA -->
      <div class="wz-body">
        {#each visibles as f (f.id_facultad)}
          {@const m = ESTADO_META[f.tipo_cambio]}
          <div class="wz-fac" class:dim={!f.vigente}>
            <div class="wz-fac-row">
              <button class="wz-caret" onclick={() => toggleExpand(f.id_facultad)} title="Ver carreras">
                <i class="bi bi-chevron-{expandidas[f.id_facultad] ? 'down' : 'right'}"></i>
              </button>
              <span class="wz-code">{f.codigo}</span>
              <input
                class="wz-input"
                bind:value={f.nombre_sugerido}
                oninput={() => onNombreFacultad(f)}
                disabled={!f.vigente}
                placeholder="Nombre de la facultad"
              />
              <span class="wz-badge" style="--c:{m.color};--bg:{m.bg}"><i class="bi {m.icon}"></i>{m.label}</span>
              <span class="wz-ncar">{f.carreras.length} car.</span>
              <button
                class="wz-toggle" class:on={f.vigente}
                onclick={() => toggleVigenteFac(f)}
                title={f.vigente ? 'Se ofertó este período' : 'No se ofertó'}>
                <i class="bi bi-{f.vigente ? 'toggle-on' : 'toggle-off'}"></i>
              </button>
            </div>

            {#if f.nombre_referencia && f.nombre_referencia !== f.nombre_sugerido}
              <div class="wz-antes"><i class="bi bi-clock-history"></i> Antes: <em>{f.nombre_referencia}</em></div>
            {/if}

            {#if expandidas[f.id_facultad]}
              <div class="wz-carreras">
                {#if f.carreras.length === 0}
                  <div class="wz-empty">Sin carreras registradas</div>
                {/if}
                {#each f.carreras as c (c.id_carrera)}
                  {@const mc = ESTADO_META[c.tipo_cambio]}
                  <div class="wz-car" class:dim={!c.vigente}>
                    <i class="bi bi-arrow-return-right wz-car-ic"></i>
                    <input
                      class="wz-input sm"
                      bind:value={c.nombre_sugerido}
                      oninput={() => onNombreCarrera(c)}
                      disabled={!c.vigente || !f.vigente}
                      placeholder="Nombre de la carrera"
                    />
                    <span class="wz-badge sm" style="--c:{mc.color};--bg:{mc.bg}"><i class="bi {mc.icon}"></i>{mc.label}</span>
                    <button
                      class="wz-toggle sm" class:on={c.vigente}
                      onclick={() => toggleVigenteCar(f, c)}
                      disabled={!f.vigente}
                      title={c.vigente ? 'Vigente' : 'No vigente'}>
                      <i class="bi bi-{c.vigente ? 'toggle-on' : 'toggle-off'}"></i>
                    </button>
                  </div>
                  {#if c.nombre_referencia && c.nombre_referencia !== c.nombre_sugerido}
                    <div class="wz-antes car"><i class="bi bi-clock-history"></i> Antes: <em>{c.nombre_referencia}</em></div>
                  {/if}
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- FOOTER -->
      <div class="wz-foot">
        <span class="wz-hint"><i class="bi bi-info-circle"></i> Esta estructura queda guardada como la foto histórica del período.</span>
        <div class="wz-foot-btns">
          <button class="wz-btn-ghost" onclick={() => onCancelar?.()} disabled={saving}>Cancelar</button>
          <button class="wz-btn-save" onclick={confirmar} disabled={saving}>
            {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}<i class="bi bi-check2-circle"></i> Confirmar y guardar{/if}
          </button>
        </div>
      </div>
    {/if}

  </div>
</div>

<style>
  .wz-overlay {
    position: fixed; inset: 0; z-index: 500;
    background: rgba(13,25,16,.55); backdrop-filter: blur(2px);
    display: flex; align-items: center; justify-content: center; padding: 24px;
  }
  .wz-modal {
    background: #fff; border-radius: 18px; width: min(920px, 100%);
    max-height: 90vh; display: flex; flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,.3); overflow: hidden;
  }

  .wz-head {
    display: flex; align-items: flex-start; justify-content: space-between;
    background: var(--verde); color: #fff; padding: 16px 20px;
  }
  .wz-head h3 { font-size: 1.05rem; font-weight: 800; display: flex; align-items: center; gap: 9px; }
  .wz-head p  { font-size: .8rem; opacity: .9; margin-top: 3px; font-weight: 600; }
  .wz-x { background: rgba(255,255,255,.15); border: none; color: #fff; width: 32px; height: 32px;
          border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: .9rem; }
  .wz-x:hover { background: rgba(255,255,255,.28); }

  .wz-loading, .wz-error { padding: 40px; text-align: center; color: #777; font-weight: 600; font-size: .9rem; }
  .wz-error { color: #c0392b; }
  .wz-error.inline { padding: 10px 20px; text-align: left; font-size: .82rem; background: #fdecec; }

  .wz-summary {
    display: flex; align-items: center; gap: 20px; padding: 14px 20px;
    border-bottom: 1px solid var(--borde); background: #fafbfa;
  }
  .wz-stat { display: flex; flex-direction: column; }
  .wz-stat-n { font-size: 1.35rem; font-weight: 900; color: var(--negro); line-height: 1; }
  .wz-stat-l { font-size: .68rem; color: var(--gris); font-weight: 700; text-transform: uppercase; letter-spacing: .04em; margin-top: 3px; }
  .wz-stat-hi .wz-stat-n { color: var(--dorado); }
  .wz-filtro { margin-left: auto; display: flex; align-items: center; gap: 7px; font-size: .8rem; font-weight: 700; color: #555; cursor: pointer; }
  .wz-filtro input { accent-color: var(--verde); width: 15px; height: 15px; }

  .wz-leyenda { display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 20px; border-bottom: 1px solid var(--borde); }
  .wz-lg { display: inline-flex; align-items: center; gap: 5px; font-size: .7rem; font-weight: 700;
           color: var(--c); background: var(--bg); border-radius: 20px; padding: 3px 10px; }

  .wz-body { overflow-y: auto; padding: 12px 20px; flex: 1; }

  .wz-fac { border: 1px solid var(--borde); border-radius: 12px; padding: 10px 12px; margin-bottom: 8px; transition: opacity .15s; }
  .wz-fac.dim { opacity: .5; background: #fafafa; }
  .wz-fac-row { display: flex; align-items: center; gap: 9px; }
  .wz-caret { background: none; border: none; color: var(--verde); font-size: .8rem; width: 22px; height: 22px;
              display: flex; align-items: center; justify-content: center; border-radius: 6px; }
  .wz-caret:hover { background: var(--verde-claro); }
  .wz-code { font-size: .68rem; font-weight: 800; color: var(--verde); background: var(--verde-claro);
             padding: 3px 8px; border-radius: 6px; flex-shrink: 0; min-width: 54px; text-align: center; }
  .wz-input {
    flex: 1; border: 1.5px solid transparent; border-radius: 8px; padding: 7px 10px;
    font-size: .86rem; font-family: inherit; font-weight: 700; color: #222; background: #f6f7f6; min-width: 0;
  }
  .wz-input:hover:not(:disabled) { background: #eef2ec; }
  .wz-input:focus { outline: none; border-color: var(--verde); background: #fff; }
  .wz-input:disabled { color: #999; background: transparent; text-decoration: line-through; }
  .wz-input.sm { font-size: .8rem; font-weight: 600; padding: 5px 9px; }
  .wz-badge { display: inline-flex; align-items: center; gap: 4px; font-size: .68rem; font-weight: 800;
              color: var(--c); background: var(--bg); border-radius: 20px; padding: 3px 9px; flex-shrink: 0; white-space: nowrap; }
  .wz-badge.sm { font-size: .62rem; padding: 2px 7px; }
  .wz-ncar { font-size: .7rem; color: var(--gris); font-weight: 700; flex-shrink: 0; }
  .wz-toggle { background: none; border: none; font-size: 1.25rem; color: var(--gris); flex-shrink: 0; line-height: 1; }
  .wz-toggle.on { color: var(--verde); }
  .wz-toggle.sm { font-size: 1.05rem; }
  .wz-toggle:disabled { opacity: .4; }

  .wz-antes { font-size: .72rem; color: var(--dorado); font-weight: 700; padding: 5px 0 2px 33px; display: flex; align-items: center; gap: 5px; }
  .wz-antes em { color: #a07500; font-style: italic; }
  .wz-antes.car { padding-left: 60px; font-size: .68rem; }

  .wz-carreras { margin: 8px 0 2px 24px; padding-left: 12px; border-left: 2px dashed #dfe6da; display: flex; flex-direction: column; gap: 6px; }
  .wz-car { display: flex; align-items: center; gap: 8px; }
  .wz-car.dim { opacity: .5; }
  .wz-car-ic { color: #bcc7b6; font-size: .8rem; flex-shrink: 0; }
  .wz-empty { font-size: .74rem; color: var(--gris); font-style: italic; padding: 4px 0; }

  .wz-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px;
             padding: 14px 20px; border-top: 1px solid var(--borde); background: #fafbfa; }
  .wz-hint { font-size: .74rem; color: var(--gris); font-weight: 600; display: flex; align-items: center; gap: 6px; }
  .wz-foot-btns { display: flex; gap: 10px; margin-left: auto; }
  .wz-btn-ghost { background: #fff; border: 1.5px solid var(--borde); color: #555; font-weight: 700;
                  border-radius: 10px; padding: 9px 18px; font-size: .84rem; }
  .wz-btn-ghost:hover { border-color: var(--gris); }
  .wz-btn-save { background: var(--verde); border: none; color: #fff; font-weight: 800;
                 border-radius: 10px; padding: 9px 20px; font-size: .84rem; display: flex; align-items: center; gap: 7px; }
  .wz-btn-save:hover { background: #156004; }
  .wz-btn-save:disabled, .wz-btn-ghost:disabled { opacity: .6; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin .7s linear infinite; }
</style>
