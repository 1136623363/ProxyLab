<template>
  <div class="nodes-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>节点管理</h1>
        <p>管理和监控所有的节点</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="addNode">
          <el-icon><Plus /></el-icon>
          添加节点
        </el-button>
        <el-button @click="refreshNodes">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 筛选器 -->
    <div class="filters">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-select v-model="filters.country" placeholder="按国家筛选" clearable>
            <el-option 
              v-for="country in availableCountries" 
              :key="country" 
              :label="country" 
              :value="country" 
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select v-model="filters.nodeType" placeholder="节点类型" clearable>
            <el-option label="V2Ray" value="v2ray" />
            <el-option label="Trojan" value="trojan" />
            <el-option label="Shadowsocks" value="ss" />
            <el-option label="ShadowsocksR" value="ssr" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select v-model="filters.status" placeholder="节点状态" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="离线" value="inactive" />
            <el-option label="错误" value="error" />
            <el-option label="未知" value="unknown" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="primary" @click="applyFilters">应用筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 节点列表 -->
    <div class="nodes-table">
      <!-- 批量操作工具栏 -->
      <div class="batch-actions" v-if="selectedNodes.length > 0">
        <el-alert
          :title="`已选择 ${selectedNodes.length} 个节点`"
          type="info"
          show-icon
          :closable="false"
        >
          <template #default>
            <div class="batch-buttons">
              <el-button 
                type="warning" 
                size="small" 
                @click="batchDisableNodes"
                :loading="batchLoading"
              >
                批量禁用
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click="batchEnableNodes"
                :loading="batchLoading"
              >
                批量启用
              </el-button>
              <el-button 
                size="small" 
                @click="clearSelection"
              >
                取消选择
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>
      
      <el-table
        :data="nodesStore.filteredNodes"
        :loading="nodesStore.loading"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="节点名称" min-width="150" />
        <el-table-column prop="node_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getNodeTypeTag(row.node_type)">
              {{ row.node_type.toUpperCase() }}
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
        <el-table-column prop="ping_latency" label="延迟" width="100">
          <template #default="{ row }">
            <span v-if="row.ping_latency">{{ Math.round(row.ping_latency) }}ms</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_check" label="最后检测" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_check) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editNode(row)">编辑</el-button>
            <el-button 
              size="small" 
              :type="row.status === 'disabled' ? 'success' : 'warning'"
              @click="toggleNodeStatus(row)"
            >
              {{ row.status === 'disabled' ? '启用' : '禁用' }}
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="checkNode(row)"
              :disabled="row.status === 'disabled'"
            >
              检测
            </el-button>
            <el-button size="small" type="danger" @click="deleteNode(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页控件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- 添加节点对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加节点"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addRules"
        label-width="100px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        
        <el-form-item label="节点类型" prop="node_type">
          <el-select v-model="addForm.node_type" placeholder="请选择节点类型">
            <el-option label="V2Ray" value="v2ray" />
            <el-option label="Trojan" value="trojan" />
            <el-option label="Shadowsocks" value="ss" />
            <el-option label="ShadowsocksR" value="ssr" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="服务器地址" prop="address">
          <el-input v-model="addForm.address" placeholder="请输入服务器地址" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="addForm.port" :min="1" :max="65535" placeholder="请输入端口" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" placeholder="请输入密码" show-password />
        </el-form-item>
        
        <el-form-item label="加密方式" prop="encryption">
          <el-input v-model="addForm.encryption" placeholder="请输入加密方式" />
        </el-form-item>
        
        <el-form-item label="UUID" prop="uuid" v-if="addForm.node_type === 'v2ray'">
          <el-input v-model="addForm.uuid" placeholder="请输入UUID" />
        </el-form-item>
        
        <el-form-item label="国家" prop="country">
          <el-input v-model="addForm.country" placeholder="请输入国家" />
        </el-form-item>
        
        <el-form-item label="地区" prop="region">
          <el-input v-model="addForm.region" placeholder="请输入地区" />
        </el-form-item>
        
        <el-form-item label="备注" prop="notes">
          <el-input v-model="addForm.notes" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleAddSubmit"
        >
          添加
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑节点对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑节点"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        
        <el-form-item label="国家" prop="country">
          <el-input v-model="editForm.country" placeholder="请输入国家" />
        </el-form-item>
        
        <el-form-item label="地区" prop="region">
          <el-input v-model="editForm.region" placeholder="请输入地区" />
        </el-form-item>
        
        <el-form-item label="忽略更新" prop="ignore_updates">
          <el-switch v-model="editForm.ignore_updates" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleEditSubmit"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNodesStore } from '@/stores/nodes'
import api from '@/utils/api'

const nodesStore = useNodesStore()

// 响应式数据
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const loading = ref(false)
const batchLoading = ref(false)
const selectedNodes = ref([])
const addFormRef = ref()
const editFormRef = ref()
const filters = ref({
  country: '',
  nodeType: '',
  status: ''
})

const availableCountries = ref([])

// 分页数据
const pagination = ref({
  page: 1,
  pageSize: 100,
  total: 0
})

const addForm = ref({
  name: '',
  node_type: 'v2ray',
  address: '',
  port: 443,
  password: '',
  encryption: '',
  uuid: '',
  country: '',
  region: '',
  notes: ''
})

const editForm = ref({
  id: null,
  name: '',
  country: '',
  region: '',
  ignore_updates: false
})

const addRules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 1, max: 100, message: '节点名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  node_type: [
    { required: true, message: '请选择节点类型', trigger: 'change' }
  ],
  address: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ]
}

const editRules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 1, max: 100, message: '节点名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 方法
const refreshNodes = async () => {
  try {
    loading.value = true
    await loadNodes()
    ElMessage.success('节点列表刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const loadNodes = async () => {
  try {
    loading.value = true
    const response = await api.get('/api/nodes/', {
      params: {
        page: pagination.value.page,
        pageSize: pagination.value.pageSize,
        node_type: filters.value.nodeType,
        country: filters.value.country,
        status: filters.value.status
      }
    })
    
    // 更新store中的节点数据
    nodesStore.nodes = response.data.data || []
    
    // 更新分页信息
    pagination.value.total = response.data.total || 0
    
    // 如果当前页没有数据且不是第一页，回到第一页
    if ((!response.data.data || response.data.data.length === 0) && pagination.value.page > 1) {
      pagination.value.page = 1
      await loadNodes()
    }
  } catch (error) {
    ElMessage.error('加载节点列表失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  pagination.value.pageSize = val
  pagination.value.page = 1
  loadNodes()
}

const handleCurrentChange = (val) => {
  pagination.value.page = val
  loadNodes()
}

const loadCountries = async () => {
  try {
    const response = await api.get('/api/nodes/countries/list')
    availableCountries.value = response.data
  } catch (error) {
    console.error('加载国家列表失败:', error)
  }
}

const applyFilters = () => {
  pagination.value.page = 1  // 重置到第一页
  loadNodes()
}

const resetFilters = () => {
  filters.value = {
    country: '',
    nodeType: '',
    status: ''
  }
  pagination.value.page = 1  // 重置到第一页
  loadNodes()
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
    active: '活跃',
    inactive: '离线',
    error: '错误',
    unknown: '未知',
    disabled: '禁用'
  }
  return statusMap[status] || '未知'
}

// 格式化时间显示
const formatTime = (timeStr) => {
  if (!timeStr) return '从未检测'
  
  try {
    const date = new Date(timeStr)
    // 转换为北京时间显示
    const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
    return beijingTime.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  } catch (error) {
    return '时间格式错误'
  }
}


const addNode = () => {
  showAddDialog.value = true
  addForm.value = {
    name: '',
    node_type: 'v2ray',
    address: '',
    port: 443,
    password: '',
    encryption: '',
    uuid: '',
    country: '',
    region: '',
    notes: ''
  }
}

const handleAddSubmit = async () => {
  if (!addFormRef.value) return
  
  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        await nodesStore.addNode(addForm.value)
        showAddDialog.value = false
        ElMessage.success('节点添加成功')
        // 刷新节点列表
        await loadNodes()
      } catch (error) {
        ElMessage.error('添加失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const editNode = (node) => {
  showEditDialog.value = true
  editForm.value = {
    id: node.id,
    name: node.name,
    country: node.country || '',
    region: node.region || '',
    ignore_updates: node.ignore_updates || false
  }
}

const handleEditSubmit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        await nodesStore.updateNode(editForm.value.id, {
          name: editForm.value.name,
          country: editForm.value.country,
          region: editForm.value.region,
          ignore_updates: editForm.value.ignore_updates
        })
        showEditDialog.value = false
        ElMessage.success('节点更新成功')
        // 刷新节点列表
        await loadNodes()
      } catch (error) {
        ElMessage.error('更新失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const toggleNodeStatus = async (node) => {
  try {
    const newStatus = node.status === 'disabled' ? 'unknown' : 'disabled'
    await nodesStore.updateNode(node.id, { status: newStatus })
    ElMessage.success(`节点已${newStatus === 'disabled' ? '禁用' : '启用'}`)
    // 刷新节点列表
    await loadNodes()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const checkNode = async (node) => {
  try {
    await nodesStore.checkNodes([node.id])
    ElMessage.success('节点检测完成')
    // 刷新节点列表
    await loadNodes()
  } catch (error) {
    ElMessage.error('节点检测失败')
  }
}

const deleteNode = async (node) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${node.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await nodesStore.deleteNode(node.id)
    ElMessage.success('节点删除成功')
    // 刷新节点列表
    await loadNodes()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量操作方法
const handleSelectionChange = (selection) => {
  selectedNodes.value = selection
}

const clearSelection = () => {
  selectedNodes.value = []
  // 清除表格选择
  const table = document.querySelector('.el-table')
  if (table) {
    const checkboxes = table.querySelectorAll('.el-checkbox__input')
    checkboxes.forEach(checkbox => {
      if (checkbox.checked) {
        checkbox.click()
      }
    })
  }
}

const batchDisableNodes = async () => {
  if (selectedNodes.value.length === 0) {
    ElMessage.warning('请先选择要禁用的节点')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要禁用选中的 ${selectedNodes.value.length} 个节点吗？`,
      '确认批量禁用',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    batchLoading.value = true
    const promises = selectedNodes.value.map(node => 
      nodesStore.updateNode(node.id, { status: 'disabled' })
    )
    
    await Promise.all(promises)
    ElMessage.success(`成功禁用 ${selectedNodes.value.length} 个节点`)
    
    // 刷新节点列表并清除选择
    await loadNodes()
    clearSelection()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量禁用失败')
    }
  } finally {
    batchLoading.value = false
  }
}

const batchEnableNodes = async () => {
  if (selectedNodes.value.length === 0) {
    ElMessage.warning('请先选择要启用的节点')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要启用选中的 ${selectedNodes.value.length} 个节点吗？`,
      '确认批量启用',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    batchLoading.value = true
    const promises = selectedNodes.value.map(node => 
      nodesStore.updateNode(node.id, { status: 'unknown' })
    )
    
    await Promise.all(promises)
    ElMessage.success(`成功启用 ${selectedNodes.value.length} 个节点`)
    
    // 刷新节点列表并清除选择
    await loadNodes()
    clearSelection()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量启用失败')
    }
  } finally {
    batchLoading.value = false
  }
}

// 生命周期
onMounted(async () => {
  // 从URL参数中读取状态过滤
  const route = useRoute()
  if (route.query.status) {
    filters.value.status = route.query.status
  }
  
  await loadCountries()
  await loadNodes()
})
</script>

<style scoped>
.nodes-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-left p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.filters {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.nodes-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.batch-actions {
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

.batch-buttons {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
  
  .filters {
    padding: 15px;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>