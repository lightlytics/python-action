https://github.com/godaddy/kubernetes-external-secrets
https://github.com/aws-samples/aws-secret-sidecar-injector/issues
https://gist.github.com/lukaszbudnik/f1f42bd5a57430e3c25034200ba44c2e

1. helm repo add external-secrets https://external-secrets.github.io/kubernetes-external-secrets/
1. helm repo update
1. To run:
```shell script
helm upgrade --install kubernetes-external-secrets external-secrets/kubernetes-external-secrets --skip-crds --set securityContext.fsGroup=65534 -f values/<release>-production-values.yaml
```


How To Use e.g. :
aws secretsmanager create-secret --name hello-service/password --secret-string "1234"

hello-service-external-secret.yml:
#####################################
apiVersion: 'kubernetes-client.io/v1'
kind: ExternalSecret
metadata:
  name: hello-service
spec:
  backendType: systemManager
  data:
    - key: /hello-service/password
      name: password
#####################################

