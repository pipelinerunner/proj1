pipeline {
    agent any

    environment {
        // Define a unique name for your app container to avoid conflicts
        APP_CONTAINER_NAME = "proj1-${BUILD_NUMBER}"
        // Define the image name for your application
        APP_IMAGE_NAME = "proj1"
        APP_IMAGE_TAG = "latest"
        // Define the port your Python app runs on INSIDE its container
        APP_INTERNAL_PORT = 5000 // Example: for Flask/Django dev server
        // Host port mapping (optional if only internal communication is needed, but good for debugging from host)
        APP_HOST_PORT = 5088
        // Define the ZAP container name
        ZAP_CONTAINER_NAME = "zap-scanner-${BUILD_NUMBER}"
        // Define a directory for ZAP reports within the workspace
        ZAP_HTML_REPORT = "zap-report.html"
        // Define the name for the shared Docker network
        DOCKER_NETWORK_NAME = "ci-dast-network-${BUILD_NUMBER}"
        // Image for running curl for health checks
        CURL_IMAGE = "curlimages/curl:latest"
        REPORTS_DIR = "ci-reports"
    }

    stages {

        stage('OSV-scan') {
            steps {
                script {
                    sh 'echo "[*] OSV-scan scanning"'
                    sh 'ls *.json || true'
                    sh 'mkdir ${REPORTS_DIR}'
                    // Run the OSV-Scanner Docker image
                    docker.image('ghcr.io/google/osv-scanner:latest').inside('--entrypoint "" ') {
                        // Run the OSV-Scanner command and generate the JSON report
                        sh "/osv-scanner --format json -r ./src > ${REPORTS_DIR}/osv-results.json || true"
                    }
                }
            }
        }
        
        stage('bandit-scan') {
            steps {
                script {
                     sh 'echo "[*] bandit scanning"'
                     docker.image('python:3.9-slim-buster').inside(' -u 0 ') {
                        sh 'ls -lrt'
                        sh 'pip install bandit '
                        sh "bandit -r ./src -f html -o ${REPORTS_DIR}/bandit-report.html --severity-level low || true"
                    }
                    
                }
            }
        }
        
        stage('semgrep-scan') {
            steps {
                script {
                     sh 'echo "[*] semgrep scanning"'
                     docker.image('returntocorp/semgrep').inside {
                        sh "semgrep --config=auto .  --output=${REPORTS_DIR}/semgrep-results.txt || true"
                    }
                    
                }
            }
        }



        stage('python-tests') {
            steps {
                script {
                     sh 'echo "[*] python tests"'
                     docker.image('python:3.9-slim-buster').inside(' -u 0 ') {
                        sh 'apt-get update && apt-get install -y make git '
                        sh 'make test'
                    }
                    
                }
            }
        }
      
        stage('build-image') {
            steps {
                script {
                    sh 'echo "[*] Building container image"'
                    def image = docker.build("proj1:latest", "-f build/Dockerfile .")
                    sh 'docker save -o proj1.latest.tar proj1:latest'
                    sh 'ls -lrt'
                }
            }
        }

        stage('trivy-scan') {
            steps {
                script {
                    sh 'echo "[*] Trivy scanning"'
                    docker.image('aquasec/trivy:latest').inside('--entrypoint "" ') {
                        sh 'ls -l'

                        sh 'trivy image --exit-code "1" --severity "MEDIUM,HIGH,CRITICAL"  --cache-dir /tmp/.cache  --format json --scanners vuln --output report_trivy.json --input proj1.latest.tar || true'
                        sh 'ls *.json'
                        sh "cp report_trivy.json ${REPORTS_DIR}/"
                    }
                    
                }
            }
        }


        stage('Setup Network') {
            steps {
                script {
                    echo "Creating Docker network ${DOCKER_NETWORK_NAME}..."
                    // Create the network; || true to not fail if it already exists (though build-specific name makes this unlikely)
                    sh "docker network create ${DOCKER_NETWORK_NAME} || true"
                }
            }
        }

        stage('app-deploy') {
            steps {
                script {
                    sh """
                        docker run -d --name ${APP_CONTAINER_NAME} \
                            --network ${DOCKER_NETWORK_NAME} \
                            -p ${APP_HOST_PORT}:${APP_INTERNAL_PORT} \
                            ${APP_IMAGE_NAME}:${APP_IMAGE_TAG}
                    """

                    echo "Waiting for application to start..."
                    sh "sleep 10" // Give it some time to start up

                    def healthCheckUrl = "http://${APP_CONTAINER_NAME}:${APP_INTERNAL_PORT}/" // Adjust path if needed


                    try {
                            // The sh step is executed in Jenkins container, but docker run executes on the Docker host
                            // This temporary container will run on the DOCKER_NETWORK_NAME
                        sh """
                            docker run --rm --network ${DOCKER_NETWORK_NAME} ${CURL_IMAGE} --silent --fail --connect-timeout 10 ${healthCheckUrl}
                            """

                        echo "Application health check successful ."
                    } catch (Exception e) {
                        echo "Health check attempt failed."
                    }

                }
            }
        }

 
        stage('zap-scan') {
            steps {
                script {
                    echo "Starting OWASP ZAP DAST Scan..."

                    // ZAP will target the app container by its name on the shared Docker network
                    def targetUrl = "http://${APP_CONTAINER_NAME}:${APP_INTERNAL_PORT}"

                    try {
                        sh "docker run  --name ${ZAP_CONTAINER_NAME}  --network ${DOCKER_NETWORK_NAME} -p 8090:8090 -i zaproxy/zap-bare zap.sh -cmd -port 8090 -quickurl ${targetUrl} -quickout /zap/zap-report.html"
                        sh "docker cp ${ZAP_CONTAINER_NAME}:/zap/zap-report.html ${REPORTS_DIR}/${ZAP_HTML_REPORT}"
                        echo "ZAP Scan completed. "
                    } catch (Exception e) {
                        echo "ZAP Scan found vulnerabilities or an error occurred: ${e.getMessage()}"
                    }
                }
            }
        }

        stage('Archive Reports') {
            steps {
                    echo "Archiving all reports..."
                    //archiveArtifacts artifacts: "${ZAP_HTML_REPORT}", fingerprint: true
                    archiveArtifacts artifacts: "${REPORTS_DIR}/**", fingerprint: true
                    // publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: true, reportDir: ZAP_REPORTS_DIR, reportFiles: 'report.html', reportName: 'ZAP Scan Report'])
                    echo "All reports archived."
                }
        }
 
 

    }

    post {
        always {

            cleanWs()

            echo "Stopping and removing application container ${APP_CONTAINER_NAME}..."
            sh "docker stop ${APP_CONTAINER_NAME} || true"
            sh "docker rm ${APP_CONTAINER_NAME} || true"
            echo "Application container ${APP_CONTAINER_NAME} stopped and removed."

            echo "Stopping and removing ZAP container ${ZAP_CONTAINER_NAME}..."
            sh "docker stop ${ZAP_CONTAINER_NAME} || true"
            sh "docker rm ${ZAP_CONTAINER_NAME} || true"
            echo "ZAP container ${ZAP_CONTAINER_NAME} stopped and removed."


            echo "Removing Docker network ${DOCKER_NETWORK_NAME}..."
            sh "docker network rm ${DOCKER_NETWORK_NAME} || true"
            echo "Docker network ${DOCKER_NETWORK_NAME} removed."

            cleanWs()
        }
    }

}

