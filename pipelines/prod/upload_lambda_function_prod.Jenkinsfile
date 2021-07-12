pipeline {
    agent {label 'slave'}
    stages {
      stage('CheckOut From GitHub - lightlytics ') {
         steps {
            dir('lightlytics') {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'e2be5b21-e679-4dbf-9c18-945353131920', url: 'https://github.com/lightlytics/lightlytics.git']]])
            }
         }
      }

      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'e2be5b21-e679-4dbf-9c18-945353131920', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }

      stage('Upload lambda functions') {
         steps {
            sh  'echo "Upload production lambda functions"'
            sh '''
                #!/bin/bash
                echo "Current Path $PATH"
                cd lightlytics/lambda_functions && make pkg-prod
            '''
         }
      }
    }
}


