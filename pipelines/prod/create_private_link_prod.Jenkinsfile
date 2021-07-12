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
               sh "python devops-scripts/build_lightlytics/create_endpoint_service_prod.py --release ${ReleaseName} --environment production --regions ${aws_regions}"
            }
      }
   }
 }

