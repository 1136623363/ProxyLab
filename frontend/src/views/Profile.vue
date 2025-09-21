<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>个人资料</h1>
      <p>管理您的个人信息和账户设置</p>
    </div>
    
    <div class="content">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="16">
          <el-card>
            <template #header>
              <span>基本信息</span>
            </template>
            
            <el-form :model="profileForm" label-width="100px">
              <el-form-item label="用户名">
                <el-input v-model="profileForm.username" disabled />
              </el-form-item>
              
              <el-form-item label="邮箱">
                <el-input v-model="profileForm.email" />
              </el-form-item>
              
              <el-form-item label="昵称">
                <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
              </el-form-item>
              
              <el-form-item label="头像">
                <el-upload
                  class="avatar-uploader"
                  action="#"
                  :show-file-list="false"
                  :on-success="handleAvatarSuccess"
                  :before-upload="beforeAvatarUpload"
                >
                  <img v-if="profileForm.avatar" :src="profileForm.avatar" class="avatar" />
                  <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                </el-upload>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="updateProfile">
                  更新资料
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="8">
          <el-card>
            <template #header>
              <span>账户信息</span>
            </template>
            
            <div class="account-info">
              <div class="info-item">
                <span class="label">注册时间：</span>
                <span class="value">2024-01-01</span>
              </div>
              <div class="info-item">
                <span class="label">最后登录：</span>
                <span class="value">2024-01-15 10:30:00</span>
              </div>
              <div class="info-item">
                <span class="label">账户状态：</span>
                <el-tag type="success">正常</el-tag>
              </div>
            </div>
          </el-card>
          
          <el-card style="margin-top: 20px;">
            <template #header>
              <span>安全设置</span>
            </template>
            
            <div class="security-actions">
              <el-button type="warning" @click="changePassword">
                修改密码
              </el-button>
              <el-button type="danger" @click="logout">
                退出登录
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const profileForm = ref({
  username: 'admin',
  email: 'admin@example.com',
  nickname: '管理员',
  avatar: ''
})

const handleAvatarSuccess = (response, file) => {
  profileForm.value.avatar = URL.createObjectURL(file.raw)
}

const beforeAvatarUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('头像图片只能是 JPG/PNG 格式!')
  }
  if (!isLt2M) {
    ElMessage.error('头像图片大小不能超过 2MB!')
  }
  return isJPG && isLt2M
}

const updateProfile = () => {
  ElMessage.success('资料更新成功')
}

const changePassword = () => {
  ElMessage.info('修改密码功能开发中...')
}

const logout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.profile-page {
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

.avatar-uploader {
  display: flex;
  align-items: center;
}

.avatar-uploader .avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 80px;
  height: 80px;
  line-height: 80px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 50%;
}

.account-info {
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

.security-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>