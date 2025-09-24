#!/bin/bash
# 测试Nginx配置

echo "🔍 测试Nginx配置..."

# 检查Nginx配置文件语法
if nginx -t; then
    echo "✅ Nginx配置语法正确"
else
    echo "❌ Nginx配置语法错误"
    exit 1
fi

# 检查Nginx用户
if id nginx >/dev/null 2>&1; then
    echo "✅ Nginx用户存在"
else
    echo "❌ Nginx用户不存在"
fi

# 检查权限
echo "📁 检查目录权限:"
ls -la /var/log/nginx
ls -la /var/lib/nginx
ls -la /var/cache/nginx

echo "🔧 检查Nginx进程:"
ps aux | grep nginx

echo "📋 检查端口:"
netstat -tlnp | grep :80
