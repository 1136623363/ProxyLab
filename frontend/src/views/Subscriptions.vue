<template>
  <div class="subscriptions-page">
    <div class="page-header">
      <h1>订阅管理</h1>
      <p>管理订阅源和自动更新</p>
    </div>
    
    <div class="content">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>订阅源列表</span>
            <el-button type="primary" @click="addSubscription">
              <el-icon><Plus /></el-icon>
              添加订阅
            </el-button>
          </div>
        </template>
        
        <el-table :data="subscriptions" stripe>
          <el-table-column prop="name" label="订阅名称" />
          <el-table-column prop="url" label="订阅地址" />
          <el-table-column prop="nodeCount" label="节点数量" width="100" />
          <el-table-column prop="lastUpdate" label="最后更新" width="180">
            <template #default="{ row }">
              {{ formatTime(row.lastUpdate) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'warning'">
                {{ row.status === 'active' ? '活跃' : '暂停' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280">
            <template #default="{ row }">
              <el-button size="small" @click="editSubscription(row)">编辑</el-button>
              <el-button 
                size="small" 
                :type="row.status === 'active' ? 'warning' : 'success'"
                @click="toggleSubscription(row)"
              >
                {{ row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" type="info" @click="updateSubscription(row)">更新</el-button>
              <el-button size="small" type="danger" @click="deleteSubscription(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    
    <!-- 添加订阅对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加订阅"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addRules"
        label-width="100px"
      >
        <el-form-item 
          label="订阅名称" 
          prop="notes"
          :required="addForm.input_type === 'url'"
        >
          <el-input 
            v-model="addForm.notes" 
            :placeholder="addForm.input_type === 'url' ? '请输入订阅名称' : '可选，留空将自动生成名称'"
          />
        </el-form-item>
        
        <el-form-item label="订阅类型" prop="input_type">
          <el-radio-group v-model="addForm.input_type" @change="handleInputTypeChange">
            <el-radio value="url">URL订阅</el-radio>
            <el-radio value="yaml">YAML文件</el-radio>
            <el-radio value="text">粘贴文本</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- URL订阅 -->
        <el-form-item label="订阅地址" prop="source_url" v-if="addForm.input_type === 'url'">
          <el-input v-model="addForm.source_url" placeholder="请输入订阅URL" />
        </el-form-item>
        
        <!-- 文件上传 -->
        <el-form-item label="选择文件" prop="file" v-if="addForm.input_type === 'yaml'">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            :show-file-list="true"
            :limit="1"
            accept=".yaml,.yml,.json,.txt"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 YAML、JSON、TXT 格式文件，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <!-- 文本输入 -->
        <el-form-item label="订阅内容" prop="content" v-if="addForm.input_type === 'text'">
          <el-input 
            v-model="addForm.content" 
            type="textarea" 
            :rows="10"
            placeholder="请粘贴订阅内容（支持 YAML、JSON、原始链接等格式）" 
          />
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
    
    <!-- 编辑订阅对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑订阅"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="订阅名称" prop="notes">
          <el-input v-model="editForm.notes" placeholder="请输入订阅名称" />
        </el-form-item>
        
        <el-form-item label="订阅地址" prop="source_url">
          <el-input v-model="editForm.source_url" placeholder="请输入订阅URL" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const subscriptions = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const addFormRef = ref()
const editFormRef = ref()
const uploadRef = ref()

const addForm = ref({
  source_url: '',
  input_type: 'url',
  content: '',
  notes: '',
  file: null
})

const editForm = ref({
  id: null,
  name: '',
  source_url: '',
  input_type: 'url',
  notes: ''
})

const addRules = {
  input_type: [
    { required: true, message: '请选择订阅类型', trigger: 'change' }
  ],
  source_url: [
    { required: true, message: '请输入订阅地址', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入订阅内容', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择文件', trigger: 'change' }
  ],
  notes: [
    { 
      required: false, 
      message: '请输入订阅名称', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        // 只有URL类型时才需要验证订阅名称
        if (addForm.value.input_type === 'url' && !value) {
          callback(new Error('请输入订阅名称'))
        } else {
          callback()
        }
      }
    }
  ]
}

const editRules = {
  notes: [
    { required: true, message: '请输入订阅名称', trigger: 'blur' }
  ],
  source_url: [
    { required: true, message: '请输入订阅地址', trigger: 'blur' }
  ]
}

// 格式化时间显示
const formatTime = (timeStr) => {
  if (!timeStr) return '从未更新'
  
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

const loadSubscriptions = async () => {
  try {
    loading.value = true
    const response = await api.get('/api/input/')
    // 只显示URL类型的订阅
    subscriptions.value = response.data
      .filter(record => record.input_type === 'url')
      .map(record => ({
        id: record.id,
        name: record.notes || '未命名订阅',
        url: record.source_url,
        nodeCount: record.node_count || 0, // 使用实际的节点数量
        lastUpdate: record.last_refresh || record.updated_at,
        status: record.is_active ? 'active' : 'inactive',
        input_type: record.input_type,
        notes: record.notes
      }))
  } catch (error) {
    ElMessage.error('加载订阅列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSubscriptions()
})

const addSubscription = () => {
  showAddDialog.value = true
  addForm.value = {
    source_url: '',
    input_type: 'url',
    content: '',
    notes: '',
    file: null
  }
  // 清空上传组件
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 处理输入类型变化
const handleInputTypeChange = (value) => {
  // 清空相关字段
  addForm.value.source_url = ''
  addForm.value.content = ''
  addForm.value.file = null
  
  // 非URL类型时清空订阅名称，让后端自动生成
  if (value !== 'url') {
    addForm.value.notes = ''
  }
  
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 文件上传前验证
const beforeUpload = (file) => {
  const isValidType = ['yaml', 'yml', 'json', 'txt'].some(ext => 
    file.name.toLowerCase().endsWith(`.${ext}`)
  )
  
  if (!isValidType) {
    ElMessage.error('只支持 YAML、JSON、TXT 格式文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }
  
  return false // 阻止自动上传
}

// 文件选择变化
const handleFileChange = (file) => {
  addForm.value.file = file.raw
  
  // 读取文件内容
  const reader = new FileReader()
  reader.onload = (e) => {
    addForm.value.content = e.target.result
  }
  reader.readAsText(file.raw, 'UTF-8')
}

const handleAddSubmit = async () => {
  if (!addFormRef.value) return
  
  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        
        // 根据输入类型准备数据
        const submitData = {
          input_type: addForm.value.input_type
        }
        
        if (addForm.value.input_type === 'url') {
          submitData.source_url = addForm.value.source_url
          // URL类型时才发送订阅名称
          if (addForm.value.notes) {
            submitData.notes = addForm.value.notes
          }
        } else {
          submitData.content = addForm.value.content
          // 非URL类型时不发送notes，让后端自动生成名称
        }
        
        await api.post('/api/input/', submitData)
        ElMessage.success('订阅添加成功')
        showAddDialog.value = false
        await loadSubscriptions()
      } catch (error) {
        ElMessage.error('添加失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleEditSubmit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        loading.value = true
        await api.put(`/api/input/${editForm.value.id}`, {
          source_url: editForm.value.source_url,
          input_type: editForm.value.input_type,
          notes: editForm.value.notes
        })
        ElMessage.success('订阅更新成功')
        showEditDialog.value = false
        await loadSubscriptions()
      } catch (error) {
        ElMessage.error('更新失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const editSubscription = (row) => {
  showEditDialog.value = true
  editForm.value = {
    id: row.id,
    name: row.name || '',
    source_url: row.source_url || '',
    input_type: row.input_type || 'url',
    notes: row.notes || ''
  }
}

const updateSubscription = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要更新订阅 "${row.name || row.source_url}" 吗？`,
      '确认更新',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用刷新API
    const response = await api.post(`/api/input/${row.id}/refresh`)
    ElMessage.success('订阅更新成功')
    
    // 刷新列表
    await loadSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('更新失败')
    }
  }
}

const toggleSubscription = async (row) => {
  try {
    const action = row.status === 'active' ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}订阅 "${row.name || row.source_url}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用切换状态API
    const newStatus = row.status === 'active' ? 'inactive' : 'active'
    await api.put(`/api/input/${row.id}`, {
      is_active: newStatus === 'active'
    })
    
    ElMessage.success(`订阅${action}成功`)
    
    // 刷新列表
    await loadSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${row.status === 'active' ? '禁用' : '启用'}失败`)
    }
  }
}

const deleteSubscription = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除订阅 "${row.name || row.source_url}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/api/input/${row.id}`)
    ElMessage.success('订阅删除成功')
    
    // 刷新列表
    await loadSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.subscriptions-page {
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
</style>