pipeline {
   agent {label 'master'}

   stages {
      stage('CheckOut From GitHub - graph-data-science-lightlytics ') {
            steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/graph-data-science-lightlytics.git']]])
            }
      }
      stage('Tests') {
            steps {
               sh ""
            }
      }
      stage('Compile') {
            steps {
               sh "./gradlew packaging:shadowJar"
            }
      }
      stage('Copy to s3') {
            steps {
               sh "aws s3 cp ./packaging/build/libs/neo4j-graph-data-science-1.4.0-*  s3://gds-lightlytics-jars/neo4j-graph-data-science-1.4.0-alpha06-standalone-${BUILD_NUMBER}.jar"
            }
      }
      stage('Run build_neo4j_docker_image') {
            when { expression { return params.build_neo4j_docker_image } }
            steps {
                build job: 'build_neo4j_docker_image'
            }
      }
      stage('Run deploy_neo4j_plugin') {
            when { expression { return params.'deploy_neo4j_plugin' } }
            steps {
                build job: 'deploy_neo4j_plugin'
            }
      }
   }
}
