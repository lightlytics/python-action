# Helm

# Install Repos

helm repo add stable https://charts.helm.sh/stable
helm repo add incubator https://charts.helm.sh/incubator
helm repo update

# Deploy Prod (DO NOT RUN IT UNLESS YOU KNOW WHAT YOU ARE DOING)

```shell
make deploy-to-prod
```
