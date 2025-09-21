#!/usr/bin/env node

const { spawn } = require('child_process')
const path = require('path')

console.log('? ��������ת����ǰ��...')

// ���û�������
process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
process.env.VITE_APP_TITLE = process.env.VITE_APP_TITLE || '����ת����'
process.env.VITE_APP_VERSION = process.env.VITE_APP_VERSION || '1.0.0'

// ����Vite����������
const vite = spawn('npm', ['run', 'dev'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
})

vite.on('error', (error) => {
  console.error('? ����ʧ��:', error)
  process.exit(1)
})

vite.on('close', (code) => {
  console.log(`ǰ�˷������˳����˳���: ${code}`)
})

// �����˳��ź�
process.on('SIGINT', () => {
  console.log('\n? ����ֹͣǰ�˷���...')
  vite.kill('SIGINT')
})

process.on('SIGTERM', () => {
  console.log('\n? ����ֹͣǰ�˷���...')
  vite.kill('SIGTERM')
})
