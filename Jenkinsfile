pipeline {
    agent any

    stages {

        stage('OSV-scan') {
            steps {
                script {
                    sh 'echo "[*] OSV-scan scanning"'
                    sh 'ls *.json || true'
                    sh 'rm *.json || true'
                    // Run the OSV-Scanner Docker image
                    docker.image('ghcr.io/google/osv-scanner:latest').inside('--entrypoint "" ') {
                        // Run the OSV-Scanner command and generate the JSON report
                        sh '/osv-scanner --format json -r ./src > osv-results.json || true'
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
                        sh 'bandit -r ./src -f html -o bandit-report.html --severity-level high || true'
                        sh 'ls *.html || true'
                        sh 'cat bandit-report.html | head -n 30'
                    }
                    
                }
            }
        }
        
        stage('semgrep-scan') {
            steps {
                script {
                     sh 'echo "[*] semgrep scanning"'
                     docker.image('returntocorp/semgrep').inside {
                        sh 'semgrep --config=auto .  --output=semgrep-results.txt || true'
                        sh 'ls *.txt'
                        sh 'cat semgrep-results.txt | head -n 30'
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
                        //sh 'apk update && apk add build-base make git '
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
                        sh 'cat report_trivy.json | head -n 30'
                    }
                    
                }
            }
        }



    }

    post {
        always {
            cleanWs()
        }
    }

}

