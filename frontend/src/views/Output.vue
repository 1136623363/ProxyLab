<template>
  <div class="output-page">
    <div class="page-header">
      <h1>输出配置</h1>
      <p>生成和导出各种格式的配置文件</p>
    </div>
    
    <div class="content">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <span>配置选项</span>
            </template>
            
            <el-form :model="configForm" label-width="100px">
              <el-form-item label="输出格式">
                <el-select v-model="configForm.format" placeholder="选择输出格式">
                  <el-option 
                    v-for="format in availableFormats" 
                    :key="format.value" 
                    :label="format.label" 
                    :value="format.value" 
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="generateConfig" :loading="loading">
                  生成配置
                </el-button>
                <el-button @click="resetForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>生成的配置</span>
                <div>
                  <el-button type="primary" @click="copyConfig" :disabled="!generatedConfig">
                    复制配置
                  </el-button>
                </div>
              </div>
            </template>
            
            <div v-if="shortUrl" class="config-url-section">
              <el-form-item label="订阅链接">
                <el-input
                  v-model="shortUrl"
                  readonly
                  placeholder="订阅链接将显示在这里"
                >
                  <template #append>
                    <el-button @click="copyShortUrl">复制</el-button>
                  </template>
                </el-input>
              </el-form-item>
            </div>
            
            <el-input
              v-model="generatedConfig"
              type="textarea"
              :rows="12"
              placeholder="生成的配置将显示在这里"
              readonly
            />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const configForm = ref({
  format: 'clash'
})

const generatedConfig = ref('')
const configUrl = ref('')
const shortUrl = ref('')
const loading = ref(false)
const availableFormats = ref([])

const loadFormats = async () => {
  try {
    const response = await api.get('/api/output/formats')
    availableFormats.value = response.data.formats
  } catch (error) {
    ElMessage.error('加载格式列表失败')
  }
}

onMounted(() => {
  loadFormats()
})

const generateConfig = async () => {
  try {
    loading.value = true
    
    // 获取当前用户ID
    const userResponse = await api.get('/auth/me')
    const userId = userResponse.data.id
    
    // 构建订阅链接
    const baseUrl = window.location.origin.replace('3000', '8001')
    let subscriptionUrl
    
    if (configForm.value.format === 'universal') {
      // 万能订阅链接 - 自动检测客户端类型
      subscriptionUrl = `${baseUrl}/api/output/subscription?user_id=${userId}`
    } else {
      // 指定格式的订阅链接
      subscriptionUrl = `${baseUrl}/api/output/subscription/${configForm.value.format}?user_id=${userId}`
    }
    
    // 获取订阅内容
    const response = await fetch(subscriptionUrl)
    if (!response.ok) {
      throw new Error('获取订阅内容失败')
    }
    
    generatedConfig.value = await response.text()
    configUrl.value = subscriptionUrl
    
    // 生成短链接
    await generateShortUrl()
    
    ElMessage.success('配置生成成功')
  } catch (error) {
    console.error('配置生成失败:', error)
    ElMessage.error('配置生成失败')
  } finally {
    loading.value = false
  }
}

const generateShortUrl = async () => {
  try {
    // 调用短链接生成API
    const formatLabel = configForm.value.format === 'universal' ? '万能订阅' : configForm.value.format.toUpperCase()
    const response = await api.post('/api/short-url/create', {
      original_url: configUrl.value,
      title: `订阅配置 - ${formatLabel}`
    })
    
    console.log('短链接API响应:', response.data)
    
    if (response.data && response.data.short_url) {
      shortUrl.value = response.data.short_url
      console.log('短链接生成成功:', shortUrl.value)
    } else {
      console.warn('短链接API返回数据格式不正确:', response.data)
      shortUrl.value = configUrl.value
    }
  } catch (error) {
    console.error('生成短链接失败:', error)
    // 如果短链接生成失败，使用原始链接
    shortUrl.value = configUrl.value
  }
}

const copyConfig = () => {
  navigator.clipboard.writeText(generatedConfig.value).then(() => {
    ElMessage.success('配置已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}


const copyShortUrl = () => {
  navigator.clipboard.writeText(shortUrl.value).then(() => {
    ElMessage.success('订阅链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const resetForm = () => {
  configForm.value = {
    format: 'clash'
  }
  generatedConfig.value = ''
  configUrl.value = ''
  shortUrl.value = ''
}
</script>

<style scoped>
.output-page {
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

.config-url-section {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>