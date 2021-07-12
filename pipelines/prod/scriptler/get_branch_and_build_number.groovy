import groovy.json.JsonSlurper;
try {


    def cmd = ["/usr/bin/aws", "ecr", "describe-images", "--repository-name", "account", "--region", "us-east-1", "--query", "reverse(sort_by(imageDetails,& imagePushedAt))[*]"]
    def ecr_images_json = cmd.execute()

    def data = new JsonSlurper().parseText(ecr_images_json.text)

    def ecr_images = []
    data.each {
        ecr_images.push("$it.imageTags".replace("[", "").replace("]",""))
    }
    return ecr_images

}
catch(Exception ex){
    print ex
}