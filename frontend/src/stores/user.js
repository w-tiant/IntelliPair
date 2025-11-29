
import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'

export const useUserStore = defineStore('user', () => {
  // --- State ---
  const currentUser = ref(null);
  const usernameInput = ref('');
  const passwordInput = ref('');
  const API_URL = '/api';

  // --- Actions ---
  async function login() {
    if (!usernameInput.value.trim() || !passwordInput.value.trim()) {
      alert("请输入用户名和密码。"); 
      return;
    }
    try {
      const response = await fetch(`${API_URL}/users/login`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: usernameInput.value.trim(),
            password: passwordInput.value.trim()
        })
      });
      const data = await response.json();
      if (response.ok) {
        currentUser.value = data.username;
        localStorage.setItem('food-app-user', data.username);
        usernameInput.value = ''; 
        passwordInput.value = '';
      } else {
        throw new Error(data.detail);
      }
    } catch (e) {
      alert(`登录/注册失败: ${e.message}`);
    }
  }
  

  function logout() {
    currentUser.value = null;
    localStorage.removeItem('food-app-user');
  }

  // --- Lifecycle Hook ---
  // 当 store 被创建时，尝试从 localStorage 恢复用户状态
  onMounted(() => {
    const savedUser = localStorage.getItem('food-app-user');
    if (savedUser) {
      currentUser.value = savedUser;
    }
  });

  return {
    currentUser,
    usernameInput,
    passwordInput,
    login,
    logout,
  }
})