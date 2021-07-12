#!/bin/bash -ex

function usage() {
  echo "usage: lightlytics_helm.sh --RELEASE_NAME <RELEASE_NAME> --NAMESPACE <NAMESPACE> --BRANCH <BRANCH> --VERSION <VERSION>"
}

function deployment_exists() {
  output_lines=$(helm list --filter "${NAMESPACE}" -n "${NAMESPACE}" | tail -n +2 | wc -l)
  if [[ ${output_lines} -eq 1 ]]; then
    true
  else
    false
  fi
}

function helm_dep_up() {
  pushd charts/deployment-main &>/dev/null
  helm dep up
  popd &>/dev/null
}

function install_demo_release() {
  helm upgrade --install "${NAMESPACE}" charts/deployment-main -f charts/deployment-main/values/dev-values.yaml --create-namespace \
    --set mongodb.enabled=true --set mongodb.mongodbRootPassword="${mongo_password}" --set neo4j.enabled=true --set neo4j.neo4jPassword="${neo4j_password}" \
    --set deployment.branchName="${BRANCH}" --set deployment.buildNumber="${VERSION}" --set deployment.env.Environment="${ENV}" --set deployment.env.ENV="${ENV}" --set deployment.env.ARCH="multi" -n "${NAMESPACE}" --timeout 2000s
  kubectl label namespaces "${NAMESPACE}" environment=demo --overwrite
  deployment_instructions
}

function install_staging_release() {
  helm upgrade --install "${NAMESPACE}" charts/deployment-main -f charts/deployment-main/values/dev-values.yaml --create-namespace \
    --set deployment.branchName="${BRANCH}" --set deployment.buildNumber="${VERSION}" --set deployment.env.Environment="${ENV}" \
    --set deployment.env.ENV="${ENV}" --set deployment.env.ARCH="multi" -n "${NAMESPACE}" --timeout 2000s
  kubectl label namespaces "${NAMESPACE}" environment=staging --overwrite
  deployment_instructions
}

function install_release() {
  helm_dep_up
  if [[ "$(echo "${ENV}" | tr '[:upper:]' '[:lower:]')" == "$(echo "Demo" | tr '[:upper:]' '[:lower:]')" ]]; then
    install_demo_release
  elif [[ "$(echo "${ENV}" | tr '[:upper:]' '[:lower:]')" == "$(echo "staging" | tr '[:upper:]' '[:lower:]')" ]]; then
    install_staging_release
  else
    echo "Unknown ENV type - exit"
    exit 1
  fi

}

function generate_password() {
  password=$(date | md5sum | awk '{print $1}')
  echo "${password}"
}

function generate_keys() {
  /usr/bin/ssh-keygen -t rsa -b 4096 -m PEM -f "${ENV}"-"${NAMESPACE}".key -q -N ""
  openssl rsa -in "${ENV}"-"${NAMESPACE}".key -pubout -outform PEM -out "${ENV}"-"${NAMESPACE}".key.pub
}

function create_demo_secrets() {
  region="us-east-1"
  mongo_password=$(generate_password)
  aws secretsmanager create-secret --region ${region} --name "${NAMESPACE}"/mongo --secret-string "{\"username\":\"root\",\"password\": \"${mongo_password}\"}"
  neo4j_password=$(generate_password)
  aws secretsmanager create-secret --region ${region} --name "${NAMESPACE}"/neo4j --secret-string "{\"username\":\"neo4j\",\"password\": \"${neo4j_password}\"}"
  #genrate private/public keys for the access token
  generate_keys
  aws secretsmanager create-secret --region ${region} --name "${NAMESPACE}"/access_token_private_key --secret-string file://"${ENV}"-"${RELEASE_NAME}".key
  aws secretsmanager create-secret --region ${region} --name "${NAMESPACE}"/access_token_public_key --secret-string file://"${ENV}"-"${RELEASE_NAME}".key.pub
  rm -rf "${ENV}"-"${NAMESPACE}".key*
}

function delete_demo_secrets() {
  aws secretsmanager delete-secret --secret-id "${NAMESPACE}"/mongo --force-delete-without-recovery
  aws secretsmanager delete-secret --secret-id "${NAMESPACE}"/neo4j --force-delete-without-recovery
  aws secretsmanager delete-secret --secret-id "${NAMESPACE}"/access_token_private_key --force-delete-without-recovery
  aws secretsmanager delete-secret --secret-id "${NAMESPACE}"/access_token_public_key --force-delete-without-recovery
}

function delete_helm_release() {
  helm delete "${NAMESPACE}" -n "${NAMESPACE}"
}

function delete_namespace() {
  kubectl delete namespaces "${NAMESPACE}"
}

function deployment_instructions() {
  echo "#######################################################"
  echo "Congratulations on setting up Lightlytics ENV!!"
  echo "front-end: http://${NAMESPACE}.lightops.io"
  echo "front-gate graphql api: http://${NAMESPACE}.lightops.io/graphql"
  echo "collection api: http://${NAMESPACE}.lightops.io/api/v1/flowlogs"
  echo "ingress: http://${NAMESPACE}-ingress.lightops.io"
  echo "#######################################################"
}

#####MAIN#####
ACTION="install"
RELEASE_NAME="None"
NAMESPACE="default"
BRANCH="master"
VERSION="latest"
ENV="prod"

while [ "$1" != "" ]; do
  case $1 in
  -r | --release_name)
    shift
    RELEASE_NAME=$1
    ;;

  -t | --tag)
    shift
    TAG=$(echo "${1}" | awk -F, '{print $1}')
    ;;

  -e | --environment)
    shift
    ENV=$(echo "$1" | tr '[:upper:]' '[:lower:])')
    echo "GOT ENV ${ENV}"
    ;;

  -a | --action)
    shift
    ACTION=$1
    ;;

  -h | --help)
    usage
    exit 1
    ;;
  *)
    usage
    exit 1
    ;;
  esac
  shift
done
NAMESPACE=${RELEASE_NAME}
echo "NAMESPACE TO DEPLOY: ${NAMESPACE}"
echo "ACTION TO RUN: ${ACTION}"

if [[ ${ACTION} == "install" ]]; then
  BRANCH=$(echo "${TAG}" | awk -F. '{print $1}')
  VERSION=$(echo "${TAG}" | awk -F. '{print $2}')
  echo "BRANCH - ${BRANCH} - VERSION ${VERSION}"
  if ! deployment_exists && [ "${ENV}" == "demo" ]; then
    create_demo_secrets
  fi
  install_release

elif [[ ${ACTION} == "delete" ]]; then
  if deployment_exists && [ "${ENV}" == "demo" ]; then
    delete_helm_release
    delete_demo_secrets
    delete_namespace
  fi

else
  echo "Unknown ACTION - exit"
  exit 1
fi
