##https://app.logz.io/#/dashboard/data-sources/Kubernetes-overHelm##
helm repo add logzio-helm https://logzio.github.io/logzio-helm/filebeat
helm install --namespace="kube-system" -f values/<release>-production-values.yaml --set-file filebeatConfig.autoCustomConfig=payload/filebeat.yaml logzio-k8s-logs logzio-helm/logzio-k8s-logs
