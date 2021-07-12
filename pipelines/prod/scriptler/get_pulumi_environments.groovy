import groovy.json.JsonSlurper;
try {
    def b = new StringBuffer()
    def cmd = ["/usr/sbin/pulumi", "stack", "ls", "--json"]
    def processBuilder=new ProcessBuilder(cmd)
    processBuilder.directory(new File("/var/lib/jenkins/lightlytics-devops/pulumi/lightlytics-environments"))
    def process = processBuilder.start()
    process.consumeProcessErrorStream(b)
    def data = new JsonSlurper().parseText(process.text)
    def pulumi_stacks = []
    data.each {
        pulumi_stacks.push("$it.name")
    }
    return pulumi_stacks
}

catch(Exception ex){
    print ex
}