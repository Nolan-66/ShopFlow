pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Récupération du code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installation des dépendances...'
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Exécution des tests...'
                sh '''
                . venv/bin/activate
                pytest tests/ --junitxml=junit-report.xml
                '''
            }
        }

    }
}