pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'project-back-python'
        DOCKERFILE_PATH = 'Dockerfile'
        PROJECT_PATH = "back-python"

        MAIN_HOST = '13.124.109.82'
        DEV_HOST = '3.34.155.126'

        REMOTE_USER = 'ubuntu'
        REMOTE_PATH = '/home/ubuntu/devops-midterm'
    }

    stages {

        stage('Select Deploy Target') {
            steps {
                script {
                    if (env.BRANCH_NAME == "main") {
                        env.DEPLOY_HOST = MAIN_HOST
                        echo "🚀 Deploy target: MAIN SERVER (${MAIN_HOST})"
                    } else if (env.BRANCH_NAME == "develop") {
                        env.DEPLOY_HOST = DEV_HOST
                        echo "🧪 Deploy target: DEVELOP SERVER (${DEV_HOST})"
                    } else {
                        error("❌ This pipeline only supports main / develop branches.")
                    }
                }
            }
        }

        stage('Checkout & Build on Remote') {
            steps {
                sshagent(credentials: ['admin']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${DEPLOY_HOST} << EOF
                            set -e
                            cd ${REMOTE_PATH}/${PROJECT_PATH}

                            git reset --hard
                            git pull origin ${BRANCH_NAME}

                            docker build \
                                -t ${DOCKER_IMAGE_NAME}:latest \
                                -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} \
                                -f ${DOCKERFILE_PATH} .
EOF
                    """
                }
            }
        }

        stage('Docker Compose Up') {
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${DEPLOY_HOST} << EOF
                            set -e
                            cd ${REMOTE_PATH}/${PROJECT_PATH}
                            docker-compose up -d --force-recreate
EOF
                    """
                }
            }
        }

        stage('Load Test (Only on develop)') {
            when {
                branch 'develop'
            }
            steps {
                sh """
                    jmeter -n -t healthybot-test-plan-full.jmx -l results.jtl
                """
            }
        }

        stage('Check p95 Latency (Only on develop)') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    // p95 계산 (JTL 에서 95% latency 추출)
                    def p95 = sh(script: "awk -F, 'NR>1 {print \$2}' results.jtl | sort -n | awk 'NR==int(NR*0.95)'", returnStdout: true).trim()
                    echo "📊 p95 latency = ${p95} ms"

                    if (p95.toInteger() > 400) {
                        error("❌ p95 latency ${p95}ms > 400ms → 성능 기준 미달. PR 병합 금지.")
                    } else {
                        echo "✅ 성능 기준 통과 (p95 ${p95}ms <= 400ms)"
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment completed successfully: #${BUILD_NUMBER}"
        }
        failure {
            echo "⚠️ Pipeline failed. Please check logs."
        }
    }
}
