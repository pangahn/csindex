<template>
  <div class="app-container">
    <header class="app-header">
      <h1>指数成分分析</h1>
    </header>
    <main>
      <router-view/>
    </main>
    <footer class="app-footer">
      <p>© 2025 指数成分分析工具</p>
    </footer>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  background-color: #f5f7fa;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #409EFF;
  color: white;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

main {
  flex: 1;
  padding: 1rem;
}

.app-footer {
  background-color: #f5f7fa;
  color: #909399;
  text-align: center;
  padding: 1rem;
  border-top: 1px solid #e4e7ed;
}
</style>