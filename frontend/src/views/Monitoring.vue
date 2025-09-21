<template>
  <div class="monitoring-page">
    <div class="page-header">
      <h1>监控检测</h1>
      <p>实时监控节点状态和性能</p>
    </div>
    
    <div class="content">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>节点状态监控</span>
                <el-button type="primary" @click="startMonitoring">
                  <el-icon><VideoPlay /></el-icon>
                  开始监控
                </el-button>
              </div>
            </template>
            
            <el-table :data="monitoringData" stripe>
              <el-table-column prop="name" label="节点名称" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status)">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="latency" label="延迟" width="100">
                <template #default="{ row }">
                  <span v-if="row.latency">{{ row.latency }}ms</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="speed" label="速度" width="120">
                <template #default="{ row }">
                  <span v-if="row.speed">{{ row.speed }}Mbps</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="lastCheck" label="最后检测" width="180" />
            </el-table>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="8">
          <el-card>
            <template #header>
              <span>监控统计</span>
            </template>
            
            <div class="stats">
              <div class="stat-item">
                <div class="stat-label">总节点数</div>
                <div class="stat-value">{{ totalNodes }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">在线节点</div>
                <div class="stat-value success">{{ onlineNodes }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">离线节点</div>
                <div class="stat-value warning">{{ offlineNodes }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">平均延迟</div>
                <div class="stat-value">{{ averageLatency }}ms</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const monitoringData = ref([])
const loading = ref(false)

const loadMonitoringData = async () => {
  try {
    loading.value = true
    // 获取节点列表
    const response = await api.get('/api/nodes/', {
      params: {
        page: 1,
        pageSize: 1000
      }
    })
    monitoringData.value = (response.data.data || []).map(node => ({
      id: node.id,
      name: node.name,
      status: node.status,
      latency: node.ping_latency,
      speed: node.speed_test,
      lastCheck: node.last_check
    }))
  } catch (error) {
    ElMessage.error('加载监控数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMonitoringData()
})

const totalNodes = computed(() => monitoringData.value.length)
const onlineNodes = computed(() => monitoringData.value.filter(node => node.status === 'active').length)
const offlineNodes = computed(() => monitoringData.value.filter(node => node.status === 'inactive').length)
const averageLatency = computed(() => {
  const activeNodes = monitoringData.value.filter(node => node.latency)
  if (activeNodes.length === 0) return 0
  const total = activeNodes.reduce((sum, node) => sum + node.latency, 0)
  return Math.round(total / activeNodes.length)
})

const getStatusTag = (status) => {
  const statusMap = {
    active: 'success',
    inactive: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '在线',
    inactive: '离线',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const startMonitoring = async () => {
  try {
    loading.value = true
    // 获取所有节点ID
    const nodeIds = monitoringData.value.map(node => node.id)
    
    if (nodeIds.length === 0) {
      ElMessage.warning('没有节点可检测')
      return
    }
    
    // 调用节点检测API
    const response = await api.post('/api/monitoring/check', {
      node_ids: nodeIds,
      force_check: true
    })
    
    // 重新加载监控数据
    await loadMonitoringData()
    
    ElMessage.success('监控检测完成')
  } catch (error) {
    ElMessage.error('监控检测失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.monitoring-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.warning {
  color: #e6a23c;
}
</style>