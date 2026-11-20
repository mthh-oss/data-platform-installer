<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <strong>Data Platform Installer</strong>
        <span>挑选组件 → 一键下载启动 → 健康监控</span>
      </div>
      <nav class="nav">
        <router-link to="/">一键启动</router-link>
        <router-link to="/jobs">下载/启动进度</router-link>
        <router-link to="/monitor">监控看板</router-link>
      </nav>
    </header>
    <router-view />
  </div>
</template>
