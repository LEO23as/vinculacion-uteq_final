<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';

  let capas = $state([]);
  let cargando = $state(true);
  let subiendo = $state(false);

  let form = $state({
    tipo_indicador: 'NBI',
    anio: new Date().getFullYear(),
    unidad: '%',
    fuente: '',
    archivo: null,
  });

  let preview = $state(null);
  let errores = $state([]);

  async function cargar() {
    cargando = true;
    try { capas = await fetchAPI('/api/capas-indicador/'); }
    catch (e) { toast.error('No se pudieron cargar las capas'); }
    finally { cargando = false; }
  }

  onMount(cargar);

  function onFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    form.archivo = f;
    const reader = new FileReader();
    reader.onload = () => parseCSV(reader.result);
    reader.readAsText(f, 'utf-8');
  }

  function parseCSV(txt) {
    errores = [];
    const lines = txt.split(/\r?\n/).filter(l => l.trim());
    if (!lines.length) { errores = ['Archivo vacío']; preview = null; return; }
    const header = lines[0].split(',').map(s => s.trim().toLowerCase());
    const iDpa = header.indexOf('dpa_canton');
    const iVal = header.indexOf('valor');
    if (iDpa < 0 || iVal < 0) {
      errores = ['Faltan columnas requeridas: dpa_canton, valor'];
      preview = null;
      return;
    }
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const c = lines[i].split(',').map(s => s.trim());
      const dpa = c[iDpa];
      const val = parseFloat(c[iVal]);
      if (!/^\d{4}$/.test(dpa)) { errores.push(`Fila ${i+1}: dpa_canton inválido "${dpa}"`); continue; }
      if (isNaN(val))           { errores.push(`Fila ${i+1}: valor inválido "${c[iVal]}"`);   continue; }
      rows.push({ dpa_canton: dpa, valor: val });
    }
    preview = rows;
  }

  async function subir() {
    if (!form.archivo)      { toast.error('Selecciona un archivo CSV'); return; }
    if (!preview?.length)   { toast.error('CSV sin filas válidas');     return; }
    if (!form.fuente.trim()){ toast.error('Indica la fuente');          return; }
    subiendo = true;
    try {
      const fd = new FormData();
      fd.append('tipo_indicador', form.tipo_indicador);
      fd.append('anio', form.anio);
      fd.append('unidad', form.unidad);
      fd.append('fuente', form.fuente);
      fd.append('archivo', form.archivo);
      const r = await fetch('/api/capas-indicador/upload/', { method:'POST', body: fd, credentials:'include' });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || 'Error al subir');
      toast.success(`Cargado: ${data.insertados} filas (${data.tipo_indicador} ${data.anio})`);
      form = { tipo_indicador:'NBI', anio: new Date().getFullYear(), unidad:'%', fuente:'', archivo:null };
      preview = null; errores = [];
      document.getElementById('csvinput').value = '';
      await cargar();
    } catch (e) {
      toast.error(e.message);
    } finally { subiendo = false; }
  }

  async function eliminar(c) {
    if (!confirm(`¿Eliminar la capa ${c.tipo_indicador} ${c.anio}? (${c.total} filas)`)) return;
    try {
      const r = await fetch(`/api/capas-indicador/${c.tipo_indicador}/${c.anio}/`, { method:'DELETE', credentials:'include' });
      if (!r.ok) throw new Error('No se pudo eliminar');
      toast.success('Capa eliminada');
      await cargar();
    } catch (e) { toast.error(e.message); }
  }
</script>

<svelte:head><title>Capas del mapa — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/configuracion">Configuración</a>
    <span class="sep">/</span>
    <span class="current">Capas del mapa</span>
  </nav>
</div>

<div class="cap-body">

  <!-- FORM DE CARGA -->
  <section class="cap-card">
    <header class="cap-h">
      <i class="bi bi-cloud-upload"></i>
      <div>
        <h3>Cargar nueva capa</h3>
        <p>Sube un CSV con los valores de un indicador por cantón. La geometría ya está en el sistema; solo se cargan los atributos.</p>
      </div>
    </header>

    <div class="cap-form">
      <div class="fg">
        <label>Tipo de indicador</label>
        <input type="text" bind:value={form.tipo_indicador} maxlength="30" placeholder="NBI, IDH, POBLACION..." />
      </div>
      <div class="fg">
        <label>Año</label>
        <input type="number" bind:value={form.anio} min="1990" max="2100" />
      </div>
      <div class="fg">
        <label>Unidad</label>
        <input type="text" bind:value={form.unidad} maxlength="20" placeholder="%" />
      </div>
      <div class="fg wide">
        <label>Fuente</label>
        <input type="text" bind:value={form.fuente} maxlength="160" placeholder="Ej: INEC - Censo 2022" />
      </div>
      <div class="fg wide">
        <label>Archivo CSV <span class="hint">(columnas: <code>dpa_canton</code>, <code>valor</code>)</span></label>
        <input id="csvinput" type="file" accept=".csv,text/csv" onchange={onFile} />
      </div>
    </div>

    {#if errores.length}
      <div class="alert warn">
        <b>{errores.length} advertencias:</b>
        <ul>{#each errores.slice(0,10) as e}<li>{e}</li>{/each}</ul>
        {#if errores.length > 10}<small>...y {errores.length - 10} más</small>{/if}
      </div>
    {/if}

    {#if preview}
      <div class="alert ok">
        ✓ <b>{preview.length}</b> filas válidas listas para insertar.
      </div>
    {/if}

    <div class="cap-actions">
      <button class="btn-primario" onclick={subir} disabled={subiendo || !preview?.length}>
        {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Subiendo...{:else}<i class="bi bi-check-lg"></i> Guardar capa{/if}
      </button>
    </div>
  </section>

  <!-- LISTA DE CAPAS EXISTENTES -->
  <section class="cap-card">
    <header class="cap-h">
      <i class="bi bi-database"></i>
      <div>
        <h3>Capas cargadas</h3>
        <p>Indicadores actualmente disponibles en el mapa.</p>
      </div>
    </header>

    {#if cargando}
      <div class="empty"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
    {:else if !capas.length}
      <div class="empty">No hay capas cargadas todavía.</div>
    {:else}
      <table class="cap-tabla">
        <thead>
          <tr><th>Indicador</th><th>Año</th><th>Cantones</th><th>Rango</th><th>Unidad</th><th>Fuente</th><th></th></tr>
        </thead>
        <tbody>
          {#each capas as c}
            <tr>
              <td><span class="pill">{c.tipo_indicador}</span></td>
              <td>{c.anio}</td>
              <td>{c.total}</td>
              <td>{c.min?.toFixed?.(1) ?? '—'} – {c.max?.toFixed?.(1) ?? '—'}</td>
              <td>{c.unidad}</td>
              <td class="fuente">{c.fuente}</td>
              <td><button class="btn-del" onclick={() => eliminar(c)} title="Eliminar"><i class="bi bi-trash"></i></button></td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>

</div>

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }
.breadcrumb a { color:var(--verde);text-decoration:none;font-weight:700;font-size:.82rem; }
.breadcrumb .sep { color:#bbb;margin:0 6px; }
.breadcrumb .current { color:#333;font-weight:800;font-size:.82rem; }

.cap-body { padding:20px 24px;display:flex;flex-direction:column;gap:18px; }

.cap-card { background:#fff;border-radius:16px;border:1px solid #ebebeb;
  box-shadow:0 3px 14px rgba(0,0,0,.06);padding:20px 22px; }
.cap-h { display:flex;align-items:flex-start;gap:14px;margin-bottom:16px; }
.cap-h > i { font-size:1.6rem;color:var(--verde);background:var(--verde-claro);
  width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0; }
.cap-h h3 { font-size:1rem;font-weight:800;color:#1a1a1a;margin:0 0 3px; }
.cap-h p  { font-size:.75rem;color:#888;margin:0; }

.cap-form { display:grid;grid-template-columns:repeat(4,1fr);gap:12px 14px; }
.fg { display:flex;flex-direction:column;gap:5px; }
.fg.wide { grid-column:span 2; }
.fg label { font-size:.7rem;font-weight:800;color:#666;text-transform:uppercase;letter-spacing:.05em; }
.fg .hint { text-transform:none;font-weight:600;color:#aaa;letter-spacing:0; }
.fg .hint code { background:#f4f6f3;padding:1px 5px;border-radius:4px;font-size:.68rem; }
.fg input {
  border:1.5px solid var(--borde);border-radius:10px;padding:8px 12px;
  font-size:.85rem;font-family:inherit;font-weight:600;color:#333;background:#fafafa;outline:none;
  transition:border-color .2s;
}
.fg input:focus { border-color:var(--verde);background:#fff; }
@media (max-width:900px) { .cap-form { grid-template-columns:repeat(2,1fr); } .fg.wide { grid-column:span 2; } }

.alert { margin-top:14px;border-radius:10px;padding:10px 14px;font-size:.8rem;font-weight:600; }
.alert.warn { background:#fff8e6;border:1px solid #f5d97a;color:#7a5b00; }
.alert.ok   { background:#e8f5e0;border:1px solid #c3e6b0;color:#1b5c02; }
.alert ul { margin:6px 0 0 20px;font-weight:500; }

.cap-actions { display:flex;justify-content:flex-end;margin-top:14px; }
.btn-primario {
  background:var(--verde);color:#fff;border:none;border-radius:20px;
  padding:8px 22px;font-size:.85rem;font-weight:800;cursor:pointer;
  display:inline-flex;align-items:center;gap:7px;font-family:inherit;transition:background .2s;
}
.btn-primario:hover:not(:disabled) { background:#155e04; }
.btn-primario:disabled { opacity:.5;cursor:not-allowed; }

.cap-tabla { width:100%;border-collapse:collapse;font-size:.82rem; }
.cap-tabla th { text-align:left;font-size:.68rem;font-weight:800;color:#888;text-transform:uppercase;
  letter-spacing:.05em;padding:8px 10px;border-bottom:2px solid #f0f0f0; }
.cap-tabla td { padding:10px;border-bottom:1px solid #f4f4f4;color:#333;font-weight:600; }
.cap-tabla tbody tr:hover { background:#fafafa; }
.pill { background:var(--verde-claro);color:var(--verde);font-weight:800;font-size:.72rem;
  padding:3px 10px;border-radius:20px;border:1px solid #c3e6b0; }
.fuente { color:#888;font-weight:500;font-size:.75rem; }
.btn-del { background:none;border:none;color:#c33;cursor:pointer;font-size:1rem;padding:4px 8px;border-radius:8px; }
.btn-del:hover { background:#fce8e8; }

.empty { padding:24px;text-align:center;color:#999;font-size:.85rem; }
@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
