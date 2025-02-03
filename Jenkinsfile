pipeline {
    agent {
        label 'int-python-stg-1'
    }
    stages {
        stage("Deploy") {
            steps {
                sh "sudo docker compose up --build -d"
                sh "echo py-icebutton.mobiloitte.io"
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('mobiloitte-sonar') {
                    script {
                        def scannerHome = tool 'mobiloitte-sonar-scanner';
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }
    }
}
