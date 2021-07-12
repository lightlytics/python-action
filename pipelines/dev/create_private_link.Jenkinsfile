pipeline {
   agent {label 'master'}

   stages {
      stage("notify  - started ") {
            steps {
               slack_send()
            }
      }

      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
            checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }
      stage('Create Private link') {
            steps {
               sh "python -u ./devops-scripts/build_lightlytics/create_endpoint_service.py --release ${ReleaseName} --environment staging --regions ${aws_regions}"
            }
      }
   }
 }

def slack_send() {
   slack_message = "Build Started: JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
    wrap([$class: 'BuildUser']) {
      slack_message = "${slack_message} BUILD_USER: ${BUILD_USER_ID}"
    }
   slackSend channel: 'jenkins-builds', color: "#439FE0", message: "${slack_message}"
}

