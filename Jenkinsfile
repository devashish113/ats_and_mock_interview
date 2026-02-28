// Jenkinsfile for CareerPrep AI (ATS Resume & Mock Interview Application)
pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_VERSION = '3.8'
        GROQ_API_KEY = credentials('groq-api-key')
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Checked out branch: ${env.BRANCH_NAME ?: 'main'}"
            }
        }

        stage('Validate') {
            parallel {
                stage('Validate Backend') {
                    steps {
                        dir('backend') {
                            echo 'Validating backend requirements...'
                            sh '''
                                if [ -f requirements.txt ]; then
                                    echo "requirements.txt found"
                                else
                                    echo "ERROR: requirements.txt not found"
                                    exit 1
                                fi
                            '''
                        }
                    }
                }
                stage('Validate Frontend') {
                    steps {
                        dir('frontend') {
                            echo 'Validating frontend package.json...'
                            sh '''
                                if [ -f package.json ]; then
                                    echo "package.json found"
                                else
                                    echo "ERROR: package.json not found"
                                    exit 1
                                fi
                            '''
                        }
                    }
                }
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('Build Backend') {
                    steps {
                        dir('backend') {
                            echo 'Building backend Docker image...'
                            sh 'docker build -t ats-backend:${IMAGE_TAG} -t ats-backend:latest .'
                        }
                    }
                }
                stage('Build Frontend') {
                    steps {
                        dir('frontend') {
                            echo 'Building frontend Docker image...'
                            sh 'docker build --build-arg REACT_APP_API_URL=http://localhost:8000 -t ats-frontend:${IMAGE_TAG} -t ats-frontend:latest .'
                        }
                    }
                }
            }
        }

        stage('Test Backend') {
            steps {
                dir('backend') {
                    echo 'Running backend tests...'
                    sh '''
                        docker run --rm ats-backend:${IMAGE_TAG} python -c "
import sys
sys.path.insert(0, '/app')
from app.main import app
print('FastAPI app imported successfully')
print('All imports validated')
"
                    '''
                }
            }
        }

        stage('Security Scan') {
            steps {
                echo 'Running security scan on Docker images...'
                sh '''
                    echo "Checking for exposed secrets..."
                    if grep -r "GROQ_API_KEY.*=" --include="*.py" --include="*.js" backend/ frontend/src/ 2>/dev/null | grep -v ".env" | grep -v "process.env" | grep -v "os.getenv"; then
                        echo "WARNING: Possible hardcoded API keys found"
                    else
                        echo "No hardcoded secrets detected"
                    fi
                '''
            }
        }

        stage('Deploy with Docker Compose') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying application with Docker Compose...'
                sh '''
                    docker-compose down --remove-orphans || true
                    docker-compose up -d --build
                    sleep 10
                    echo "Waiting for services to be healthy..."
                '''
            }
        }

        stage('Health Check') {
            when {
                branch 'main'
            }
            steps {
                echo 'Running health checks...'
                sh '''
                    # Check backend health
                    for i in 1 2 3 4 5; do
                        if curl -s http://localhost:8000/docs > /dev/null; then
                            echo "Backend is healthy"
                            break
                        fi
                        echo "Waiting for backend... attempt $i"
                        sleep 5
                    done

                    # Check frontend health
                    for i in 1 2 3 4 5; do
                        if curl -s http://localhost:3000 > /dev/null; then
                            echo "Frontend is healthy"
                            break
                        fi
                        echo "Waiting for frontend... attempt $i"
                        sleep 5
                    done
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed'
            cleanWs()
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed!'
        }
    }
}
