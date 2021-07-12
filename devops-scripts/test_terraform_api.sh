##### Constants
URL="http://miko-ingress.lightlytics.com/terraform/plan"
TOKEN="abc"
####
echo "Posting terraform plan to Lightlytics"
echo $1 > /tmp/body.json
curl -d @/tmp/body.json  -X POST $URL \
    -H "Content-Type: application/json" \
    -H $TOKEN \
    -H "role: TERRAFORM_ONLY" \
    -H "customer_id: 111" \
    -H "external_account_id: 222"