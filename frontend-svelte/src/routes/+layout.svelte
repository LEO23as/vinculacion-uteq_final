<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { get } from 'svelte/store';
  import { user, checkAuth, logout, capaNBIActiva } from '$lib/stores';

  let { children } = $props();

  const PUBLIC     = ['/'];
  let authChecked  = $state(false);
  let capasAbiertas = $state(false);

  onMount(async () => {
    await checkAuth();
    authChecked = true;
    const path = get(page).url.pathname;
    if (!$user && !PUBLIC.includes(path)) goto('/');
  });

  async function handleLogout() {
    await logout();
    goto('/');
  }

  const ESTADOS = [
    { val:'EN_EJECUCION', label:'En ejecución', color:'#1b7505' },
    { val:'PROPUESTO',    label:'Propuesto',    color:'#dba112' },
    { val:'APROBADO',     label:'Aprobado',     color:'#0d6efd' },
    { val:'EN_CIERRE',    label:'En cierre',    color:'#fd7e14' },
    { val:'DETENIDO',     label:'Detenido',     color:'#dc3545' },
    { val:'FINALIZADO',   label:'Finalizado',   color:'#a8a8a7' },
    { val:'RECHAZADO',    label:'Rechazado',    color:'#6c757d' },
  ];

  const SIDEBAR_LINKS = {
    dashboard: { modulo: 'Dashboard',             links: [] },
    mapa:      { modulo: 'Mapa',                  links: [
                   { href: '/mapa', icon: 'bi-map', label: 'Ver mapa interactivo' },
                 ]},
    proyectos: { modulo: 'Proyectos',             links: [{ href: '/proyectos', icon: 'bi-list-ul', label: 'Lista de proyectos'  }] },
    entidades: { modulo: 'Entidades',             links: [{ href: '/entidades', icon: 'bi-list-ul', label: 'Lista de entidades'  }] },
    convenios: { modulo: 'Convenios',             links: [{ href: '/convenios', icon: 'bi-list-ul', label: 'Lista de convenios'  }] },
    periodos:  { modulo: 'Períodos',              links: [{ href: '/periodos',  icon: 'bi-list-ul', label: 'Lista de períodos'   }] },
    facultades:{ modulo: 'Facultades y Carreras', links: [
                   { href: '/facultades', icon: 'bi-bank', label: 'Facultades' },
                   { href: '/carreras',   icon: 'bi-book', label: 'Carreras'   },
                 ]},
    reportes:  { modulo: 'Reportes',             links: [{ href: '/reportes',  icon: 'bi-graph-up', label: 'Estadísticas' }] },
  };

  function getKey(pathname) {
    if (pathname.startsWith('/mapa'))       return 'mapa';
    if (pathname.startsWith('/proyectos'))  return 'proyectos';
    if (pathname.startsWith('/entidades'))  return 'entidades';
    if (pathname.startsWith('/convenios'))  return 'convenios';
    if (pathname.startsWith('/periodos'))   return 'periodos';
    if (pathname.startsWith('/facultades') || pathname.startsWith('/carreras')) return 'facultades';
    if (pathname.startsWith('/reportes'))   return 'reportes';
    return 'dashboard';
  }

  let moduloKey   = $derived(getKey($page.url.pathname));
  let moduloData  = $derived(SIDEBAR_LINKS[moduloKey]);
  let isDashboard = $derived($page.url.pathname === '/dashboard');
  let isMapa      = $derived($page.url.pathname.startsWith('/mapa'));
</script>

{#if PUBLIC.includes($page.url.pathname)}
  {#if authChecked}
    {@render children()}
  {/if}
{:else if !$user}
  {#if authChecked}
    {@render children()}
  {:else}
    <div class="checking">
      <i class="bi bi-arrow-repeat spin"></i> Verificando sesión...
    </div>
  {/if}
{:else}
  <div class="app-shell">

    <!-- NAVBAR -->
    <header class="navbar">
      <div class="navbar-left">
        <img src="/logo-uteq.png" alt="UTEQ" class="nav-logo" />
        <span class="nav-title">SGV <span class="nav-sub">| Sistema de Gestión de Vinculación</span></span>
      </div>
      <div class="navbar-right">
        <button class="icon-btn" title="Notificaciones">
          <i class="bi bi-bell-fill"></i>
          <span class="badge-dot">0</span>
        </button>
        {#if $user?.periodo}
          <div class="periodo-badge">
            <i class="bi bi-calendar-event-fill"></i>
            <span>{$user.periodo.codigo}</span>
          </div>
        {/if}
        <div class="user-badge">
          <div class="user-avatar">{($user?.nombre || 'U')[0].toUpperCase()}</div>
          <div class="user-info">
            <span class="user-name">{$user?.nombre}</span>
            <span class="user-rol">{$user?.rol}</span>
          </div>
          <button class="btn-logout" onclick={handleLogout} title="Cerrar sesión">
            <i class="bi bi-box-arrow-right"></i>
          </button>
        </div>
      </div>
    </header>

    <!-- CUERPO -->
    <div class="body-row">

      {#if !isDashboard}
      <!-- COLUMNA IZQUIERDA -->
      <div class="left-col">

        <!-- MENÚ MÓDULO -->
        <div class="float-card">
          <p class="fc-label">MÓDULO</p>

          {#each moduloData.links as link}
            <a
              href={link.href}
              class="fc-link"
              class:fc-active={$page.url.pathname === link.href || $page.url.pathname.startsWith(link.href + '/')}
            >
              <i class="bi {link.icon}"></i>
              <span>{link.label}</span>
            </a>
          {/each}

          <!-- Capas expandible: solo en mapa -->
          {#if isMapa}
            <button class="fc-capas-btn" onclick={() => capasAbiertas = !capasAbiertas}>
              <i class="bi bi-layers"></i>
              <span>Capas temáticas</span>
              <i class="bi bi-chevron-{capasAbiertas ? 'up' : 'down'} fc-caret"></i>
            </button>
            {#if capasAbiertas}
              <div class="fc-capas-panel">
                <label class="fc-check">
                  <input type="checkbox" checked disabled />
                  <span>Proyectos vinculación</span>
                </label>
                <label class="fc-check">
                  <input
                    type="checkbox"
                    checked={$capaNBIActiva}
                    onchange={(e) => capaNBIActiva.set(e.target.checked)}
                  />
                  <span>NBI por Sector (INEC 2022)</span>
                </label>
              </div>
            {/if}
          {/if}

          <div class="fc-divider"></div>

          <a href="/dashboard" class="fc-link fc-home">
            <i class="bi bi-house-door"></i>
            <span>Volver al inicio</span>
          </a>
        </div>

        <!-- ESTADOS: solo en mapa, debajo del menú -->
        {#if isMapa}
        <div class="estados-card">
          <p class="sc-label">ESTADOS</p>
          <div class="sc-pills">
            {#each ESTADOS as e}
              <span class="sc-pill" style="--c:{e.color}">
                <span class="sc-dot"></span>{e.label}
              </span>
            {/each}
          </div>
        </div>
        {/if}

      </div>
      {/if}

      <!-- CONTENIDO -->
      <main class="content">
        {@render children()}
      </main>

    </div>

    <!-- FOOTER -->
    <footer class="app-footer">
      <span>Universidad Técnica Estatal de Quevedo</span>
      <span>© 2026 — Todos los derechos reservados</span>
    </footer>

  </div>
{/if}

<style>
/* ── GENERAL ── */
.app-shell { display:flex;flex-direction:column;min-height:100vh;background:#f4f6f3; }
.checking  { display:flex;align-items:center;justify-content:center;height:100vh;color:#888;font-family:Nunito,sans-serif;font-size:.9rem;gap:10px; }

/* ── NAVBAR ── */
.navbar {
  display:flex;align-items:center;justify-content:space-between;
  background:var(--verde);height:56px;padding:0 20px;
  position:sticky;top:0;z-index:200;
  box-shadow:0 2px 8px rgba(0,0,0,.15);
}
.navbar-left  { display:flex;align-items:center;gap:10px; }
.navbar-right { display:flex;align-items:center;gap:10px; }
.nav-logo  { height:36px;filter:brightness(0) invert(1); }
.nav-title { color:#fff;font-weight:800;font-size:1.05rem; }
.nav-sub   { font-weight:500;font-size:.85rem;opacity:.85; }

.icon-btn {
  position:relative;background:rgba(255,255,255,.15);border:none;border-radius:50%;
  width:36px;height:36px;display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:1rem;cursor:pointer;transition:background .2s;
}
.icon-btn:hover { background:rgba(255,255,255,.25); }
.badge-dot {
  position:absolute;top:3px;right:3px;background:var(--dorado);color:#fff;
  font-size:.55rem;font-weight:800;width:14px;height:14px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;border:1.5px solid var(--verde);
}
.periodo-badge {
  background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
  border-radius:8px;padding:5px 12px;color:#fff;font-size:.78rem;font-weight:700;
  display:flex;align-items:center;gap:6px;
}
.user-badge {
  display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);
  border-radius:10px;padding:4px 10px 4px 4px;
}
.user-avatar {
  width:32px;height:32px;border-radius:50%;background:var(--dorado);color:#fff;
  font-weight:800;font-size:.95rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.user-info  { display:flex;flex-direction:column;line-height:1.2; }
.user-name  { color:#fff;font-weight:700;font-size:.8rem; }
.user-rol   { color:rgba(255,255,255,.7);font-size:.68rem; }
.btn-logout { background:none;border:none;color:rgba(255,255,255,.8);font-size:1rem;padding:2px 0 2px 6px;cursor:pointer;transition:color .2s; }
.btn-logout:hover { color:#fff; }

/* ── CUERPO ── */
.body-row { display:flex;flex:1;align-items:flex-start;min-height:0; }

/* ── COLUMNA IZQUIERDA ── */
.left-col {
  display:flex;flex-direction:column;gap:12px;
  width:252px;flex-shrink:0;
  position:sticky;top:68px;
  align-self:flex-start;
  padding:14px 12px 14px 16px;
}

/* ── ESTADOS CARD ── */
.estados-card {
  background:#fff;border-radius:14px;
  box-shadow:0 3px 14px rgba(0,0,0,.08),0 1px 3px rgba(0,0,0,.05);
  border:1px solid #ebebeb;
  padding:12px 14px 10px;
}
.sc-label {
  font-size:.58rem;font-weight:800;color:#bbb;
  text-transform:uppercase;letter-spacing:.1em;margin:0 0 8px;
}
.sc-pills { display:flex;flex-direction:column;gap:5px; }
.sc-pill {
  display:inline-flex;align-items:center;gap:7px;
  font-size:.74rem;font-weight:700;color:#444;
  border-radius:20px;padding:3px 10px 3px 7px;width:fit-content;
  border:1px solid color-mix(in srgb,var(--c) 35%,#e0e0e0);
  background:color-mix(in srgb,var(--c) 10%,#fff);
}
.sc-dot { width:9px;height:9px;border-radius:50%;background:var(--c);flex-shrink:0; }

/* ── MENÚ MÓDULO (float-card) ── */
.float-card {
  background:#fff;border-radius:16px;
  box-shadow:0 4px 20px rgba(0,0,0,.10),0 1px 4px rgba(0,0,0,.06);
  border:1px solid #ebebeb;
  padding:14px 0 10px;
}
.fc-label {
  font-size:.6rem;font-weight:800;color:#bbb;
  text-transform:uppercase;letter-spacing:.1em;
  padding:0 18px 8px;margin:0;
}
.fc-link {
  display:flex;align-items:center;gap:12px;
  padding:9px 18px;font-size:.85rem;font-weight:600;color:#3a3a5c;
  text-decoration:none;border-left:3px solid transparent;
  transition:background .14s,color .14s,border-color .14s;
}
.fc-link i { font-size:.95rem;color:#9999bb;flex-shrink:0;transition:color .14s; }
.fc-link:hover { background:var(--verde-claro);color:var(--verde);border-left-color:var(--verde); }
.fc-link:hover i { color:var(--verde); }
.fc-active { background:var(--verde-claro);color:var(--verde);border-left-color:var(--verde);font-weight:700; }
.fc-active i { color:var(--verde); }

/* Capas expandible */
.fc-capas-btn {
  display:flex;align-items:center;gap:12px;width:100%;
  padding:9px 18px;font-size:.85rem;font-weight:600;color:#3a3a5c;
  background:none;border:none;border-left:3px solid transparent;
  cursor:pointer;font-family:inherit;text-align:left;
  transition:background .14s,color .14s,border-color .14s;
}
.fc-capas-btn i:first-child { font-size:.95rem;color:#9999bb;flex-shrink:0; }
.fc-capas-btn span { flex:1; }
.fc-caret { font-size:.65rem;color:#bbb; }
.fc-capas-btn:hover { background:var(--verde-claro);color:var(--verde);border-left-color:var(--verde); }
.fc-capas-btn:hover i { color:var(--verde); }

.fc-capas-panel {
  background:#f9fafb;border-top:1px solid #f0f0f0;border-bottom:1px solid #f0f0f0;
  padding:10px 18px 10px 22px;display:flex;flex-direction:column;gap:6px;
}
.fc-check {
  display:flex;align-items:center;gap:8px;
  font-size:.78rem;color:#555;font-weight:600;cursor:pointer;
}
.fc-check input { accent-color:var(--verde); }

.fc-divider { height:1px;background:#f0f0f0;margin:8px 16px; }
.fc-home { color:#444 !important;font-weight:600 !important; }
.fc-home i { color:#aaa !important; }
.fc-home:hover { background:#f5faf0 !important;color:var(--verde) !important;border-left-color:var(--verde) !important; }
.fc-home:hover i { color:var(--verde) !important; }

/* ── CONTENIDO ── */
.content { flex:1;min-width:0;overflow-x:hidden;min-height:0;display:flex;flex-direction:column; }

/* ── FOOTER ── */
.app-footer {
  background:var(--verde);color:rgba(255,255,255,.8);
  font-size:.72rem;font-weight:600;padding:10px 24px;height:36px;
  display:flex;justify-content:space-between;align-items:center;
}

@keyframes spin { to { transform:rotate(360deg); } }
.spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
