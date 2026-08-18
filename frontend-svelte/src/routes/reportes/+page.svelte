<script>
  import { onMount } from 'svelte';

  let stats = $state(null);
  let periodos = $state([]);
  let periodoFiltro = $state('');
  let loading = $state(true);
  let ChartModule = $state(null);

  const ESTADO_COLORES = {
    EN_EJECUCION: '#1b7505',
    PROPUESTO: '#dba112',
    APROBADO: '#0d6efd',
    EN_CIERRE: '#fd7e14',
    DETENIDO: '#dc3545',
    FINALIZADO: '#8e8e8e',
    RECHAZADO: '#6c757d',
  };
  const ESTADO_LABEL = {
    EN_EJECUCION: 'En ejecución',
    PROPUESTO: 'Propuesto',
    APROBADO: 'Aprobado',
    EN_CIERRE: 'En cierre',
    DETENIDO: 'Detenido',
    FINALIZADO: 'Finalizado',
    RECHAZADO: 'Rechazado',
  };
  const CONV_COLORES = {
    VIGENTE: '#1b7505',
    VENCIDO: '#e65100',
    RENOVADO: '#1565c0',
    CANCELADO: '#8e8e8e',
  };
  const PALETTE = [
    '#1b5e20', '#2e7d32', '#388e3c', '#4caf50', '#81c784',
    '#dba112', '#0d6efd', '#fd7e14', '#9c27b0', '#00bcd4', '#ff5722'
  ];

  const commonTooltip = {
    backgroundColor: 'rgba(27, 40, 30, 0.92)',
    padding: 10,
    cornerRadius: 8,
    titleFont: { weight: '800', size: 12 },
    bodyFont: { weight: '600', size: 12 },
  };

  onMount(async () => {
    try {
      const { Chart, registerables } = await import('chart.js');
      Chart.register(...registerables);
      Chart.defaults.font.family = "'Nunito', sans-serif";
      Chart.defaults.font.weight = '600';
      Chart.defaults.color = '#555';
      ChartModule = Chart;
    } catch (e) {
      console.error('Error cargando Chart.js', e);
    }

    try {
      const r = await fetch('/api/periodos/', { credentials: 'include' });
      periodos = r.ok ? await r.json() : [];
    } catch {}

    cargarEstadisticas();
  });

  async function cargarEstadisticas() {
    loading = true;
    try {
      const url = periodoFiltro ? `/api/reportes/stats/?periodo=${periodoFiltro}` : '/api/reportes/stats/';
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) {
        stats = null;
        loading = false;
        return;
      }
      stats = await res.json();
    } catch {
      stats = null;
      loading = false;
      return;
    }
    loading = false;
  }

  function chartAction(node, config) {
    if (!ChartModule || !config) return;
    let chart = new ChartModule(node, config);
    return {
      update(newConfig) {
        if (chart && newConfig) {
          chart.data = newConfig.data;
          chart.options = newConfig.options;
          chart.update();
        }
      },
      destroy() {
        if (chart) chart.destroy();
      }
    };
  }

  function imprimirReporte() {
    window.print();
  }
</script>

<svelte:head>
  <title>Reportes y Estadísticas — SGV UTEQ</title>
</svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Reportes y Estadísticas</span>
  </nav>

  <div class="rep-actions">
    <div class="filter-group">
      <i class="bi bi-funnel"></i>
      <select bind:value={periodoFiltro} onchange={cargarEstadisticas} class="rep-select">
        <option value="">Todos los períodos</option>
        {#each periodos as p}
          <option value={p.id_periodo}>{p.nombre}</option>
        {/each}
      </select>
    </div>
    <button class="btn-print" onclick={imprimirReporte} title="Imprimir o guardar como PDF">
      <i class="bi bi-printer"></i> Imprimir Reporte
    </button>
  </div>
</div>

{#if loading || !ChartModule}
  <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Generando análisis estadístico...</div>
{:else if stats}
  <div class="rep-wrap">

    <!-- KPIs PRINCIPALES -->
    <div class="kpis-grid">
      <div class="kpi-card verde">
        <div class="kpi-icon"><i class="bi bi-folder2-open"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">{stats.kpis.total_proyectos}</span>
          <span class="kpi-label">Total Proyectos</span>
          <span class="kpi-sub">{stats.kpis.en_ejecucion} en ejecución</span>
        </div>
      </div>

      <div class="kpi-card dorado">
        <div class="kpi-icon"><i class="bi bi-building"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">{stats.kpis.total_entidades}</span>
          <span class="kpi-label">Entidades Cooperantes</span>
          <span class="kpi-sub">Activas</span>
        </div>
      </div>

      <div class="kpi-card azul">
        <div class="kpi-icon"><i class="bi bi-file-earmark-text"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">{stats.kpis.total_convenios}</span>
          <span class="kpi-label">Convenios</span>
          <span class="kpi-sub">Registrados</span>
        </div>
      </div>

      <div class="kpi-card esmeralda">
        <div class="kpi-icon"><i class="bi bi-cash-stack"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">${(stats.kpis.presupuesto_total || 0).toLocaleString('es-EC', { minimumFractionDigits: 2 })}</span>
          <span class="kpi-label">Presupuesto Acumulado</span>
          <span class="kpi-sub">Inversión planificada</span>
        </div>
      </div>

      <div class="kpi-card verde">
        <div class="kpi-icon"><i class="bi bi-geo-alt-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">{stats.kpis.con_geo}</span>
          <span class="kpi-label">Georreferenciados</span>
          <span class="kpi-sub">{stats.kpis.cantones_cobertura || 0} cantones con cobertura</span>
        </div>
      </div>

      <div class="kpi-card naranja">
        <div class="kpi-icon"><i class="bi bi-play-circle-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-num">{stats.kpis.pct_ejecucion}%</span>
          <span class="kpi-label">Tasa de Ejecución</span>
          <span class="kpi-sub">{stats.kpis.en_ejecucion} proyectos activos</span>
        </div>
      </div>
    </div>

    <!-- FILA 1: ESTADOS + FACULTADES -->
    <div class="charts-row">
      <div class="chart-card sm">
        <h4 class="chart-title"><i class="bi bi-pie-chart-fill text-verde"></i> Proyectos por estado</h4>
        <div class="chart-wrap h200">
          <canvas use:chartAction={{
            type: 'doughnut',
            data: {
              labels: Object.keys(stats.estados || {}).map(k => ESTADO_LABEL[k] || k),
              datasets: [{
                data: Object.keys(stats.estados || {}).map(k => stats.estados[k]),
                backgroundColor: Object.keys(stats.estados || {}).map(k => ESTADO_COLORES[k] || '#888'),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              cutout: '72%',
              plugins: { legend: { display: false }, tooltip: commonTooltip }
            }
          }}></canvas>
        </div>
        <div class="estado-bars">
          {#each Object.entries(stats.estados || {}) as [k, v]}
            <div class="ebar">
              <span class="ebar-label">{ESTADO_LABEL[k] || k}</span>
              <div class="ebar-track">
                <div class="ebar-fill" style="width:{(v/(stats.kpis.total_proyectos||1)*100).toFixed(0)}%;background:{ESTADO_COLORES[k]}"></div>
              </div>
              <span class="ebar-val">{v} <small>({(v/(stats.kpis.total_proyectos||1)*100).toFixed(0)}%)</small></span>
            </div>
          {/each}
        </div>
      </div>

      <div class="chart-card lg">
        <h4 class="chart-title"><i class="bi bi-bar-chart-line-fill text-verde"></i> Proyectos por facultad UTEQ</h4>
        <div class="chart-wrap h300">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_facultad?.labels || [],
              datasets: [{
                label: 'Proyectos',
                data: stats.por_facultad?.values || [],
                backgroundColor: PALETTE,
                borderRadius: 6,
                barThickness: 18,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y',
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
              }
            }
          }}></canvas>
        </div>
      </div>
    </div>

    <!-- FILA 2: GEOGRAFÍA (PROVINCIAS + CANTONES) -->
    <div class="charts-row">
      <div class="chart-card">
        <h4 class="chart-title"><i class="bi bi-map-fill text-verde"></i> Cobertura por provincia</h4>
        <div class="chart-wrap h260">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_provincia?.labels || [],
              datasets: [{
                label: 'Proyectos',
                data: stats.por_provincia?.values || [],
                backgroundColor: '#1b5e20',
                borderRadius: 6,
                barThickness: 18,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y',
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
              }
            }
          }}></canvas>
        </div>
      </div>

      <div class="chart-card">
        <h4 class="chart-title"><i class="bi bi-geo-fill text-dorado"></i> Cantones impactados</h4>
        <div class="chart-wrap h260">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_canton?.labels || [],
              datasets: [{
                label: 'Proyectos',
                data: stats.por_canton?.values || [],
                backgroundColor: '#dba112',
                borderRadius: 6,
                barThickness: 18,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y',
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
              }
            }
          }}></canvas>
        </div>
      </div>
    </div>

    <!-- FILA 3: ODS Y CARRERAS -->
    <div class="charts-row">
      <div class="chart-card">
        <h4 class="chart-title"><i class="bi bi-globe-americas text-azul"></i> Alineación con Objetivos ODS</h4>
        <div class="chart-wrap h260">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_ods?.labels || [],
              datasets: [{
                label: 'Proyectos alineados',
                data: stats.por_ods?.values || [],
                backgroundColor: '#0d6efd',
                borderRadius: 6,
                barThickness: 18,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y',
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
              }
            }
          }}></canvas>
        </div>
      </div>

      <div class="chart-card">
        <h4 class="chart-title"><i class="bi bi-mortarboard-fill text-verde"></i> Proyectos por carrera académica</h4>
        <div class="chart-wrap h260">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_carrera?.labels || [],
              datasets: [{
                label: 'Proyectos',
                data: stats.por_carrera?.values || [],
                backgroundColor: '#20c997',
                borderRadius: 6,
                barThickness: 18,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y',
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
              }
            }
          }}></canvas>
        </div>
      </div>
    </div>

    <!-- FILA 4: CONVENIOS + ENTIDADES + PERÍODOS -->
    <div class="charts-row">
      <div class="chart-card sm">
        <h4 class="chart-title"><i class="bi bi-file-earmark-check-fill text-verde"></i> Convenios por estado</h4>
        <div class="chart-wrap h180">
          <canvas use:chartAction={{
            type: 'doughnut',
            data: {
              labels: Object.keys(stats.convenios_estados || {}),
              datasets: [{
                data: Object.keys(stats.convenios_estados || {}).map(k => stats.convenios_estados[k]),
                backgroundColor: Object.keys(stats.convenios_estados || {}).map(k => CONV_COLORES[k] || '#888'),
                borderWidth: 2,
                borderColor: '#ffffff',
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              cutout: '70%',
              plugins: { legend: { display: false }, tooltip: commonTooltip }
            }
          }}></canvas>
        </div>
        <div class="estado-bars sm-bars">
          {#each Object.entries(stats.convenios_estados || {}) as [k, v]}
            <div class="ebar">
              <span class="ebar-label">{k}</span>
              <div class="ebar-track">
                <div class="ebar-fill" style="width:{(v/(stats.kpis.total_convenios||1)*100).toFixed(0)}%;background:{CONV_COLORES[k]}"></div>
              </div>
              <span class="ebar-val">{v}</span>
            </div>
          {/each}
        </div>
      </div>

      <div class="chart-card sm">
        <h4 class="chart-title"><i class="bi bi-buildings-fill text-dorado"></i> Entidades por tipo</h4>
        <div class="chart-wrap h240">
          <canvas use:chartAction={{
            type: 'doughnut',
            data: {
              labels: stats.entidades_tipos?.labels || [],
              datasets: [{
                data: stats.entidades_tipos?.values || [],
                backgroundColor: PALETTE,
                borderWidth: 2,
                borderColor: '#ffffff',
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              cutout: '70%',
              plugins: {
                legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: commonTooltip
              }
            }
          }}></canvas>
        </div>
      </div>

      <div class="chart-card sm">
        <h4 class="chart-title"><i class="bi bi-calendar-week-fill text-azul"></i> Proyectos por período</h4>
        <div class="chart-wrap h240">
          <canvas use:chartAction={{
            type: 'bar',
            data: {
              labels: stats.por_periodo?.labels || [],
              datasets: [{
                label: 'Proyectos',
                data: stats.por_periodo?.values || [],
                backgroundColor: '#0d6efd',
                borderRadius: 6,
                barThickness: 24,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false }, tooltip: commonTooltip },
              scales: {
                x: { grid: { display: false } },
                y: { grid: { color: '#f0f4f1' }, ticks: { precision: 0 } }
              }
            }
          }}></canvas>
        </div>
      </div>
    </div>

    <!-- ÚLTIMOS PROYECTOS -->
    <div class="chart-card full-card">
      <div class="card-hdr-flex">
        <h4 class="chart-title"><i class="bi bi-clock-history text-verde"></i> ÚLTIMOS PROYECTOS REGISTRADOS</h4>
        <a href="/proyectos" class="link-proys">Ver todos los proyectos →</a>
      </div>
      <table class="mini-table">
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre del Proyecto</th>
            <th>Facultad</th>
            <th>Período de inicio</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {#each stats.ultimos_proyectos || [] as p}
            <tr>
              <td><span class="code">{p.codigo}</span></td>
              <td class="td-trunc" title={p.nombre}>{p.nombre}</td>
              <td class="txt-sm">{p.facultad}</td>
              <td class="txt-sm">{p.periodo}</td>
              <td>
                <span class="badge-est" style="background:{ESTADO_COLORES[p.estado]}18;color:{ESTADO_COLORES[p.estado]};border:1px solid {ESTADO_COLORES[p.estado]}40">
                  {ESTADO_LABEL[p.estado] || p.estado}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

  </div>
{:else}
  <div class="loading">No se pudieron cargar los datos del reporte.</div>
{/if}

<style>
  .subbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 24px; background: #fff; border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .rep-actions { display: flex; align-items: center; gap: 12px; }
  .filter-group {
    display: flex; align-items: center; gap: 8px;
    background: #fafafa; border: 1.5px solid var(--borde, #e0e0e0);
    border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #444;
  }
  .rep-select {
    border: none; background: transparent; font-family: inherit; font-size: 0.8rem;
    font-weight: 700; color: #333; outline: none; cursor: pointer;
  }
  .btn-print {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--verde, #1b5e20); color: #fff; border: none; border-radius: 20px;
    padding: 7px 18px; font-size: 0.8rem; font-weight: 800; cursor: pointer;
    transition: background 0.2s; font-family: inherit;
  }
  .btn-print:hover { background: #134217; }

  .loading {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    padding: 60px; font-size: 0.9rem; font-weight: 700; color: #666;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }

  .rep-wrap { padding: 20px 24px; display: flex; flex-direction: column; gap: 18px; }

  /* KPIs Grid */
  .kpis-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
  .kpi-card {
    background: #fff; border-radius: 14px; border: 1px solid var(--borde, #ebebeb);
    padding: 16px 18px; display: flex; align-items: center; gap: 14px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.04); transition: transform 0.18s, box-shadow 0.18s;
  }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.07); }
  .kpi-icon {
    width: 44px; height: 44px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;
  }
  .kpi-card.verde .kpi-icon { background: #e8f5e9; color: var(--verde, #1b5e20); }
  .kpi-card.dorado .kpi-icon { background: #fff8e1; color: #dba112; }
  .kpi-card.azul .kpi-icon { background: #e8f0ff; color: #0d6efd; }
  .kpi-card.esmeralda .kpi-icon { background: #e0f2f1; color: #00897b; }
  .kpi-card.naranja .kpi-icon { background: #fff3e0; color: #fd7e14; }

  .kpi-body { display: flex; flex-direction: column; gap: 2px; }
  .kpi-num { font-size: 1.35rem; font-weight: 900; color: #222; line-height: 1.1; }
  .kpi-label { font-size: 0.7rem; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi-sub { font-size: 0.68rem; color: #777; font-weight: 600; }

  /* Charts Row */
  .charts-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .chart-card {
    background: #fff; border-radius: 14px; border: 1px solid var(--borde, #ebebeb);
    padding: 20px 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); display: flex; flex-direction: column;
  }
  .chart-card.sm { min-width: 0; }
  .chart-card.lg { grid-column: span 2; }
  .chart-card.full-card { grid-column: 1 / -1; }

  .chart-title {
    font-size: 0.84rem; font-weight: 800; color: #222; text-transform: uppercase; letter-spacing: 0.04em;
    margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
  }
  .chart-wrap { position: relative; width: 100%; }
  .h180 { height: 180px; }
  .h200 { height: 200px; }
  .h240 { height: 240px; }
  .h260 { height: 260px; }
  .h300 { height: 300px; }

  /* Estado bars */
  .estado-bars { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
  .sm-bars { gap: 6px; }
  .ebar { display: flex; align-items: center; gap: 10px; font-size: 0.75rem; }
  .ebar-label { min-width: 90px; color: #444; font-weight: 700; }
  .ebar-track { flex: 1; height: 7px; background: #f0f4f1; border-radius: 4px; overflow: hidden; }
  .ebar-fill { height: 100%; border-radius: 4px; transition: width 0.4s; }
  .ebar-val { min-width: 50px; text-align: right; font-weight: 800; color: #222; }
  .ebar-val small { font-size: 0.7rem; color: #777; font-weight: 600; }

  /* Mini table */
  .card-hdr-flex { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .link-proys { font-size: 0.8rem; font-weight: 800; color: var(--verde, #1b5e20); text-decoration: none; }
  .link-proys:hover { text-decoration: underline; }

  .mini-table { width: 100%; border-collapse: collapse; text-align: left; }
  .mini-table th { font-size: 0.7rem; font-weight: 800; color: #777; text-transform: uppercase; letter-spacing: 0.04em; padding: 10px 14px; border-bottom: 1.5px dashed #edf5ee; }
  .mini-table td { padding: 11px 14px; font-size: 0.84rem; border-bottom: 1px solid #f4f7f4; }
  .code { background: #f0f7f1; color: var(--verde, #1b5e20); padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; font-family: monospace; }
  .td-trunc { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 700; color: #333; }
  .txt-sm { font-size: 0.78rem; color: #666; font-weight: 600; }
  .badge-est { padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; }

  @media (max-width: 992px) {
    .chart-card.lg { grid-column: span 1; }
  }
  @media print {
    .subbar, .btn-print, .rep-actions { display: none !important; }
    .rep-wrap { padding: 0 !important; gap: 10px !important; }
    .chart-card { break-inside: avoid; border: 1px solid #ddd !important; box-shadow: none !important; }
  }
</style>
