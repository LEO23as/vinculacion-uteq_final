<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

  let stats      = $state(null);
  let cargando   = $state(true);
  let buscar     = $state('');

  const modulos = [
    { href: '/mapa',       icon: '/icons/mapa.png',       label: 'Mapa',       desc: 'Proyectos georreferenciados',  key: null,        disabled: false },
    { href: '/proyectos',  icon: '/icons/proyectos.png',  label: 'Proyectos',  desc: 'Gestión de proyectos',         key: 'proyectos', disabled: false },
    { href: '/entidades',  icon: '/icons/entidades.png',  label: 'Entidades',  desc: 'Organizaciones aliadas',       key: 'entidades', disabled: false },
    { href: '/convenios',  icon: '/icons/convenios.png',  label: 'Convenios',  desc: 'Acuerdos institucionales',     key: 'convenios', disabled: false },
    { href: '/periodos',   icon: '/icons/periodos.png',   label: 'Períodos',   desc: 'Períodos académicos',          key: 'periodos',  disabled: false },
    { href: '/facultades', icon: '/icons/facultades.png', label: 'Facultades', desc: 'Unidades académicas',          key: 'facultades',disabled: false },
    { href: '/reportes',   icon: '/icons/reportes.png',   label: 'Reportes',   desc: 'Estadísticas y gráficas',      key: null,        disabled: false },
    { href: null,          icon: '/icons/docentes.png',   label: 'Docentes',   desc: 'Próximamente',                 key: null,        disabled: true  },
    { href: null,          icon: '/icons/usuarios.png',   label: 'Usuarios',   desc: 'Gestión de accesos',           key: null,        disabled: true  },
  ];

  let filtered = $derived(
    buscar.trim()
      ? modulos.filter(m => m.label.toLowerCase().includes(buscar.toLowerCase()))
      : modulos
  );

  onMount(async () => {
    try { stats = await fetchAPI('/api/dashboard/stats/'); } catch {}
    cargando = false;
  });
</script>

<svelte:head><title>Dashboard — SGV UTEQ</title></svelte:head>

<!-- BARRA SECUNDARIA -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Dashboard</span><span class="sep">/</span>
  </nav>
  <div class="search-wrap">
    <i class="bi bi-search"></i>
    <input bind:value={buscar} placeholder="Buscar módulo..." />
  </div>
</div>

<!-- CUERPO PRINCIPAL -->
<div class="dash-body">

  <!-- PANEL IZQUIERDO: imagen informativa -->
  <aside class="info-panel">
    <div class="info-card">
      <div class="info-img-wrap">
        <img src="/logo-uteq.png" alt="UTEQ" class="info-logo" />
      </div>
      <div class="info-text">
        <h3>Departamento de Vinculación</h3>
        <div class="info-sep"></div>
        <p>Sistema de Gestión de Proyectos</p>
      </div>
    </div>

    <div class="info-card notice">
      <div class="notice-icon"><i class="bi bi-megaphone-fill"></i></div>
      <div class="notice-body">
        <strong>Avisos</strong>
        <p>No hay avisos por el momento.</p>
      </div>
    </div>
  </aside>

  <!-- MÓDULOS -->
  <section class="modulos-wrap">
    <div class="modulos-grid">
      {#each filtered as m}
        {#if m.disabled}
          <div class="mod-card disabled">
            <i class="bi bi-star-fill mod-star"></i>
            <div class="mod-icon-wrap">
              <img src={m.icon} alt={m.label} class="mod-img" />
            </div>
            <div class="mod-name">{m.label}</div>
            <div class="mod-desc">{m.desc}</div>
          </div>
        {:else}
          <a href={m.href} class="mod-card">
            <i class="bi bi-star-fill mod-star"></i>
            {#if !cargando && stats && m.key && stats[m.key] !== undefined}
              <span class="mod-badge">{stats[m.key]}</span>
            {/if}
            <div class="mod-icon-wrap">
              <img src={m.icon} alt={m.label} class="mod-img" />
            </div>
            <div class="mod-name">{m.label}</div>
            <div class="mod-desc">{m.desc}</div>
          </a>
        {/if}
      {/each}
    </div>
  </section>

</div>

<style>
/* ── SUBBAR ── */
.subbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 24px;
  background: #fff;
  border-bottom: 1px solid var(--borde);
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--gris-claro);
  border: 1.5px solid var(--borde);
  border-radius: 10px;
  padding: 0 14px;
  min-width: 260px;
  transition: border-color .2s;
}
.search-wrap:focus-within { border-color: var(--verde); background: #fff; }
.search-wrap i { color: var(--gris); }
.search-wrap input {
  border: none; outline: none;
  padding: 8px 0;
  font-size: .88rem;
  font-family: inherit;
  background: transparent;
  width: 100%;
}

/* ── BODY ── */
.dash-body {
  display: flex;
  gap: 0;
  align-items: flex-start;
  padding: 20px 24px;
  gap: 20px;
}

/* ── PANEL IZQUIERDO ── */
.info-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 900px) { .info-panel { display: none; } }

.info-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--borde);
  overflow: hidden;
  box-shadow: var(--sombra);
}

.info-img-wrap {
  background: var(--verde);
  padding: 28px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-logo {
  width: 140px;
  filter: brightness(0) invert(1);
}
.info-text {
  padding: 16px 16px 20px;
  text-align: center;
}
.info-text h3 {
  font-size: .9rem;
  font-weight: 800;
  color: var(--negro);
  margin-bottom: 8px;
}
.info-sep {
  width: 40px;
  height: 3px;
  background: var(--dorado);
  border-radius: 2px;
  margin: 0 auto 10px;
}
.info-text p {
  font-size: .78rem;
  color: var(--dorado);
  font-weight: 700;
}

.notice {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 10px;
}
.notice-icon {
  width: 36px; height: 36px;
  background: var(--verde-claro);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: var(--verde);
  font-size: 1.1rem;
}
.notice-body strong {
  font-size: .85rem;
  font-weight: 800;
  color: var(--negro);
  display: block;
  margin-bottom: 4px;
}
.notice-body p {
  font-size: .75rem;
  color: var(--gris);
}

/* ── MÓDULOS ── */
.modulos-wrap { flex: 1; min-width: 0; }

.modulos-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
@media (max-width: 900px) { .modulos-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 600px) { .modulos-grid { grid-template-columns: repeat(2, 1fr); } }

.mod-card {
  background: #fff;
  border: 1.5px solid #c8e6bc;
  border-radius: 16px;
  padding: 22px 10px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  text-decoration: none;
  position: relative;
  transition: border-color .2s, box-shadow .2s, transform .18s;
  min-height: 195px;
}
.mod-card:hover {
  border-color: var(--verde);
  box-shadow: 0 8px 28px rgba(27,117,5,.16);
  transform: translateY(-4px);
}
.mod-card.disabled { opacity: .45; cursor: not-allowed; pointer-events: none; }

.mod-star {
  position: absolute; top: 9px; left: 10px;
  color: #e8d98a; font-size: .72rem;
  transition: color .2s;
}
.mod-card:hover .mod-star { color: var(--dorado); }

.mod-badge {
  position: absolute; top: 8px; right: 10px;
  background: var(--verde); color: #fff;
  font-size: .62rem; font-weight: 800;
  padding: 2px 7px; border-radius: 20px;
}

/* Contenedor ícono: caja fija para que todos los PNG queden iguales */
.mod-icon-wrap {
  width: 90px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: 10px;
}
.mod-img {
  width: 90px;
  height: 90px;
  object-fit: contain;
}

.mod-name {
  font-size: .88rem; font-weight: 800;
  color: #1a1a1a; margin-bottom: 3px;
  line-height: 1.2;
}
.mod-card:hover .mod-name { color: var(--verde); }

.mod-desc { font-size: .72rem; color: #b0b0b0; font-weight: 500; }
</style>
