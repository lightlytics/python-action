pipeline {
   agent {label 'master'}

   stages {
     
      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }

      stage('Build Docker Images') {
         steps {
            script {
               sh "sudo bash devops-scripts/test_terraform_api.sh ${terraform_json}"
            }
            input('Do you want to proceed?')
      }
   }

   }
}
