<script>
  import { onMount } from 'svelte';

    let stats = $state(null);
  let loading = $state(true);

  const ESTADO_COLORES = {
    EN_EJECUCION:'#1b7505', PROPUESTO:'#dba112', APROBADO:'#0d6efd',
    EN_CIERRE:'#fd7e14', DETENIDO:'#dc3545', FINALIZADO:'#a8a8a7', RECHAZADO:'#6c757d',
  };
  const ESTADO_LABEL = {
    EN_EJECUCION:'En ejecución', PROPUESTO:'Propuesto', APROBADO:'Aprobado',
    EN_CIERRE:'En cierre', DETENIDO:'Detenido', FINALIZADO:'Finalizado', RECHAZADO:'Rechazado',
  };
  const CONV_COLORES = { VIGENTE:'#1b7505', VENCIDO:'#e65100', RENOVADO:'#1565c0', CANCELADO:'#a8a8a7' };
  const PALETTE = ['#1b7505','#dba112','#0d6efd','#fd7e14','#dc3545','#a8a8a7','#6c757d','#20c997','#0dcaf0'];

  let chartEstados, chartFacultad, chartProvincia, chartCanton, chartConvEstados, chartEntTipos, chartPeriodo;

  onMount(async () => {
    try {
      const res = await fetch('/api/reportes/stats/', { credentials:'include' });
      stats = await res.json();
    } catch { loading = false; return; }
    loading = false;

    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);
    Chart.defaults.font.family = "'Nunito', sans-serif";

    // 1. Proyectos por estado (Donut)
    const estadoKeys = Object.keys(stats.estados);
    new Chart(chartEstados, {
      type: 'doughnut',
      data: {
        labels: estadoKeys.map(k => ESTADO_LABEL[k] || k),
        datasets: [{ data: estadoKeys.map(k => stats.estados[k]), backgroundColor: estadoKeys.map(k => ESTADO_COLORES[k] || '#888') }]
      },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}} }
    });

    // 2. Por facultad (Bar horizontal)
    new Chart(chartFacultad, {
      type: 'bar',
      data: {
        labels: stats.por_facultad.labels,
        datasets: [{ data: stats.por_facultad.values, backgroundColor: PALETTE }]
      },
      options: { responsive:true, maintainAspectRatio:false, indexAxis:'y', plugins:{legend:{display:false}}, scales:{ x:{grid:{color:'#f0f0f0'}}, y:{grid:{display:false}} } }
    });

    // 3. Por provincia (Bar horizontal)
    new Chart(chartProvincia, {
      type: 'bar',
      data: {
        labels: stats.por_provincia.labels,
        datasets: [{ data: stats.por_provincia.values, backgroundColor: 'rgba(27,117,5,.8)' }]
      },
      options: { responsive:true, maintainAspectRatio:false, indexAxis:'y', plugins:{legend:{display:false}}, scales:{ x:{grid:{color:'#f0f0f0'}}, y:{grid:{display:false}} } }
    });

    // 4. Por cantón (Bar horizontal)
    new Chart(chartCanton, {
      type: 'bar',
      data: {
        labels: stats.por_canton.labels,
        datasets: [{ data: stats.por_canton.values, backgroundColor: 'rgba(219,161,18,.8)' }]
      },
      options: { responsive:true, maintainAspectRatio:false, indexAxis:'y', plugins:{legend:{display:false}}, scales:{ x:{grid:{color:'#f0f0f0'}}, y:{grid:{display:false}} } }
    });

    // 5. Convenios por estado (Donut)
    const convKeys = Object.keys(stats.convenios_estados);
    new Chart(chartConvEstados, {
      type: 'doughnut',
      data: {
        labels: convKeys,
        datasets: [{ data: convKeys.map(k => stats.convenios_estados[k]), backgroundColor: convKeys.map(k => CONV_COLORES[k] || '#888') }]
      },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}} }
    });

    // 6. Entidades por tipo (Donut)
    new Chart(chartEntTipos, {
      type: 'doughnut',
      data: {
        labels: stats.entidades_tipos.labels,
        datasets: [{ data: stats.entidades_tipos.values, backgroundColor: PALETTE }]
      },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'right'}} }
    });

    // 7. Por período (Bar)
    new Chart(chartPeriodo, {
      type: 'bar',
      data: {
        labels: stats.por_periodo.labels,
        datasets: [{ data: stats.por_periodo.values, backgroundColor: 'rgba(13,105,253,.8)' }]
      },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#f0f0f0'}} } }
    });
  });
</script>

<svelte:head><title>Reportes — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a><span class="sep">/</span>
    <span class="current">Reportes</span><span class="sep">/</span>
  </nav>
</div>

{#if loading}
  <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando estadísticas...</div>
{:else if stats}
<div class="rep-wrap">

  <!-- KPIs -->
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
        <span class="kpi-label">Total Entidades</span>
        <span class="kpi-sub">Activas</span>
      </div>
    </div>
    <div class="kpi-card azul">
      <div class="kpi-icon"><i class="bi bi-file-earmark-text"></i></div>
      <div class="kpi-body">
        <span class="kpi-num">{stats.kpis.total_convenios}</span>
        <span class="kpi-label">Total Convenios</span>
        <span class="kpi-sub">Registrados</span>
      </div>
    </div>
    <div class="kpi-card verde">
      <div class="kpi-icon"><i class="bi bi-geo-alt-fill"></i></div>
      <div class="kpi-body">
        <span class="kpi-num">{stats.kpis.con_geo}</span>
        <span class="kpi-label">Georreferenciados</span>
        <span class="kpi-sub">Visibles en mapa</span>
      </div>
    </div>
    <div class="kpi-card naranja">
      <div class="kpi-icon"><i class="bi bi-play-circle-fill"></i></div>
      <div class="kpi-body">
        <span class="kpi-num">{stats.kpis.pct_ejecucion}%</span>
        <span class="kpi-label">En Ejecución</span>
        <span class="kpi-sub">{stats.kpis.en_ejecucion} proyectos</span>
      </div>
    </div>
    <div class="kpi-card gris">
      <div class="kpi-icon"><i class="bi bi-check-circle-fill"></i></div>
      <div class="kpi-body">
        <span class="kpi-num">{stats.kpis.pct_finalizado}%</span>
        <span class="kpi-label">Finalizados</span>
        <span class="kpi-sub">{stats.kpis.finalizado} proyectos</span>
      </div>
    </div>
  </div>

  <!-- Fila 2: Estado + Facultad -->
  <div class="charts-row">
    <div class="chart-card sm">
      <h4 class="chart-title">Proyectos por estado</h4>
      <div class="chart-wrap h220"><canvas bind:this={chartEstados}></canvas></div>
      <div class="estado-bars">
        {#each Object.entries(stats.estados) as [k, v]}
          <div class="ebar">
            <span class="ebar-label">{ESTADO_LABEL[k] || k}</span>
            <div class="ebar-track">
              <div class="ebar-fill" style="width:{(v/stats.kpis.total_proyectos*100||0).toFixed(0)}%;background:{ESTADO_COLORES[k]}"></div>
            </div>
            <span class="ebar-val">{v}</span>
          </div>
        {/each}
      </div>
    </div>
    <div class="chart-card lg">
      <h4 class="chart-title">Proyectos por facultad</h4>
      <div class="chart-wrap h260"><canvas bind:this={chartFacultad}></canvas></div>
    </div>
  </div>

  <!-- Fila 3: Provincia + Cantón -->
  <div class="charts-row">
    <div class="chart-card">
      <h4 class="chart-title">Distribución por provincia</h4>
      <div class="chart-wrap h260"><canvas bind:this={chartProvincia}></canvas></div>
    </div>
    <div class="chart-card">
      <h4 class="chart-title">Top 8 cantones</h4>
      <div class="chart-wrap h260"><canvas bind:this={chartCanton}></canvas></div>
    </div>
  </div>

  <!-- Fila 4: Convenios + Entidades + Períodos -->
  <div class="charts-row">
    <div class="chart-card sm">
      <h4 class="chart-title">Convenios por estado</h4>
      <div class="chart-wrap h180"><canvas bind:this={chartConvEstados}></canvas></div>
      <div class="estado-bars sm-bars">
        {#each Object.entries(stats.convenios_estados) as [k, v]}
          <div class="ebar">
            <span class="ebar-label">{k}</span>
            <div class="ebar-track"><div class="ebar-fill" style="width:{(v/(stats.kpis.total_convenios||1)*100).toFixed(0)}%;background:{CONV_COLORES[k]}"></div></div>
            <span class="ebar-val">{v}</span>
          </div>
        {/each}
      </div>
    </div>
    <div class="chart-card sm">
      <h4 class="chart-title">Entidades por tipo</h4>
      <div class="chart-wrap h180"><canvas bind:this={chartEntTipos}></canvas></div>
    </div>
    <div class="chart-card sm">
      <h4 class="chart-title">Proyectos por período</h4>
      <div class="chart-wrap h180"><canvas bind:this={chartPeriodo}></canvas></div>
    </div>
  </div>

  <!-- Últimos proyectos -->
  <div class="chart-card full-card">
    <h4 class="chart-title">Últimos proyectos registrados</h4>
    <table class="mini-table">
      <thead>
        <tr><th>Código</th><th>Nombre</th><th>Facultad</th><th>Período</th><th>Estado</th></tr>
      </thead>
      <tbody>
        {#each stats.ultimos_proyectos as p}
          <tr>
            <td><span class="code">{p.codigo}</span></td>
            <td class="td-trunc">{p.nombre}</td>
            <td class="txt-sm">{p.facultad}</td>
            <td class="txt-sm">{p.periodo}</td>
            <td>
              <span class="badge-est" style="background:{ESTADO_COLORES[p.estado]}20;color:{ESTADO_COLORES[p.estado]}">
                {ESTADO_LABEL[p.estado] || p.estado}
              </span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
    <div class="ver-todos">
      <a href="/proyectos">Ver todos los proyectos →</a>
    </div>
  </div>

</div>
{:else}
  <div class="loading">No se pudieron cargar los datos</div>
{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }

.rep-wrap { padding:20px 24px;display:flex;flex-direction:column;gap:16px; }

/* KPIs */
.kpis-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px; }
.kpi-card { background:#fff;border-radius:14px;border:1px solid var(--borde);padding:16px 18px;display:flex;align-items:center;gap:14px;box-shadow:var(--sombra); }
.kpi-icon { width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0; }
.kpi-card.verde .kpi-icon { background:var(--verde-claro);color:var(--verde); }
.kpi-card.dorado .kpi-icon { background:#fff8e1;color:var(--dorado); }
.kpi-card.azul .kpi-icon { background:#e8f0ff;color:#0d6efd; }
.kpi-card.naranja .kpi-icon { background:#fff3e0;color:#fd7e14; }
.kpi-card.gris .kpi-icon { background:#f5f5f5;color:var(--gris); }
.kpi-body { display:flex;flex-direction:column;gap:2px; }
.kpi-num { font-size:1.5rem;font-weight:900;color:var(--negro);line-height:1; }
.kpi-label { font-size:.72rem;font-weight:800;color:#555;text-transform:uppercase;letter-spacing:.04em; }
.kpi-sub { font-size:.68rem;color:var(--gris); }

/* Charts */
.charts-row { display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px; }
.chart-card { background:#fff;border-radius:14px;border:1px solid var(--borde);padding:18px 20px;box-shadow:var(--sombra); }
.chart-card.sm { min-width:0; }
.chart-card.lg { grid-column:span 2; }
.chart-card.full-card { grid-column:1/-1; }
.chart-title { font-size:.82rem;font-weight:800;color:var(--negro);margin-bottom:14px;text-transform:uppercase;letter-spacing:.04em; }
.chart-wrap { position:relative; }
.chart-wrap canvas { width:100%!important; }
.h180 { height:180px; }
.h220 { height:220px; }
.h260 { height:260px; }

/* Estado bars */
.estado-bars { margin-top:12px;display:flex;flex-direction:column;gap:6px; }
.sm-bars { gap:4px; }
.ebar { display:flex;align-items:center;gap:8px;font-size:.72rem; }
.ebar-label { min-width:80px;color:#555;font-weight:600; }
.ebar-track { flex:1;height:6px;background:#f0f0f0;border-radius:4px;overflow:hidden; }
.ebar-fill { height:100%;border-radius:4px;transition:width .4s; }
.ebar-val { min-width:22px;text-align:right;font-weight:700;color:var(--negro); }

/* Mini table */
.mini-table { width:100%;border-collapse:collapse; }
.mini-table th { font-size:.72rem;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.04em;padding:8px 12px;border-bottom:1px solid #f0f0f0; }
.mini-table td { padding:9px 12px;font-size:.83rem;border-bottom:1px solid #f9f9f9; }
.td-trunc { max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.txt-sm { font-size:.75rem;color:var(--gris); }
.badge-est { padding:3px 9px;border-radius:20px;font-size:.7rem;font-weight:700; }
.ver-todos { text-align:right;margin-top:12px;font-size:.8rem; }
.ver-todos a { color:var(--verde);font-weight:700; }
</style>
