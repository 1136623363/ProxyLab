pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKERHUB_USERNAME = '1136623363'
        IMAGE_NAME = 'proxylab'
        REGISTRY = 'docker.io'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    python -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                    pip install pytest pytest-cov
                    # 创建测试目录（如果不存在）
                    mkdir -p tests
                    # 运行测试（如果测试文件存在）
                    if [ -f "tests/test_*.py" ]; then
                        pytest tests/ --cov=app --cov-report=xml
                    else
                        echo "No tests found, skipping test execution"
                        # 创建一个空的coverage.xml文件
                        echo '<?xml version="1.0" ?><coverage></coverage>' > coverage.xml
                    fi
                '''
            }
            post {
                always {
                    publishCoverage adapters: [
                        coberturaAdapter('coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
        stage('Build') {
            steps {
                script {
                    def backendImage = docker.build("${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${env.BUILD_NUMBER}")
                    def frontendImage = docker.build("${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:${env.BUILD_NUMBER}", "./frontend")
                    
                    // 标记为latest（仅main分支）
                    if (env.BRANCH_NAME == 'main') {
                        sh "docker tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${env.BUILD_NUMBER} ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
                        sh "docker tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:${env.BUILD_NUMBER} ${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:latest"
                    }
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", 'dockerhub-credentials') {
                        sh "docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                        sh "docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:${env.BUILD_NUMBER}"
                        
                        if (env.BRANCH_NAME == 'main') {
                            sh "docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
                            sh "docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:latest"
                        }
                    }
                }
            }
        }
        
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    # 拉取最新镜像
                    docker pull ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                    docker pull ${DOCKERHUB_USERNAME}/${IMAGE_NAME}-frontend:latest
                    
                    # 部署到生产环境
                    docker-compose -f docker-compose.prod.yml up -d
                '''
            }
        }
    }
    
    post {
        always {
            // 清理工作空间
            cleanWs()
        }
        success {
            // 发送成功通知
            emailext (
                subject: "构建成功: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "构建成功完成！",
                to: "admin@example.com"
            )
        }
        failure {
            // 发送失败通知
            emailext (
                subject: "构建失败: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "构建失败，请检查日志。",
                to: "admin@example.com"
            )
        }
    }
}
