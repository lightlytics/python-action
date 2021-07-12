pipeline {
   agent {label 'master'}

   stages {
      stage('CheckOut From GitHub - lightlytics-devops ') {
            steps {
               checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
            }
      }
       stage('chmod file') {
            steps {
               sh "chmod 700 ./ansible_2ng/Lightlytics.pem"
            }
      }
      stage('Run playbook install neo4j plugin') {
            steps {
               sh '''ansible-playbook --private-key=./ansible_2ng/Lightlytics.pem ./ansible_2ng/playbooks/neo4j/neo4j-plugin-installation.yaml -i ./ansible_2ng/playbooks/group_vars/staging.yml'''
            }
      }

   }
}
