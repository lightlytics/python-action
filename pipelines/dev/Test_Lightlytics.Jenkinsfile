pipeline {
   agent {label 'master'}

   stages {
      stage("notify  - started ") {
            steps {
               slack_send_start()
            }
      }
      
      stage('CheckOut From GitHub - lightlytics ') {
         steps {
            dir('lightlytics') {
               checkout([$class: 'GitSCM', branches: [[name: '*/${ghprbSourceBranch}']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics.git']]])
            }
         }
      }
      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }


      stage('Pre lightlytics build') {
            steps {
               script {
                  sh "sudo python devops-scripts/build_lightlytics/pre_lightlytics_build.py --branch_name=${ghprbSourceBranch} --build_number=${BUILD_NUMBER}"
                  sh "echo sleeping to make sure neo4j is up and ready for tests"; sleep 40; echo "sleep done"
              }
         }
      }
      
      stage('Test Docker images') {
         environment {
            MicroServices_List = MicroServices.replaceAll(',', ' ')
         }
         steps {
            script {
               sh "python -u devops-scripts/build_lightlytics/build_lightlytics.py --branch_name=${ghprbSourceBranch} --build_number=${BUILD_NUMBER} --microservices ${MicroServices_List} --test_only"
            }
      }
   }

   }
   post {
      failure {
          slack_send_failure()
      }
      always {
         junit allowEmptyResults: true, testResults: 'reports/result*.xml'
         archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage/*.*', followSymlinks: false
         sh "sudo python devops-scripts/build_lightlytics/post_lightlytics_build.py --branch_name=${ghprbSourceBranch} --build_number=${BUILD_NUMBER}"
      }
   }

}

def get_build_runner() {
   if (params.ghprbActualCommitAuthor != null){
      return params.ghprbActualCommitAuthor
   }
   else {
      wrap([$class: 'BuildUser']) {
         return BUILD_USER_ID
   }
    }
}

def slack_send_start() {
    USER = get_build_runner()
   slack_message = "Build Started: JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
    slack_message = "${slack_message} BUILD_USER: ${USER}"

   slackSend channel: 'jenkins-builds', color: "#439FE0", message: "${slack_message}"
}

def slack_send_failure() {
    USER = get_build_runner()
   slack_message = "Failed : JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
    slack_message = "${slack_message} BUILD_USER: ${USER}"

   slackSend channel: 'jenkins-builds', color: "#E0434D", message: "${slack_message}"
}

