pipeline {
    agent { label 'master' }

    stages {
        stage("notify  - started ") {
            steps {
                slack_send()
            }
        }

        stage('CheckOut From GitHub - lightlytics ') {
            steps {
                dir('lightlytics') {
                    checkout([$class: 'GitSCM', branches: [[name: '*/${Branch}']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics.git']]])
                }
            }
        }
        stage('CheckOut From GitHub - lightlytics devops ') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: 'master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '89019ef1-0bf8-44d4-806b-fe2fe2180348', url: 'https://github.com/lightlytics/lightlytics-devops.git']]])
            }
        }

        stage('Authenticate Docker client to registry') {
              steps {
                 sh "aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 219342927623.dkr.ecr.us-east-1.amazonaws.com"
              }
        }


        stage('Pre lightlytics build') {
            steps {
                script {
                    if (params.SkipTests) {
                        echo "Skip Pre lightlytics build"
                    } else {
                        sh "sudo python devops-scripts/build_lightlytics/pre_lightlytics_build.py --branch_name=${Branch} --build_number=${BUILD_NUMBER}"
                        sh "echo sleeping to make sure neo4j is up and ready for tests"; sleep 30; echo "sleep done"
                    }
                }
            }
        }

        stage('Build Docker Images') {
            environment {
                MicroServices_List = MicroServices.replaceAll(',', ' ')
            }
            steps {
                script {
                    if (params.SkipTests) {
                        sh "python -u devops-scripts/build_lightlytics/build_lightlytics.py --branch_name=${Branch} --build_number=${BUILD_NUMBER} --microservices ${MicroServices_List} --skip_test"
                    } else {
                        sh "python -u devops-scripts/build_lightlytics/build_lightlytics.py --branch_name=${Branch} --build_number=${BUILD_NUMBER} --microservices ${MicroServices_List}"
                    }
                }
            }
        }

        stage('Run demo deployment') {
            when { expression { return params.DeployDemoEnvironment } }
            steps {
                build job: 'Deploy Lightlytics Demo Environment', parameters: [
                        string(name: 'Tag', value: String.valueOf(Branch) + "." + String.valueOf(BUILD_NUMBER)),
                        string(name: 'ReleaseName', value: String.valueOf(DemoRelaseName))]
            }
        }

        stage('Run staging deployment') {
            when { expression { return params.DeployStagingEnvironment } }
            steps {
                build job: 'Deploy Lightlytics Staging environment', parameters: [
                        string(name: 'Tag', value: String.valueOf(Branch) + "." + String.valueOf(BUILD_NUMBER))
                ]
            }
        }
    }
    post {
        always {
            sh "sudo python devops-scripts/build_lightlytics/post_lightlytics_build.py --branch_name=${Branch} --build_number=${BUILD_NUMBER}"
        }
    }
}

def get_build_runner() {
    try {
        wrap([$class: 'BuildUser']) {
            return BUILD_USER_ID
        }
    }
    catch (Exception e) {
        return "unknown"
    }
}

def slack_send() {
    USER = get_build_runner()
    slack_message = "Build Started: JOB_NAME: ${env.JOB_NAME}, BUILD_NUMBER:${env.BUILD_NUMBER} \n"
    slack_message = "${slack_message} BUILD_USER: ${USER}"

    slackSend channel: 'jenkins-builds', color: "#439FE0", message: "${slack_message}"
}

