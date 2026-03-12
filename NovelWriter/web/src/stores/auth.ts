import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '@/api/client';

interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('auth_token'));
  const userInfo = localStorage.getItem('user_info');
  const user = ref<User | null>(userInfo ? JSON.parse(userInfo) : null);

  // Computed
  const isLoggedIn = computed(() => !!token.value && !!user.value);

  // Actions
  async function login(email: string, password: string): Promise<User | null> {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      
      if (response.data.access_token) {
        token.value = response.data.access_token;
        user.value = response.data.user;
        
        localStorage.setItem('auth_token', response.data.access_token);
        localStorage.setItem('user_info', JSON.stringify(response.data.user));
        
        return response.data.user;
      }
      return null;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async function register(email: string, password: string, name: string): Promise<User | null> {
    try {
      const response = await apiClient.post('/auth/register', { email, password, name });
      
      if (response.data.access_token) {
        token.value = response.data.access_token;
        user.value = response.data.user;
        
        localStorage.setItem('auth_token', response.data.access_token);
        localStorage.setItem('user_info', JSON.stringify(response.data.user));
        
        return response.data.user;
      }
      return null;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  function logout(): void {
    token.value = null;
    user.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  function loadFromStorage(): void {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user_info');
    
    if (storedToken && storedUser) {
      token.value = storedToken;
      user.value = JSON.parse(storedUser);
    }
  }

  return {
    // State
    token,
    user,
    // Computed
    isLoggedIn,
    // Actions
    login,
    register,
    logout,
    loadFromStorage,
  };
});
