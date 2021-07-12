pipeline {
    agent { label 'master' }
    triggers {
        cron('0 0 * * 0')
    }

    stages {
        stage('CheckOut From GitHub - lightlytics ') {
            steps {
                dir('lightlytics') {
                    checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics.git']]])
                }
            }
        }

        stage('run update aws cidr service') {
            steps {
              dir('lightlytics') {
                script {
                  sh "python -u shared/cidr/update_aws_cidr_map.py"
                }
              }
            }
        }
        stage('Update GIT') {
          steps {
            script {
            dir('lightlytics') {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                  withCredentials([usernamePassword(credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                      def encodedPassword = URLEncoder.encode("$GIT_PASSWORD",'UTF-8')
                      sh "git config --global user.email devops@lightlytics.com"
                      sh "git config --global user.name lightlyticsDevops"
                      sh "git add ."
                      sh "git commit -m 'Update AWS cidr by jenkins - build_number: ${env.BUILD_NUMBER}'"
                      sh "git push --force https://${GIT_USERNAME}:${encodedPassword}@github.com/lightlytics/lightlytics.git HEAD:master"
                  }
                }
            }

            }
          }
        }
    }
}

