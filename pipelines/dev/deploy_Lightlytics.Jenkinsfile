pipeline {
   agent {label 'master'}

   parameters {
         string(name: 'ReleaseName', defaultValue: '', description: 'Helm release name - Install new one if not exists')
   }
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
               sh "sudo bash -e ./devops-scripts/build_lightlytics/lightlytics_helm.sh --release_name ${ReleaseName} --tag ${Tag} --environment demo"
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

