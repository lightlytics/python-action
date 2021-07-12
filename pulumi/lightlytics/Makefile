git-pull:
	git pull
run: git-pull
	pulumi stack up
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