# Example: RELEASE=staging make template

RELEASE ?= test
template:
	echo "creating template for release - $(RELEASE)"
	helm template --namespace $(RELEASE) $(RELEASE) . --debug --output-dir template-test -f ./values/dev-values.yaml
	echo "created template for release - $(RELEASE)"

prod-template:
	echo "creating template for release - prod"
	helm template --namespace prod prod -f production-values.yaml . --debug --output-dir template-test
	echo "created template for release - prod"

BUILD_NUM ?= 99999
deploy-to-production:
	helm upgrade --install prod . --set deployment.branchName=master --set deployment.buildNumber=$(BUILD_NUM) --create-namespace -f ./production-values.yaml --create-namespace -n prod