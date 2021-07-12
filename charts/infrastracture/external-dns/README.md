# External DNS

## Info

https://github.com/kubernetes-sigs/external-dns
https://github.com/helm/charts/tree/master/stable/external-dns

## Install 

helm repo add bitnami https://charts.bitnami.com/bitnami
helm dep up

## Deployment

# Prod Cluster(s):

helm upgrade --install external-dns-prod --recreate-pods -f values/<release>-production-values.yaml bitnami/external-dns

# Dev Cluster:

helm upgrade --install external-dns-prod --recreate-pods -f dev-values.yaml bitnami/external-dns
