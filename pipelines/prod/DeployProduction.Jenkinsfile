pipeline {
   agent {label 'slave'}

   stages {
      stage('CheckOut From GitHub - lightlytics devops ') {
         steps {
            checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'e2be5b21-e679-4dbf-9c18-945353131920', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
         }
      }
      stage('Run deployment') {
            steps {
               sh "python devops-scripts/prod/production_deployment.py --environment ${ProdEnvironment} --run_lightlytics_chart --branch_and_build ${BranchAndBuild}"
            }
      }
      stage('Tag Build') {
        steps {
          script {
              manager.addShortText(
                params.ProdEnvironment + "-" + params.BranchAndBuild
              )
          }
        }
      }
   }
    post {
       success {
            slack_send()
       }
       always {
          archiveArtifacts allowEmptyArchive: true, artifacts: 'charts/deployment-main/values/*-production-values.yaml', followSymlinks: false
       }
    }
 }

def slack_send() {
   slack_message = "Deployment Success: environment: ${params.ProdEnvironment}, BUILD_NUMBER:${params.BranchAndBuild} \n"
   slackSend channel: 'general', color: "#439FE0", message: "${slack_message}"
}

