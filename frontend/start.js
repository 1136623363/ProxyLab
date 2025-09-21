#!/usr/bin/env node

const { spawn } = require('child_process')
const path = require('path')

console.log('? 启动订阅转换器前端...')

// 设置环境变量
process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
process.env.VITE_APP_TITLE = process.env.VITE_APP_TITLE || '订阅转换器'
process.env.VITE_APP_VERSION = process.env.VITE_APP_VERSION || '1.0.0'

// 启动Vite开发服务器
const vite = spawn('npm', ['run', 'dev'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
})

vite.on('error', (error) => {
  console.error('? 启动失败:', error)
  process.exit(1)
})

vite.on('close', (code) => {
  console.log(`前端服务已退出，退出码: ${code}`)
})

// 处理退出信号
process.on('SIGINT', () => {
  console.log('\n? 正在停止前端服务...')
  vite.kill('SIGINT')
})

process.on('SIGTERM', () => {
  console.log('\n? 正在停止前端服务...')
  vite.kill('SIGTERM')
})
