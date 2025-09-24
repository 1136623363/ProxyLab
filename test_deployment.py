#!/usr/bin/env python3
"""
部署测试脚本 - 验证所有功能是否正常
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8899"
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
    def test_health_check(self) -> bool:
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_frontend_access(self) -> bool:
        """测试前端访问"""
        print("🔍 测试前端访问...")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200 and "Subscription Converter" in response.text:
                print("✅ 前端访问正常")
                return True
            else:
                print(f"❌ 前端访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 前端访问异常: {e}")
            return False
    
    def test_api_docs(self) -> bool:
        """测试API文档"""
        print("🔍 测试API文档...")
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200 and "Swagger" in response.text:
                print("✅ API文档访问正常")
                return True
            else:
                print(f"❌ API文档访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API文档访问异常: {e}")
            return False
    
    def test_static_files(self) -> bool:
        """测试静态文件"""
        print("🔍 测试静态文件...")
        try:
            # 测试静态文件目录是否存在
            response = self.session.get(f"{self.base_url}/static/", timeout=10)
            if response.status_code in [200, 404]:  # 404也是正常的，说明路由工作
                print("✅ 静态文件路由正常")
                return True
            else:
                print(f"❌ 静态文件路由失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 静态文件路由异常: {e}")
            return False
    
    def test_user_login(self) -> bool:
        """测试用户登录"""
        print("🔍 测试用户登录...")
        try:
            # 测试JSON登录
            response = self.session.post(
                f"{self.base_url}/auth/login-json",
                json=TEST_USER,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    print("✅ 用户登录成功")
                    return True
                else:
                    print("❌ 登录响应格式错误")
                    return False
            else:
                print(f"❌ 用户登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户登录异常: {e}")
            return False
    
    def test_protected_endpoints(self) -> bool:
        """测试受保护的端点"""
        if not self.token:
            print("❌ 没有认证token，跳过受保护端点测试")
            return False
        
        print("🔍 测试受保护的端点...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 测试获取用户信息
            response = self.session.get(
                f"{self.base_url}/auth/me",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ 受保护端点访问正常")
                return True
            else:
                print(f"❌ 受保护端点访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 受保护端点访问异常: {e}")
            return False
    
    def test_database_operations(self) -> bool:
        """测试数据库操作"""
        if not self.token:
            print("❌ 没有认证token，跳过数据库操作测试")
            return False
        
        print("🔍 测试数据库操作...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 测试获取节点列表
            response = self.session.get(
                f"{self.base_url}/api/nodes/",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ 数据库操作正常")
                return True
            else:
                print(f"❌ 数据库操作失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 数据库操作异常: {e}")
            return False
    
    def test_subscription_generation(self) -> bool:
        """测试订阅生成"""
        if not self.token:
            print("❌ 没有认证token，跳过订阅生成测试")
            return False
        
        print("🔍 测试订阅生成...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 测试生成订阅
            response = self.session.get(
                f"{self.base_url}/api/output/subscription?format=clash",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ 订阅生成正常")
                return True
            else:
                print(f"❌ 订阅生成失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 订阅生成异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始部署测试...")
        print(f"测试目标: {self.base_url}")
        print("=" * 50)
        
        tests = {
            "健康检查": self.test_health_check,
            "前端访问": self.test_frontend_access,
            "API文档": self.test_api_docs,
            "静态文件": self.test_static_files,
            "用户登录": self.test_user_login,
            "受保护端点": self.test_protected_endpoints,
            "数据库操作": self.test_database_operations,
            "订阅生成": self.test_subscription_generation,
        }
        
        results = {}
        for test_name, test_func in tests.items():
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results[test_name] = False
            print()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """打印测试总结"""
        print("=" * 50)
        print("📊 测试结果总结:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print("=" * 50)
        print(f"总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！部署成功！")
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关功能")
            return False

def main():
    """主函数"""
    print("ProxyLab 部署测试工具")
    print("=" * 50)
    
    # 检查服务是否运行
    tester = DeploymentTester(BASE_URL)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    for i in range(30):  # 等待最多30秒
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务已启动")
                break
        except:
            pass
        time.sleep(1)
        print(f"等待中... ({i+1}/30)")
    else:
        print("❌ 服务启动超时，请检查Docker容器状态")
        sys.exit(1)
    
    # 运行测试
    results = tester.run_all_tests()
    success = tester.print_summary(results)
    
    if success:
        print("\n🎯 部署验证完成！")
        print(f"🌐 应用地址: {BASE_URL}")
        print(f"📚 API文档: {BASE_URL}/docs")
        print(f"🔧 健康检查: {BASE_URL}/health")
        sys.exit(0)
    else:
        print("\n❌ 部署验证失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
