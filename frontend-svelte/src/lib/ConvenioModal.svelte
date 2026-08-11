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
            <button type="button" class:activo={!nuevaEntidad} onclick={() => nuevaEntidad = false}>Entidad existente</button>
            <button type="button" class:activo={nuevaEntidad} onclick={() => nuevaEntidad = true}>+ Nueva entidad</button>
          </div>

          {#if !nuevaEntidad}
            <div class="grid-row">
              <div class="field col-12">
                <label>Entidad Cooperante *</label>
                <select bind:value={form.id_entidad}>
                  <option value="">— Seleccionar entidad —</option>
                  {#each entidades as e}<option value={e.id_entidad}>{e.nombre}</option>{/each}
                </select>
              </div>
            </div>
          {:else}
            <div class="grid-row">
              <div class="field col-7"><label>Nombre completo *</label><input bind:value={entidadForm.nombre} placeholder="Nombre de la entidad..." /></div>
              <div class="field col-5">
                <label>Tipo de entidad *</label>
                <select bind:value={entidadForm.id_tipo}>
                  <option value="">— Seleccionar —</option>
                  {#each tipos as t}<option value={t.id_tipo}>{t.nombre}</option>{/each}
                </select>
              </div>
              <div class="field col-4"><label>RUC</label><input bind:value={entidadForm.ruc} maxlength="15" /></div>
              <div class="field col-4"><label>Teléfono</label><input bind:value={entidadForm.telefono} /></div>
              <div class="field col-4"><label>Correo</label><input type="email" bind:value={entidadForm.correo} /></div>
            </div>
          {/if}
        </div>

        <div class="sec">
          <div class="grid-row">
            <div class="field col-4">
              <label>Período Académico</label>
              <select bind:value={form.id_periodo}>
                <option value="">— Seleccionar —</option>
                {#each periodos as p}<option value={p.id_periodo}>{p.nombre}</option>{/each}
              </select>
            </div>
            <div class="field col-4"><label>N° Memorando</label><input bind:value={form.numero_memorando} placeholder="VCL-2025-001" /></div>
            <div class="field col-4">
              <label>Estado *</label>
              <select bind:value={form.estado}>{#each ESTADOS as e}<option value={e}>{e}</option>{/each}</select>
            </div>
          </div>
        </div>

        <div class="sec">
          <div class="grid-row">
            <div class="field col-3"><label>Fecha de firma</label><input type="date" bind:value={form.fecha_firma} /></div>
            <div class="field col-3"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
            <div class="field col-3"><label>Fecha de fin</label><input type="date" bind:value={form.fecha_fin} /></div>
            <div class="field col-3"><label>Duración (años)</label><input type="number" min="1" max="10" bind:value={form.duracion_anios} /></div>
          </div>
        </div>

        <div class="sec">
          <div class="grid-row">
            <div class="field col-3"><label>Estudiantes asignados</label><input type="number" min="0" bind:value={form.estudiantes_asignados} /></div>
            <div class="field col-9"><label>Observaciones</label><textarea rows="2" bind:value={form.observaciones}></textarea></div>
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
  .modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index:9999; padding:20px; }
  .modal-card {
    background:#fff; border-radius:16px; max-width:720px; width:100%; max-height:88vh;
    box-shadow:0 8px 32px rgba(0,0,0,.18);
    display:flex; flex-direction:column; overflow:hidden;
  }
  .modal-hdr {
    display:flex; align-items:center; justify-content:space-between; padding:18px 22px;
    background:var(--verde); color:#fff; border-radius:16px 16px 0 0; flex-shrink:0;
  }
  .modal-hdr h3 { font-size:1rem; font-weight:900; display:flex; align-items:center; gap:8px; color:#fff; }
  .modal-hdr h3 i { color:#fff; }
  .modal-close { background:none; border:none; color:#fff; font-size:1rem; cursor:pointer; padding:6px; border-radius:8px; opacity:.85; }
  .modal-close:hover { background:rgba(255,255,255,.18); opacity:1; }
  .modal-body { padding:18px 22px; overflow-y:auto; min-height:0; }
  .modal-actions { display:flex; justify-content:flex-end; gap:10px; padding:16px 22px; border-top:1px solid var(--borde); flex-shrink:0; }

  .entidad-toggle { display:flex; gap:8px; margin-bottom:14px; }
  .entidad-toggle button {
    flex:1; padding:9px 12px; border:1.5px solid var(--borde); border-radius:9px;
    background:#fff; font-family:inherit; font-size:.82rem; font-weight:700; color:#666; cursor:pointer;
    transition:all .15s;
  }
  .entidad-toggle button:hover { border-color:var(--verde); }
  .entidad-toggle button.activo { border-color:var(--verde); background:var(--verde-claro); color:var(--verde); }

  .btn-registrar {
    background:var(--verde); color:#fff; border:none; border-radius:9px;
    padding:10px 26px; font-size:.85rem; font-weight:800; cursor:pointer;
    display:flex; align-items:center; gap:8px; transition:background .2s;
  }
  .btn-registrar:hover:not(:disabled) { background:var(--verde2); }
  .btn-registrar:disabled { opacity:.65; cursor:not-allowed; }

  .alert-error { margin:0 22px; margin-top:14px; }

  @keyframes spin { to { transform:rotate(360deg); } }
  .spin { display:inline-block; animation:spin .7s linear infinite; }
</style>
