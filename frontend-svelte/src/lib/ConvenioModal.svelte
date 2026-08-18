<script>
  import { toast } from '$lib/toast';

  let {
    open = $bindable(false),
    proyectoId,
    onCreated = () => {},
  } = $props();

  let entidades = $state([]);
  let tipos = $state([]);
  let periodos = $state([]);
  let cargado = $state(false);
  let saving = $state(false);
  let error = $state('');

  let nuevaEntidad = $state(false);

  let form = $state({
    id_entidad:'', id_periodo:'', numero_memorando:'',
    estado:'VIGENTE', fecha_firma:'', fecha_inicio:'', fecha_fin:'',
    duracion_anios:2, estudiantes_asignados:'', observaciones:'',
  });

  let entidadForm = $state({ nombre:'', id_tipo:'', ruc:'', telefono:'', correo:'' });

  const ESTADOS = ['VIGENTE','VENCIDO','RENOVADO','CANCELADO'];

  $effect(() => {
    if (open && !cargado) cargar();
  });

  async function cargar() {
    try {
      const [entRes, tiposRes, perRes] = await Promise.all([
        fetch('/api/entidades/', { credentials:'include' }).then(r => r.json()),
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
        fetch('/api/periodos/', { credentials:'include' }).then(r => r.json()),
      ]);
      entidades = entRes || [];
      tipos = tiposRes.tipos || [];
      periodos = perRes || [];
      cargado = true;
    } catch { toast.error('No se pudieron cargar los datos del formulario'); }
  }

  function cerrar() {
    open = false;
    error = '';
    nuevaEntidad = false;
    form = { id_entidad:'', id_periodo:'', numero_memorando:'', estado:'VIGENTE',
      fecha_firma:'', fecha_inicio:'', fecha_fin:'', duracion_anios:2,
      estudiantes_asignados:'', observaciones:'' };
    entidadForm = { nombre:'', id_tipo:'', ruc:'', telefono:'', correo:'' };
  }

  async function guardar() {
    error = '';
    if (nuevaEntidad) {
      if (!entidadForm.nombre || !entidadForm.id_tipo) {
        error = 'Nombre y tipo de la entidad son obligatorios.'; return;
      }
    } else if (!form.id_entidad) {
      error = 'Selecciona una entidad cooperante.'; return;
    }
    saving = true;
    try {
      let idEntidad = form.id_entidad;
      if (nuevaEntidad) {
        const resEnt = await fetch('/api/entidades/create/', {
          method:'POST', credentials:'include',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify(entidadForm),
        });
        const dataEnt = await resEnt.json();
        if (!resEnt.ok) { error = dataEnt.error || 'Error al crear la entidad'; return; }
        idEntidad = dataEnt.id_entidad;
      }
      const res = await fetch('/api/convenios/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ ...form, id_proyecto: proyectoId, id_entidad: idEntidad }),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear el convenio'; return; }
      toast.success('Convenio registrado');
      onCreated(data);
      cerrar();
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

{#if open}
  <div class="modal-overlay" onclick={cerrar}>
    <div class="modal-card" onclick={(e) => e.stopPropagation()}>
      <div class="modal-hdr">
        <h3><i class="bi bi-people"></i> Registrar convenio</h3>
        <button class="modal-close" onclick={cerrar} aria-label="Cerrar"><i class="bi bi-x-lg"></i></button>
      </div>

      {#if error}<div class="alert-error">{error}</div>{/if}

      <div class="modal-body">
        <div class="sec">
          <div class="entidad-toggle">
            <button type="button" class:activo={!nuevaEntidad} onclick={() => nuevaEntidad = false}>
              <i class="bi bi-building"></i> Entidad existente
            </button>
            <button type="button" class:activo={nuevaEntidad} onclick={() => nuevaEntidad = true}>
              <i class="bi bi-plus-circle"></i> + Nueva entidad
            </button>
          </div>

          {#if !nuevaEntidad}
            <div class="field full-width">
              <label>Entidad Cooperante *</label>
              <select bind:value={form.id_entidad}>
                <option value="">— Seleccionar entidad cooperante —</option>
                {#each entidades as e}<option value={e.id_entidad}>{e.nombre} {e.ruc ? `(${e.ruc})` : ''}</option>{/each}
              </select>
            </div>
          {:else}
            <div class="grid-3 mb-12">
              <div class="field col-span-2">
                <label>Nombre completo de la Entidad *</label>
                <input bind:value={entidadForm.nombre} placeholder="Ej. Gobierno Autónomo Descentralizado..." />
              </div>
              <div class="field">
                <label>Tipo de entidad *</label>
                <select bind:value={entidadForm.id_tipo}>
                  <option value="">— Seleccionar —</option>
                  {#each tipos as t}<option value={t.id_tipo}>{t.nombre}</option>{/each}
                </select>
              </div>
            </div>
            <div class="grid-3">
              <div class="field"><label>RUC</label><input bind:value={entidadForm.ruc} placeholder="Ej. 1291823912001" maxlength="15" /></div>
              <div class="field"><label>Teléfono</label><input bind:value={entidadForm.telefono} placeholder="Ej. 0991234567" /></div>
              <div class="field"><label>Correo Electrónico</label><input type="email" bind:value={entidadForm.correo} placeholder="contacto@entidad.gob.ec" /></div>
            </div>
          {/if}
        </div>

        <div class="sec">
          <div class="grid-3">
            <div class="field">
              <label>Período Académico</label>
              <select bind:value={form.id_periodo}>
                <option value="">— Seleccionar período —</option>
                {#each periodos as p}<option value={p.id_periodo}>{p.nombre || p.codigo}</option>{/each}
              </select>
            </div>
            <div class="field">
              <label>N° Memorando / Código</label>
              <input bind:value={form.numero_memorando} placeholder="Ej. VCL-2025-001" />
            </div>
            <div class="field">
              <label>Estado del Convenio *</label>
              <select bind:value={form.estado}>
                {#each ESTADOS as e}<option value={e}>{e}</option>{/each}
              </select>
            </div>
          </div>
        </div>

        <div class="sec">
          <div class="grid-4">
            <div class="field"><label>Fecha de firma</label><input type="date" bind:value={form.fecha_firma} /></div>
            <div class="field"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
            <div class="field"><label>Fecha de fin</label><input type="date" bind:value={form.fecha_fin} /></div>
            <div class="field"><label>Duración (años)</label><input type="number" min="1" max="10" bind:value={form.duracion_anios} /></div>
          </div>
        </div>

        <div class="sec no-border">
          <div class="grid-obs">
            <div class="field">
              <label>Estudiantes asignados</label>
              <input type="number" min="0" bind:value={form.estudiantes_asignados} placeholder="0" />
            </div>
            <div class="field">
              <label>Observaciones del convenio</label>
              <textarea rows="3" bind:value={form.observaciones} placeholder="Detalles u observaciones adicionales del convenio..."></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn-cancel" onclick={cerrar}>Cancelar</button>
        <button class="btn-registrar" onclick={guardar} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}<i class="bi bi-check-lg"></i> Registrar convenio{/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(2px);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999; padding: 20px;
  }
  .modal-card {
    background: #fff; border-radius: 16px; max-width: 860px; width: 100%; max-height: 90vh;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.22);
    display: flex; flex-direction: column; overflow: hidden;
  }
  .modal-hdr {
    display: flex; align-items: center; justify-content: space-between; padding: 16px 24px;
    background: var(--verde, #1b5e20); color: #fff; border-radius: 16px 16px 0 0; flex-shrink: 0;
  }
  .modal-hdr h3 { font-size: 1.05rem; font-weight: 800; display: flex; align-items: center; gap: 10px; color: #fff; margin: 0; }
  .modal-close { background: none; border: none; color: #fff; font-size: 1.1rem; cursor: pointer; padding: 6px 10px; border-radius: 8px; opacity: 0.85; transition: all 0.2s; }
  .modal-close:hover { background: rgba(255, 255, 255, 0.2); opacity: 1; }
  
  .modal-body { padding: 22px 26px; overflow-y: auto; min-height: 0; display: flex; flex-direction: column; gap: 18px; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 26px; background: #fafafa; border-top: 1px solid var(--borde, #e0e0e0); flex-shrink: 0; }

  .sec { border-bottom: 1px solid #f0f0f0; padding-bottom: 16px; }
  .sec.no-border { border-bottom: none; padding-bottom: 0; }

  .entidad-toggle {
    display: flex; gap: 6px; background: #f0f4f1; padding: 4px; border-radius: 10px; margin-bottom: 16px;
  }
  .entidad-toggle button {
    flex: 1; padding: 9px 14px; border: none; border-radius: 7px;
    background: transparent; font-family: inherit; font-size: 0.84rem; font-weight: 700; color: #555; cursor: pointer;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: all 0.2s ease;
  }
  .entidad-toggle button:hover { color: var(--verde, #1b5e20); }
  .entidad-toggle button.activo { background: #fff; color: var(--verde, #1b5e20); box-shadow: 0 2px 6px rgba(0,0,0,0.08); font-weight: 800; }

  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 16px; width: 100%; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px 16px; width: 100%; }
  .grid-obs { display: grid; grid-template-columns: 1fr 3fr; gap: 14px 16px; width: 100%; align-items: flex-start; }
  .mb-12 { margin-bottom: 12px; }
  .col-span-2 { grid-column: span 2; }
  .full-width { width: 100%; }

  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 0.73rem; font-weight: 800; color: #444; text-transform: uppercase; letter-spacing: 0.04em; }
  .field input:not([type="file"]), .field select {
    height: 42px; border: 1.5px solid var(--borde, #ccc); border-radius: 9px;
    padding: 0 14px; font-size: 0.86rem; font-family: inherit; outline: none; background: #fff;
    width: 100%; box-sizing: border-box; transition: border-color 0.2s, box-shadow 0.2s;
  }
  .field textarea {
    border: 1.5px solid var(--borde, #ccc); border-radius: 9px;
    padding: 10px 14px; font-size: 0.86rem; font-family: inherit; outline: none; background: #fff;
    width: 100%; box-sizing: border-box; transition: border-color 0.2s, box-shadow 0.2s;
    resize: vertical; min-height: 80px;
  }
  .field input:focus, .field select:focus, .field textarea:focus {
    border-color: var(--verde, #1b5e20);
    box-shadow: 0 0 0 3px rgba(27, 94, 32, 0.12);
  }

  .btn-cancel {
    background: #fff; border: 1.5px solid var(--borde, #ccc); border-radius: 9px;
    padding: 10px 22px; font-size: 0.85rem; font-weight: 700; color: #555; cursor: pointer;
    transition: all 0.2s;
  }
  .btn-cancel:hover { background: #f5f5f5; color: #333; }
  .btn-registrar {
    background: var(--verde, #1b5e20); color: #fff; border: none; border-radius: 9px;
    padding: 10px 26px; font-size: 0.85rem; font-weight: 800; cursor: pointer;
    display: flex; align-items: center; gap: 8px; transition: background 0.2s;
  }
  .btn-registrar:hover:not(:disabled) { background: #134217; }
  .btn-registrar:disabled { opacity: 0.65; cursor: not-allowed; }

  .alert-error { margin: 0 26px; margin-top: 16px; background: #fff0f0; border: 1px solid #ffc9c9; color: #c0392b; border-radius: 9px; padding: 10px 14px; font-size: 0.83rem; font-weight: 700; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
