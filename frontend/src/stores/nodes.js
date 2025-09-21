import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export const useNodesStore = defineStore('nodes', () => {
  // 状态
  const nodes = ref([])
  const loading = ref(false)
  const total = ref(0)
  const filters = ref({
    page: 1,
    pageSize: 100,  // 增加默认分页大小以显示更多节点
    search: '',
    nodeType: '',
    country: '',
    region: '',
    status: ''
  })

  // 计算属性
  const filteredNodes = computed(() => {
    let result = nodes.value

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(node => 
        node.name.toLowerCase().includes(search) ||
        node.address.toLowerCase().includes(search)
      )
    }

    if (filters.value.nodeType) {
      result = result.filter(node => node.node_type === filters.value.nodeType)
    }

    if (filters.value.country) {
      result = result.filter(node => node.country === filters.value.country)
    }

    if (filters.value.region) {
      result = result.filter(node => node.region === filters.value.region)
    }

    if (filters.value.status) {
      result = result.filter(node => node.status === filters.value.status)
    }

    return result
  })

  const nodeStats = computed(() => {
    const stats = {
      total: nodes.value.length,
      active: 0,
      inactive: 0,
      error: 0,
      unknown: 0,
      byType: {},
      byCountry: {}
    }

    nodes.value.forEach(node => {
      // 状态统计
      stats[node.status] = (stats[node.status] || 0) + 1

      // 类型统计
      stats.byType[node.node_type] = (stats.byType[node.node_type] || 0) + 1

      // 国家统计
      if (node.country) {
        stats.byCountry[node.country] = (stats.byCountry[node.country] || 0) + 1
      }
    })

    return stats
  })

  // 方法
  const fetchNodes = async (params = {}) => {
    try {
      loading.value = true
      const response = await api.get('/api/nodes/', {
        params: { ...filters.value, ...params }
      })
      nodes.value = response.data.data || []
      total.value = response.data.total || 0
      return response.data.data || []
    } catch (error) {
      ElMessage.error('获取节点列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const getNode = async (id) => {
    try {
      const response = await api.get(`/api/nodes/${id}`)
      return response.data
    } catch (error) {
      ElMessage.error('获取节点详情失败')
      throw error
    }
  }

  const updateNode = async (id, data) => {
    try {
      const response = await api.put(`/api/nodes/${id}`, data)
      
      // 更新本地数据
      const index = nodes.value.findIndex(node => node.id === id)
      if (index !== -1) {
        nodes.value[index] = { ...nodes.value[index], ...response.data }
      }
      
      ElMessage.success('节点更新成功')
      return response.data
    } catch (error) {
      ElMessage.error('更新节点失败')
      throw error
    }
  }

  const addNode = async (nodeData) => {
    try {
      loading.value = true
      const response = await api.post('/api/nodes/', nodeData)
      
      // 添加到本地数据
      nodes.value.push(response.data)
      
      ElMessage.success('节点添加成功')
      return response.data
    } catch (error) {
      ElMessage.error('添加节点失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteNode = async (id) => {
    try {
      await api.delete(`/api/nodes/${id}`)
      
      // 从本地数据中移除
      const index = nodes.value.findIndex(node => node.id === id)
      if (index !== -1) {
        nodes.value.splice(index, 1)
      }
      
      ElMessage.success('节点删除成功')
    } catch (error) {
      ElMessage.error('删除节点失败')
      throw error
    }
  }

  const checkNodes = async (nodeIds = []) => {
    try {
      loading.value = true
      const response = await api.post('/api/monitoring/check', {
        node_ids: nodeIds,
        force_check: true
      })
      
      // 更新本地数据
      response.data.forEach(result => {
        const node = nodes.value.find(n => n.id === result.node_id)
        if (node) {
          node.status = result.status
          node.ping_latency = result.ping_latency
          node.packet_loss = result.packet_loss
          node.speed_test = result.speed_test
          node.availability = result.availability
          node.last_check = new Date().toISOString()
        }
      })
      
      ElMessage.success('节点检测完成')
      return response.data
    } catch (error) {
      ElMessage.error('节点检测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const getNodeStats = async () => {
    try {
      const response = await api.get('/api/nodes/stats/summary')
      return response.data
    } catch (error) {
      ElMessage.error('获取节点统计失败')
      throw error
    }
  }

  const getCountries = async () => {
    try {
      const response = await api.get('/api/nodes/countries/list')
      return response.data
    } catch (error) {
      ElMessage.error('获取国家列表失败')
      throw error
    }
  }

  const getRegions = async () => {
    try {
      const response = await api.get('/api/nodes/regions/list')
      return response.data
    } catch (error) {
      ElMessage.error('获取地区列表失败')
      throw error
    }
  }

  const setFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const resetFilters = () => {
    filters.value = {
      page: 1,
      pageSize: 20,
      search: '',
      nodeType: '',
      country: '',
      region: '',
      status: ''
    }
  }

  return {
    nodes,
    loading,
    total,
    filters,
    filteredNodes,
    nodeStats,
    fetchNodes,
    getNode,
    addNode,
    updateNode,
    deleteNode,
    checkNodes,
    getNodeStats,
    getCountries,
    getRegions,
    setFilters,
    resetFilters
  }
})