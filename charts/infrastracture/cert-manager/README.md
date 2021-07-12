# Cert Manager & Cluster Issuer

- https://github.com/jetstack/cert-manager

## Guidelines

In order to enable automatic certificates in our cluster, we need to enable few resources and connection between them:

1. Cluster Issuer - In charge of communicating with LetsEncrypt through ACME DNS01(our case) challenge
1. Cert Manager - In charge of the "glue" between Ingress and Certificates issued by ClusterIssuer
1. Ingress Annotations and Configuration

Cert manager looks for annotations > requests form the cluster issuer to issue a certificate > requests a cert from
LetsEncrypt > requests ACME challenge from the issuer > Issuer solves the challenge > LetsEncrypt returns a cert >
Issuer delivers the cert > Cert manager gives it to the ingress > ingress-controller puts it to ALB / other reverse
proxy

**NOTE: this is not working automatically with ALB INGRESS CONTROLLER! - USE ACM with ALB INGRESS CONTROLLER OR use this
[ugly hack](https://github.com/kubernetes-sigs/aws-load-balancer-controller/issues/1084#issuecomment-725566515)  **

## Installation

Follow this:

- https://cert-manager.io/docs/installation/kubernetes/
- https://cert-manager.io/docs/configuration/acme/dns01/route53/

```shell
# Get cluster OIDC URL:
# https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html
aws eks describe-cluster --name <cluster_name> --query "cluster.identity.oidc.issuer" --output text
```

- see [policies dir](policies) for the trust relationship policy

## Deploy

To deploy you must run:

```shell
export CM_VERSION=v1.1.0
helm repo add jetstack https://charts.jetstack.io
helm repo update
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/${CM_VERSION}/cert-manager.crds.yaml
helm upgrade --install cert-manager jetstack/cert-manager --create-namespace --namespace cert-manager --set installCRDs=true --recreate-pods --version ${CM_VERSION} -f ./dev-values.yaml
#helm upgrade --install cert-manager jetstack/cert-manager --create-namespace --namespace cert-manager --version v1.1.0 -f ./production-values.yaml
# CLUSTER ISSUERS CAN'T BE INSTALLED WITHOUT CRDs
kubectl apply -f cluster-issuer.yaml
```   
