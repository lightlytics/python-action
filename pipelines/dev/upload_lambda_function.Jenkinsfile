pipeline {
   agent {label 'master'}

   stages {
      stage("notify  - started ") {
            steps {
               slack_send()
            }
      }
      
      stage('CheckOut From GitHub - lightlytics ') {
         steps {
            dir('lightlytics') {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics.git']]])
            }
         }
      }

      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }
  

      stage('Update lambda functions') {
         steps {
            sh  'echo "Lightlytics lambdas"'
            sh '''
                #!/bin/bash
                    echo "Who I'm $SHELL"
                    echo "Current Path $PATH"
                    cd lightlytics/lambda_functions && make build && make pkg
            '''
         }
      }
   }

}

def get_build_runner() {
      wrap([$class: 'BuildUser']) {
         return BUILD_USER_ID
   }
}

def slack_send() {
    USER = get_build_runner()
   slack_message = "Build Started: JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
    slack_message = "${slack_message} BUILD_USER: ${USER}"

   slackSend channel: 'jenkins-builds', color: "#439FE0", message: "${slack_message}"
}

