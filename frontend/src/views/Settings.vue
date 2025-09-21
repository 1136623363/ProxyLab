<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>配置系统参数和偏好设置</p>
    </div>
    
    <div class="content">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="16">
          <el-card>
            <template #header>
              <span>基本设置</span>
            </template>
            
            <el-form :model="settingsForm" label-width="120px">
              <el-form-item label="系统名称">
                <el-input v-model="settingsForm.systemName" placeholder="请输入系统名称" />
              </el-form-item>
              
              <el-form-item label="自动检测间隔">
                <el-input-number
                  v-model="settingsForm.checkInterval"
                  :min="1"
                  :max="60"
                  controls-position="right"
                />
                <span style="margin-left: 8px; color: #909399;">分钟</span>
              </el-form-item>
              
              <el-form-item label="超时时间">
                <el-input-number
                  v-model="settingsForm.timeout"
                  :min="1"
                  :max="30"
                  controls-position="right"
                />
                <span style="margin-left: 8px; color: #909399;">秒</span>
              </el-form-item>
              
              <el-form-item label="启用通知">
                <el-switch v-model="settingsForm.enableNotification" />
              </el-form-item>
              
              <el-form-item label="启用日志">
                <el-switch v-model="settingsForm.enableLogging" />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveSettings">
                  保存设置
                </el-button>
                <el-button @click="resetSettings">重置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="8">
          <el-card>
            <template #header>
              <span>系统信息</span>
            </template>
            
            <div class="system-info">
              <div class="info-item">
                <span class="label">版本号：</span>
                <span class="value">v1.0.0</span>
              </div>
              <div class="info-item">
                <span class="label">构建时间：</span>
                <span class="value">2024-01-15</span>
              </div>
              <div class="info-item">
                <span class="label">运行时间：</span>
                <span class="value">2天3小时</span>
              </div>
              <div class="info-item">
                <span class="label">内存使用：</span>
                <span class="value">128MB</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const settingsForm = ref({
  systemName: '订阅转换器',
  checkInterval: 5,
  timeout: 10,
  enableNotification: true,
  enableLogging: true
})

const saveSettings = () => {
  ElMessage.success('设置保存成功')
}

const resetSettings = () => {
  settingsForm.value = {
    systemName: '订阅转换器',
    checkInterval: 5,
    timeout: 10,
    enableNotification: true,
    enableLogging: true
  }
  ElMessage.info('设置已重置')
}
</script>

<style scoped>
.settings-page {
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

.system-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  font-size: 14px;
  color: #606266;
}

.value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}
</style>