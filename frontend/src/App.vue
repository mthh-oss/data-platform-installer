<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <strong>Data Platform Installer</strong>
        <span>选配置 → Compose 一键部署 → 健康监控</span>
      </div>
      <nav class="nav">
        <router-link to="/">配置向导</router-link>
        <router-link to="/jobs">部署任务</router-link>
        <router-link to="/monitor">监控看板</router-link>
      </nav>
    </header>
    <router-view />
  </div>
</template>
