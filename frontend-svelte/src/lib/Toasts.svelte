<script>
  import { toasts, dismiss } from '$lib/toast';

  const META = {
    success: { icon: 'bi-check-circle-fill', title: '¡Listo!',  color: '#1b7505', bg: '#eef7e8' },
    error:   { icon: 'bi-x-circle-fill',     title: 'Error',    color: '#dc3545', bg: '#fdecec' },
    warning: { icon: 'bi-exclamation-triangle-fill', title: 'Atención', color: '#dba112', bg: '#fff8e6' },
    info:    { icon: 'bi-info-circle-fill',   title: 'Aviso',    color: '#0d6efd', bg: '#e8f0ff' },
  };
</script>

<div class="toast-stack">
  {#each $toasts as t (t.id)}
    {@const m = META[t.type] || META.info}
    <div class="toast" style="--c:{m.color};--bg:{m.bg}">
      <div class="t-ic"><i class="bi {m.icon}"></i></div>
      <div class="t-body">
        <div class="t-title">{m.title}</div>
        <div class="t-msg">{t.message}</div>
      </div>
      <button class="t-close" onclick={() => dismiss(t.id)} aria-label="Cerrar"><i class="bi bi-x-lg"></i></button>
      <div class="t-bar"></div>
    </div>
  {/each}
</div>

<style>
  .toast-stack {
    position: fixed; bottom: 52px; right: 20px; z-index: 9999;
    display: flex; flex-direction: column-reverse; gap: 10px; max-width: 370px; width: calc(100vw - 40px);
    pointer-events: none;
  }
  .toast {
    pointer-events: auto; position: relative; overflow: hidden;
    display: flex; align-items: flex-start; gap: 12px;
    background: #fff; border-radius: 12px; padding: 13px 14px 14px 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,.16), 0 2px 6px rgba(0,0,0,.08);
    border-left: 5px solid var(--c);
    animation: toast-in .28s cubic-bezier(.2,.9,.3,1.3);
  }
  .t-ic { color: var(--c); font-size: 1.25rem; line-height: 1; flex-shrink: 0; margin-top: 1px; }
  .t-body { flex: 1; min-width: 0; }
  .t-title { font-size: .82rem; font-weight: 800; color: var(--c); line-height: 1.2; }
  .t-msg { font-size: .8rem; color: #444; font-weight: 600; margin-top: 2px; line-height: 1.35; word-break: break-word; }
  .t-close {
    background: none; border: none; color: #bbb; font-size: .7rem; flex-shrink: 0;
    width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer;
  }
  .t-close:hover { background: #f0f0f0; color: #666; }
  .t-bar { position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: var(--c); opacity: .3; }

  @keyframes toast-in {
    from { transform: translateY(20px); opacity: 0; }
    to   { transform: translateY(0); opacity: 1; }
  }
</style>
