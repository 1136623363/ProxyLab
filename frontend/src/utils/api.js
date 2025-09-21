import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    
    // 记录请求时间
    config.metadata = { startTime: new Date() }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 记录响应时间
    if (response.config.metadata) {
      const endTime = new Date()
      const duration = endTime - response.config.metadata.startTime
      console.log(`API请求 ${response.config.url} 耗时: ${duration}ms`)
    }
    
    return response
  },
  (error) => {
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转登录页
          const userStore = useUserStore()
          userStore.logout()
          ElMessage.error('登录已过期，请重新登录')
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 422:
          // 数据验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errors = data.detail.map(err => err.msg).join(', ')
            ElMessage.error(errors)
          } else {
            ElMessage.error('数据验证失败')
          }
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          ElMessage.error(data?.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// 导出API实例
export default api

// 导出常用的HTTP方法
export const get = (url, config = {}) => api.get(url, config)
export const post = (url, data = {}, config = {}) => api.post(url, data, config)
export const put = (url, data = {}, config = {}) => api.put(url, data, config)
export const del = (url, config = {}) => api.delete(url, config)
export const patch = (url, data = {}, config = {}) => api.patch(url, data, config)