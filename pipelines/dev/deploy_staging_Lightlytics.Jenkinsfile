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
      stage('Run deployment') {
            steps { 
               sh "sudo bash -e ./devops-scripts/build_lightlytics/lightlytics_helm.sh --release_name staging --tag ${Tag} --environment staging"
            }
      }
   }
 }

def get_build_runner() {
   try{
        wrap([$class: 'BuildUser']) {
            return BUILD_USER_ID
        }
   }
   catch(Exception e) {
      return "unknown"
   }
}

def slack_send() {
   USER = get_build_runner()
   slack_message = "Build Started: JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
   wrap([$class: 'BuildUser']) {
      slack_message = "${slack_message} BUILD_USER: ${USER}"
    }
   slackSend channel: 'jenkins-builds', color: "#439FE0", message: "${slack_message}"
}

