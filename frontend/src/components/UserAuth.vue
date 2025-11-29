
<template>
  <div class="user-auth-widget">
    <div v-if="user.currentUser" class="welcome-message">
      <span>欢迎，<strong>{{ user.currentUser }}</strong> ！ </span>
      <button @click="user.logout" class="logout-button">退出</button>
    </div>
    <div v-else class="login-form">
      <input 
        type="text" 
        v-model="user.usernameInput" 
        placeholder="用户名" 
      />
      <input 
        type="password" 
        v-model="user.passwordInput" 
        placeholder="密码" 
        @keyup.enter="user.login"
      />
      <button @click="user.login">进入</button>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '../stores/user';
const user = useUserStore();
</script>

<style scoped>
.user-auth-widget {
  position: fixed;
  top: 1.5rem;
  right: 2rem;
  z-index: 1001;
  
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px -8px rgba(0, 0, 0, 0.1);
  
  padding: 6px 8px;
  border-radius: 99px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.user-auth-widget:hover {
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 10px 40px -8px rgba(0, 0, 0, 0.15);
}

.login-form {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 输入框：去边框，全透明 */
.login-form input {
  box-sizing: border-box;
  height: 36px;
  border: none;
  border-radius: 99px;
  padding: 0 1rem;
  font-size: 14px;
  width: 140px;
  background-color: rgba(255,255,255,0.5);
  color: #334155;
  transition: all 0.2s;
}

.login-form input:focus {
  outline: none;
  background-color: #fff;
  box-shadow: 0 0 0 2px rgba(var(--accent-color-rgb, 20, 128, 97), 0.2);
  width: 160px;
}

/* 按钮：圆形或椭圆 */
.login-form button, .logout-button {
  height: 36px;
  padding: 0 1.2rem;
  border: none;
  border-radius: 99px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  
  /* 渐变绿 */
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  transition: all 0.2s;
}

.logout-button {
  background: linear-gradient(135deg, #5acdaa 0%, #059669 100%);
  box-shadow: 0 2px 8px rgba(100, 116, 139, 0.3);
}

.login-form button:hover, .logout-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.welcome-message {
  padding: 0 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #334155;
  font-size: 0.9rem;
}
.welcome-message strong { color: var(--accent-color); }
</style>