<template>
  <div class="dashboard">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    
    <!-- 错误状态 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      class="error-alert"
    />
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row" v-if="!loading && !error">
      <el-col :xs="24" :sm="12" :md="8" :lg="4" v-for="stat in stats" :key="stat.key">
        <div 
          class="stat-card" 
          :class="[stat.class, { 'clickable': stat.clickable }]"
          @click="stat.clickable ? handleStatClick(stat.key) : null"
        >
          <div class="stat-icon">
            <el-icon :size="28">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    
    <!-- 节点状态监控 -->
    <el-row :gutter="20" class="monitoring-row">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>节点状态监控</h3>
            <div class="monitoring-controls">
              <el-button type="text" @click="loadMonitoringData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button type="primary" @click="startMonitoring" :loading="monitoringLoading">
                <el-icon><VideoPlay /></el-icon>
                开始检测
              </el-button>
            </div>
          </div>
          <div class="monitoring-table">
            <el-table :data="monitoringData" stripe max-height="500">
              <el-table-column prop="name" label="节点名称" min-width="150" />
              <el-table-column prop="node_type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getNodeTypeTag(row.node_type)">
                    {{ row.node_type?.toUpperCase() || 'UNKNOWN' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="address" label="地址" min-width="120" />
              <el-table-column prop="port" label="端口" width="80" />
              <el-table-column prop="country" label="国家" width="80" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status)">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="latency" label="延迟" width="100">
                <template #default="{ row }">
                  <span v-if="row.latency">{{ Math.round(row.latency) }}ms</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="lastCheck" label="最后检测" width="180">
                <template #default="{ row }">
                  {{ formatTime(row.lastCheck) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { useNodesStore } from '@/stores/nodes'
import api from '@/utils/api'

const nodesStore = useNodesStore()

// 响应式数据
const loading = ref(false)
const error = ref('')
const monitoringLoading = ref(false)
const monitoringData = ref([])
const allNodesData = ref([]) // 存储所有节点数据用于统计

// 统计数据
const stats = computed(() => {
  // 获取所有节点数据，不仅仅是活跃节点
  const allNodes = allNodesData.value || []
  const total = allNodes.length
  const active = allNodes.filter(node => node.status === 'active').length
  const inactive = allNodes.filter(node => node.status === 'inactive').length
  const error = allNodes.filter(node => node.status === 'error').length
  const disabled = allNodes.filter(node => node.status === 'disabled').length
  const unknown = allNodes.filter(node => node.status === 'unknown').length
  
  return [
    {
      key: 'total',
      label: '总节点数',
      value: total,
      icon: 'Grid',
      class: 'stat-primary',
      clickable: total > 0
    },
    {
      key: 'active',
      label: '活跃节点',
      value: active,
      icon: 'Check',
      class: 'stat-success',
      clickable: active > 0
    },
    {
      key: 'inactive',
      label: '离线节点',
      value: inactive,
      icon: 'Close',
      class: 'stat-warning',
      clickable: inactive > 0
    },
    {
      key: 'error',
      label: '错误节点',
      value: error,
      icon: 'Warning',
      class: 'stat-danger',
      clickable: error > 0
    },
    {
      key: 'disabled',
      label: '禁用节点',
      value: disabled,
      icon: 'Lock',
      class: 'stat-info',
      clickable: disabled > 0
    },
    {
      key: 'unknown',
      label: '未知节点',
      value: unknown,
      icon: 'QuestionFilled',
      class: 'stat-default',
      clickable: unknown > 0
    }
  ]
})


// 方法
const refreshData = async () => {
  try {
    loading.value = true
    await nodesStore.fetchNodes()
    await loadMonitoringData()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

// 加载监控数据
const loadMonitoringData = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await api.get('/api/nodes/', {
      params: {
        page: 1,
        pageSize: 1000
      }
    })
    
    if (!response.data || !response.data.data) {
      throw new Error('数据格式错误')
    }
    
    // 保存所有节点数据用于统计
    allNodesData.value = response.data.data || []
    
    // 只显示活跃节点用于监控表格
    const activeNodes = allNodesData.value.filter(node => node.status === 'active')
    
    monitoringData.value = activeNodes.map(node => ({
      id: node.id,
      name: node.name,
      node_type: node.node_type,
      address: node.address,
      port: node.port,
      country: node.country,
      status: node.status,
      latency: node.ping_latency,
      lastCheck: node.last_check
    }))
  } catch (err) {
    console.error('加载监控数据失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载监控数据失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 开始监控检测
const startMonitoring = async () => {
  try {
    monitoringLoading.value = true
    const nodeIds = monitoringData.value.map(node => node.id)
    await api.post('/api/monitoring/check', {
      node_ids: nodeIds,
      force_check: true
    })
    
    // 重新加载监控数据
    await loadMonitoringData()
    ElMessage.success('节点检测完成')
  } catch (error) {
    ElMessage.error('节点检测失败')
  } finally {
    monitoringLoading.value = false
  }
}

// 处理统计卡片点击
const handleStatClick = (statKey) => {
  // 跳转到节点管理页面并设置过滤条件
  const router = useRouter()
  router.push({
    path: '/nodes',
    query: {
      status: statKey === 'total' ? '' : statKey
    }
  })
}

// 状态标签和文本
const getStatusTag = (status) => {
  const statusMap = {
    active: 'success',
    inactive: 'warning',
    error: 'danger',
    unknown: 'info',
    disabled: 'info'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '在线',
    inactive: '离线',
    error: '错误',
    unknown: '未知',
    disabled: '禁用'
  }
  return statusMap[status] || '未知'
}

const getNodeTypeTag = (type) => {
  const typeMap = {
    v2ray: 'primary',
    trojan: 'success',
    ss: 'warning',
    ssr: 'info'
  }
  return typeMap[type] || 'default'
}

const formatTime = (time) => {
  if (!time) return '从未检测'
  
  try {
    const date = new Date(time)
    // 转换为北京时间显示
    const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    return beijingTime.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } catch (error) {
    return '时间格式错误'
  }
}

// 生命周期
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-primary .stat-icon {
  background: #e3f2fd;
  color: #1976d2;
}

.stat-success .stat-icon {
  background: #e8f5e8;
  color: #4caf50;
}

.stat-warning .stat-icon {
  background: #fff3e0;
  color: #ff9800;
}

.stat-danger .stat-icon {
  background: #ffebee;
  color: #f44336;
}

.stat-info .stat-icon {
  background: #f5f5f5;
  color: #909399;
}

.stat-default .stat-icon {
  background: #fafafa;
  color: #dcdfe6;
}

/* 加载和错误状态样式 */
.loading-container {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.error-alert {
  margin-bottom: 20px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-card.clickable {
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.monitoring-row {
  margin-bottom: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}


.monitoring-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.monitoring-table {
  padding: 0;
}


/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 15px;
  }
  
  .stat-card {
    padding: 15px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
  }
  
  .stat-number {
    font-size: 20px;
  }
}
</style>