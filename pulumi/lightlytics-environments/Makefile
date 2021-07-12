git-pull:
	git pull
debug-run: git-pull
	pulumi stack up -d
get-stacks:
	pulumi stack ls
prod:
	pulumi stack select prod
show-secrets-conf:
	pulumi config --show-secrets
show-secrets-stack:
	pulumi stack --show-secrets
#make create-stack stack_name=<stack_name> external_region_list="<regionA> <regionB> .."
create-stack:
	pulumi stack init $(stack_name)
	cp 	Pulumi.template.yaml Pulumi.$(stack_name).yaml
	pulumi config set --secret lightlytics-environments:lightlyticsSupportPassword $(shell date +%s | sha1sum | base64 | cut -c1-14)
	pulumi config set --secret lightlytics-environments:neo4jPassword $(shell date +%s | sha1sum | base64 | cut -c14-28)
	pulumi config set --secret lightlytics-environments:mongoDbPassword $(shell date +%s | sha1sum | base64 | cut -c28-42)
	index=0; \
	for region in $(external_region_list); do \
	pulumi config set --path lightlytics-environments:externalRegions[$$index] $$region; \
	index=$(shell echo $$(($(index)+1))); \
	done


#make delete-stack stack_name=<stack_name>
delete-stack:
	pulumi stack rm $(stack_name)

#make run-stack stack_name=<stack_name>
run-stack:
	pulumi up --stack $(stack_name)
	pulumi stack output --stack $(stack_name) --json > outputs/$(stack_name)-output.json

#make output stack_name=<stack_name>
output-with-secrets:
	pulumi stack output --stack $(stack_name) --json --show-secrets > outputs/$(stack_name)-output.json

