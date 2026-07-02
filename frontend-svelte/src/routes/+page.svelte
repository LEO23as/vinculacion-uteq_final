<script>
  import { goto } from '$app/navigation';
  import { login, user } from '$lib/stores';
  import { onMount } from 'svelte';

  let username = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);

  onMount(() => {
    if ($user) goto('/dashboard');
  });

  async function handleLogin() {
    error = '';
    loading = true;
    try {
      await login(username, password);
      goto('/dashboard');
    } catch (e) {
      error = e?.error || 'Error al iniciar sesión';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Iniciar Sesión — SGV UTEQ</title></svelte:head>

<div class="login-page">
  <div class="login-card">
    <div class="login-header">
      <img src="/logo-uteq.png" alt="UTEQ" class="login-logo" />
      <h1>SGV</h1>
      <p>Sistema de Gestión de Vinculación</p>
    </div>

    <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }} class="login-form">
      {#if error}
        <div class="alert-error"><i class="bi bi-exclamation-circle"></i> {error}</div>
      {/if}

      <div class="field">
        <label for="username">Usuario</label>
        <div class="input-wrap">
          <i class="bi bi-person"></i>
          <input id="username" type="text" bind:value={username} placeholder="Ingrese su usuario" required />
        </div>
      </div>

      <div class="field">
        <label for="password">Contraseña</label>
        <div class="input-wrap">
          <i class="bi bi-lock"></i>
          <input id="password" type="password" bind:value={password} placeholder="Ingrese su contraseña" required />
        </div>
      </div>

      <button type="submit" class="btn-login" disabled={loading}>
        {#if loading}
          <i class="bi bi-arrow-repeat spin"></i> Ingresando...
        {:else}
          <i class="bi bi-box-arrow-in-right"></i> Ingresar
        {/if}
      </button>
    </form>

    <div class="login-footer">
      © 2026 Universidad Técnica Estatal de Quevedo
    </div>
  </div>
</div>

<style>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--negro) 0%, var(--verde) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 20px;
  padding: 40px 36px 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.login-logo { height: 70px; margin-bottom: 12px; }
.login-header h1 {
  font-size: 2rem;
  font-weight: 900;
  color: var(--verde);
  line-height: 1;
}
.login-header p {
  font-size: .8rem;
  color: var(--gris);
  font-weight: 600;
  margin-top: 4px;
}

.alert-error {
  background: #fff0f0;
  border: 1px solid #f5c2c2;
  border-radius: 8px;
  padding: 10px 14px;
  color: #c0392b;
  font-size: .83rem;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.login-form { display: flex; flex-direction: column; gap: 16px; }

.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: .8rem; font-weight: 700; color: #444; }

.input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1.5px solid var(--borde);
  border-radius: 10px;
  padding: 0 14px;
  transition: border-color .2s;
}
.input-wrap:focus-within { border-color: var(--verde); }
.input-wrap i { color: var(--gris); font-size: .95rem; }
.input-wrap input {
  flex: 1;
  border: none;
  outline: none;
  padding: 11px 0;
  font-size: .9rem;
  font-family: inherit;
  background: transparent;
}

.btn-login {
  background: var(--verde);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 13px;
  font-size: .95rem;
  font-weight: 800;
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background .2s, transform .15s;
}
.btn-login:hover:not(:disabled) { background: #155e04; transform: translateY(-1px); }
.btn-login:disabled { opacity: .7; cursor: not-allowed; }

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: .72rem;
  color: var(--gris);
  font-weight: 600;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }
</style>
