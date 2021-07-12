# Jenkins

# NOTE:

THIS IS AN EXPERIMENT FOR FUTURE RELEASE

https://github.com/jenkinsci/helm-charts
https://github.com/jenkinsci/helm-charts/blob/main/charts/jenkins/README.md

## Install

```shell
helm repo add jenkinsci https://charts.jenkins.io
helm repo update

# The helm charts in the Jenkins repo can be listed with the command:

helm search repo jenkinsci


helm upgrade --install jenkins jenkinsci/jenkins --create-namespace -n jenkins
```

## Usage

NOTES:

1. Get your 'admin' user password by running:
   kubectl exec --namespace jenkins -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/chart-admin-password && echo
   -- `9b70x5jw044zzaMTSugLF8`
2. Get the Jenkins URL to visit by running these commands in the same shell:
   echo http://127.0.0.1:8080
   kubectl --namespace jenkins port-forward svc/jenkins 8080:8080

3. Login with the password from step 1 and the username: admin
4. Configure security realm and authorization strategy
5. Use Jenkins Configuration as Code by specifying configScripts in your values.yaml file, see documentation: http:
   ///configuration-as-code and examples: https://github.com/jenkinsci/configuration-as-code-plugin/tree/master/demos

For more information on running Jenkins on Kubernetes, visit:
https://cloud.google.com/solutions/jenkins-on-container-engine

For more information about Jenkins Configuration as Code, visit:
https://jenkins.io/projects/jcasc/
