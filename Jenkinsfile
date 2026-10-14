pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        PYTHONUNBUFFERED = '1'
        CI = 'true'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Backend tests') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r backend/requirements-dev.txt
                    mkdir -p reports
                    cd backend
                    ../.venv-ci/bin/python -m compileall -q .
                    ../.venv-ci/bin/python -m pytest -q tests --junitxml=../reports/backend-junit.xml
                '''
            }
            post {
                always {
                    junit testResults: 'reports/backend-junit.xml', allowEmptyResults: true
                }
            }
        }

        stage('Frontend checks and build') {
            steps {
                sh '''
                    set -eu
                    cd frontend
                    npm install --no-audit --no-fund
                    npm run build
                '''
            }
        }

        stage('Configuration validation') {
            steps {
                sh '''
                    set -eu
                    test ! -e backend/.env || { echo "Refusing to overwrite existing backend/.env"; exit 1; }
                    cp backend/.env.example backend/.env
                    cleanup() { rm -f backend/.env; }
                    trap cleanup EXIT
                    GRAFANA_ADMIN_PASSWORD='ci-only-placeholder-password' docker compose -f docker-compose.production.yml config --quiet
                    python3 -m json.tool grafana/dashboards/scoutline-overview.json >/dev/null
                    docker run --rm --entrypoint promtool -v "$PWD/prometheus:/etc/prometheus:ro" prom/prometheus:v2.55.1 check config /etc/prometheus/prometheus.yml
                    docker run --rm --entrypoint promtool -v "$PWD/prometheus:/etc/prometheus:ro" prom/prometheus:v2.55.1 check rules /etc/prometheus/alerts.yml
                '''
            }
        }

        stage('Build production images') {
            steps {
                sh '''
                    set -eu
                    docker build --pull -t scoutline-backend:$IMAGE_TAG ./backend
                    docker build --pull -t scoutline-frontend:$IMAGE_TAG ./frontend
                '''
            }
        }

        stage('Secret and image vulnerability scans') {
            steps {
                sh '''
                    set -eu
                    gitleaks detect --source . --no-git --redact
                    trivy image --exit-code 1 --severity HIGH,CRITICAL scoutline-backend:$IMAGE_TAG
                    trivy image --exit-code 1 --severity HIGH,CRITICAL scoutline-frontend:$IMAGE_TAG
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            sh 'rm -rf .venv-ci'
        }
        success {
            echo 'CI checks passed. No deployment was attempted.'
        }
        failure {
            echo 'CI failed. Review the failing stage and archived reports before promoting an image.'
        }
    }
}
