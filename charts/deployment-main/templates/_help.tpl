{{/*
define ECR url based on the AWS account
*/}}
{{- define "ecrUrl" -}}
    {{- .Values.deployment.env.AWS_ACCOUNT -}}.dkr.ecr.us-east-1.amazonaws.com
{{- end -}}
