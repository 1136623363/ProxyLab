<template>
  <div id="app">
    <!-- 登录页面 -->
    <router-view v-if="isLoginPage" />
    
    <!-- 主应用布局 -->
    <el-container v-else class="layout-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
        <div class="logo">
          <img src="/logo.svg" alt="Logo" v-if="!isCollapse" />
          <span v-if="!isCollapse">订阅转换器</span>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="true"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>仪表板</span>
          </el-menu-item>
          
          <el-menu-item index="/nodes">
            <el-icon><Connection /></el-icon>
            <span>节点管理</span>
          </el-menu-item>
          
          <el-menu-item index="/subscriptions">
            <el-icon><Link /></el-icon>
            <span>订阅管理</span>
          </el-menu-item>
          
          
          <el-menu-item index="/output">
            <el-icon><Download /></el-icon>
            <span>输出配置</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主要内容区 -->
      <el-container class="main-container">
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <el-button
              type="text"
              @click="toggleCollapse"
              class="collapse-btn"
            >
              <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
            </el-button>
            
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item
                v-for="item in breadcrumbs"
                :key="item.path"
                :to="item.path"
              >
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <!-- 通知 -->
            <el-badge :value="notificationCount" class="notification-badge">
              <el-button type="text" @click="showNotifications">
                <el-icon><Bell /></el-icon>
              </el-button>
            </el-badge>
            
            <!-- 用户菜单 -->
            <el-dropdown @command="handleUserCommand">
              <div class="user-info">
                <el-avatar :size="32" :src="userAvatar">
                  {{ userStore.user?.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ userStore.user?.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="settings">账户设置</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 页面内容 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    
    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notificationDrawer"
      direction="rtl"
      size="400px"
    >
      <template #header>
        <div class="notification-header">
          <span>系统通知</span>
          <div class="notification-header-actions">
            <el-button 
              v-if="unreadCount > 0"
              size="small" 
              type="primary" 
              @click="markAllAsRead"
            >
              一键已读
            </el-button>
            <el-button 
              v-if="notifications.length > 0"
              size="small" 
              type="danger" 
              @click="deleteAllNotifications"
            >
              一键删除
            </el-button>
            <el-button 
              size="small" 
              type="text" 
              @click="notificationDrawer = false"
            >
              关闭
            </el-button>
          </div>
        </div>
      </template>
      <div class="notification-list">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
          :class="{ 'unread': !notification.read }"
        >
          <div class="notification-content">
            <div class="notification-title">
              {{ notification.title }}
              <el-tag v-if="!notification.read" type="danger" size="small">未读</el-tag>
            </div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-time">{{ formatTime(notification.time) }}</div>
          </div>
          <div class="notification-actions">
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteNotification(notification.id)"
            >
              删除
            </el-button>
          </div>
        </div>
        
        <div v-if="notifications.length === 0" class="empty-notifications">
          <el-empty description="暂无通知" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const isCollapse = ref(false)
const notificationDrawer = ref(false)
const notificationCount = ref(0)
const notifications = ref([])

// 计算属性
const isLoginPage = computed(() => route.path === '/login')

const activeMenu = computed(() => route.path)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    name: item.meta.title
  }))
})

const userAvatar = computed(() => {
  return userStore.user?.avatar || ''
})

// 方法
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const showNotifications = () => {
  notificationDrawer.value = true
}

const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确认要退出登录吗？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消
  }
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}

// 监听路由变化
watch(route, (newRoute) => {
  // 更新页面标题
  document.title = `${newRoute.meta?.title || '订阅转换器'} - 订阅转换器`
}, { immediate: true })

// 初始化
const init = async () => {
  // 初始化用户状态
  await userStore.init()
  
  // 如果已登录，加载通知
  if (userStore.isLoggedIn) {
    loadNotifications()
  }
}

const loadNotifications = () => {
  // 从本地存储加载通知数据
  const savedNotifications = localStorage.getItem('notifications')
  if (savedNotifications) {
    const parsed = JSON.parse(savedNotifications)
    // 转换时间字符串为Date对象
    notifications.value = parsed.map(notification => ({
      ...notification,
      time: new Date(notification.time)
    }))
  } else {
    // 初始化通知数据
    notifications.value = [
      {
        id: 1,
        title: '节点检测完成',
        message: '已检测 15 个节点，其中 12 个正常',
        time: new Date(),
        read: false
      },
      {
        id: 2,
        title: '订阅更新成功',
        message: '订阅源已成功更新，新增 3 个节点',
        time: new Date(Date.now() - 3600000),
        read: true
      },
      {
        id: 3,
        title: '系统维护通知',
        message: '系统将于今晚 2:00-4:00 进行维护，期间可能无法访问',
        time: new Date(Date.now() - 7200000),
        read: false
      }
    ]
    saveNotifications()
  }
  updateNotificationCount()
}

const saveNotifications = () => {
  // 保存通知数据到本地存储
  localStorage.setItem('notifications', JSON.stringify(notifications.value))
}

const updateNotificationCount = () => {
  notificationCount.value = notifications.value.filter(n => !n.read).length
}

// 计算未读通知数量
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

const markAllAsRead = () => {
  const unreadNotifications = notifications.value.filter(n => !n.read)
  if (unreadNotifications.length === 0) {
    ElMessage.info('没有未读通知')
    return
  }
  
  unreadNotifications.forEach(notification => {
    notification.read = true
  })
  
  saveNotifications()
  updateNotificationCount()
  ElMessage.success(`已标记 ${unreadNotifications.length} 条通知为已读`)
}

const markAsRead = (notificationId) => {
  const notification = notifications.value.find(n => n.id === notificationId)
  if (notification) {
    notification.read = true
    saveNotifications()
    updateNotificationCount()
    ElMessage.success('已标记为已读')
  }
}

const deleteNotification = (notificationId) => {
  const index = notifications.value.findIndex(n => n.id === notificationId)
  if (index !== -1) {
    notifications.value.splice(index, 1)
    saveNotifications()
    updateNotificationCount()
    ElMessage.success('通知已删除')
  }
}

const deleteAllNotifications = () => {
  if (notifications.value.length === 0) {
    ElMessage.info('没有通知可删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除所有 ${notifications.value.length} 条通知吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    notifications.value = []
    saveNotifications()
    updateNotificationCount()
    ElMessage.success('所有通知已删除')
  }).catch(() => {
    // 用户取消删除
  })
}

// 启动应用
init()
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #434a50;
}

.logo img {
  width: 32px;
  height: 32px;
  margin-right: 8px;
}

.sidebar-menu {
  border: none;
  background: #304156;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #263445;
  color: white;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #409eff;
  color: white;
}

.main-container {
  background: #f5f7fa;
}

.header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  margin-right: 20px;
  font-size: 18px;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-badge {
  margin-right: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
}

.notification-list {
  padding: 0;
}

.notification-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #f0f9ff;
  border-left: 3px solid #409eff;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.notification-header-actions {
  display: flex;
  gap: 8px;
}

.notification-content {
  flex: 1;
  margin-right: 12px;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-message {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-notifications {
  padding: 40px 20px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 1000;
    height: 100vh;
  }
  
  .main-container {
    margin-left: 0;
  }
  
  .header {
    padding: 0 15px;
  }
  
  .main-content {
    padding: 15px;
  }
}
</style>