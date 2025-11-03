pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'project-back-python'
        DOCKERFILE_PATH = 'Dockerfile'
        PROJECT_PATH = "back-python"
        REMOTE_USER = 'ubuntu'
        REMOTE_HOST = '13.124.109.82'
        REMOTE_PATH = '/home/ubuntu/devops-midterm'
    }

    stages {
        stage('Checkout & Build on Remote') {
            steps {
                sshagent(credentials: ['admin']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} << EOF
                            set -e
                            cd ${REMOTE_PATH}/${PROJECT_PATH}

                            echo "Updating code..."
                            git reset --hard
                            git pull origin main

                            echo "Current commit: \$(git rev-parse --short HEAD)"
                            echo "Branch: \$(git rev-parse --abbrev-ref HEAD)"
                            echo "Commit message: \$(git log -1 --pretty=%B)"

                            echo "Building Docker image..."
                            docker build \
                                -t ${DOCKER_IMAGE_NAME}:latest \
                                -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} \
                                -f ${DOCKERFILE_PATH} \
                                .
EOF
                    """
                }
            }
        }

        stage('Docker Compose Up on Remote') {
            steps {
                sshagent(credentials: ['admin']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} << EOF
                            set -e
                            cd ${REMOTE_PATH}/${PROJECT_PATH}

                            echo "Starting services with Docker Compose..."
                            docker-compose pull
                            docker-compose up -d
EOF
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployment completed successfully for build #${BUILD_NUMBER}"
        }
        failure {
            echo "Pipeline failed. Check logs."
        }
    }
}
