<script>
  // Selección múltiple de Objetivos de Desarrollo Sostenible (ONU, Agenda 2030).
  // seleccionados: array bindable de números (ej: [2, 12, 15]).
  let { seleccionados = $bindable([]) } = $props();

  const ODS = [
    { n: 1,  t: 'Fin de la pobreza',                         c: '#e5243b' },
    { n: 2,  t: 'Hambre cero',                               c: '#dda63a' },
    { n: 3,  t: 'Salud y bienestar',                         c: '#4c9f38' },
    { n: 4,  t: 'Educación de calidad',                      c: '#c5192d' },
    { n: 5,  t: 'Igualdad de género',                        c: '#ff3a21' },
    { n: 6,  t: 'Agua limpia y saneamiento',                 c: '#26bde2' },
    { n: 7,  t: 'Energía asequible y no contaminante',       c: '#fcc30b' },
    { n: 8,  t: 'Trabajo decente y crecimiento económico',   c: '#a21942' },
    { n: 9,  t: 'Industria, innovación e infraestructura',   c: '#fd6925' },
    { n: 10, t: 'Reducción de las desigualdades',            c: '#dd1367' },
    { n: 11, t: 'Ciudades y comunidades sostenibles',        c: '#fd9d24' },
    { n: 12, t: 'Producción y consumo responsables',         c: '#bf8b2e' },
    { n: 13, t: 'Acción por el clima',                       c: '#3f7e44' },
    { n: 14, t: 'Vida submarina',                            c: '#0a97d9' },
    { n: 15, t: 'Vida de ecosistemas terrestres',            c: '#56c02b' },
    { n: 16, t: 'Paz, justicia e instituciones sólidas',     c: '#00689d' },
    { n: 17, t: 'Alianzas para lograr los objetivos',        c: '#19486a' },
  ];

  function toggle(n) {
    seleccionados = seleccionados.includes(n)
      ? seleccionados.filter(x => x !== n)
      : [...seleccionados, n].sort((a, b) => a - b);
  }
</script>

<div class="ods-grid">
  {#each ODS as o}
    <button
      type="button"
      class="ods-chip"
      class:sel={seleccionados.includes(o.n)}
      style="--c:{o.c}"
      onclick={() => toggle(o.n)}
      title={o.t}
    >
      <span class="ods-num">{o.n}</span>
      <span class="ods-txt">{o.t}</span>
      {#if seleccionados.includes(o.n)}<i class="bi bi-check-lg ods-check"></i>{/if}
    </button>
  {/each}
</div>
{#if seleccionados.length}
  <p class="ods-sel">Seleccionados: <strong>{seleccionados.map(n => 'ODS ' + n).join(', ')}</strong></p>
{/if}

<style>
  .ods-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:7px; }
  .ods-chip {
    display:flex; align-items:center; gap:8px; text-align:left;
    border:1.5px solid var(--borde); border-radius:10px; padding:7px 9px;
    background:#fff; font-family:inherit; cursor:pointer; position:relative; transition:all .15s;
  }
  .ods-chip:hover { border-color:var(--c); background:#fafafa; }
  .ods-num {
    width:26px; height:26px; border-radius:6px; background:var(--c); color:#fff;
    font-weight:800; font-size:.82rem; display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }
  .ods-txt { font-size:.72rem; font-weight:600; color:#444; line-height:1.2; flex:1; }
  .ods-chip.sel { border-color:var(--c); background:color-mix(in srgb, var(--c) 8%, #fff); }
  .ods-chip.sel .ods-txt { color:#222; font-weight:700; }
  .ods-check { color:var(--c); font-size:.9rem; flex-shrink:0; }
  .ods-sel { margin-top:8px; font-size:.76rem; color:var(--gris); }
  .ods-sel strong { color:var(--verde); }
</style>
