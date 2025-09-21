import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // 方法
  const login = async (credentials) => {
    try {
      loading.value = true
      const response = await api.post('/auth/login-json', credentials)
      
      if (response.data.access_token) {
        token.value = response.data.access_token
        localStorage.setItem('token', token.value)
        
        // 获取用户信息
        await getUserInfo()
        
        ElMessage.success('登录成功')
        return true
      }
    } catch (error) {
      const message = error.response?.data?.detail || '登录失败'
      ElMessage.error(message)
      return false
    } finally {
      loading.value = false
    }
  }

  const register = async (userData) => {
    try {
      loading.value = true
      await api.post('/auth/register', userData)
      ElMessage.success('注册成功，请登录')
      return true
    } catch (error) {
      const message = error.response?.data?.detail || '注册失败'
      ElMessage.error(message)
      return false
    } finally {
      loading.value = false
    }
  }

  const getUserInfo = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return user.value
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    }
  }

  const logout = async () => {
    try {
      // 清除本地存储
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      
      // 清除API默认header
      delete api.defaults.headers.common['Authorization']
      
      ElMessage.success('已退出登录')
    } catch (error) {
      console.error('退出登录失败:', error)
    }
  }

  const updateProfile = async (profileData) => {
    try {
      loading.value = true
      const response = await api.put('/auth/me', profileData)
      user.value = response.data
      ElMessage.success('资料更新成功')
      return true
    } catch (error) {
      const message = error.response?.data?.detail || '更新失败'
      ElMessage.error(message)
      return false
    } finally {
      loading.value = false
    }
  }

  // 初始化
  const init = async () => {
    if (token.value) {
      // 设置API默认header
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      // 获取用户信息
      await getUserInfo()
    }
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    login,
    register,
    getUserInfo,
    logout,
    updateProfile,
    init
  }
})