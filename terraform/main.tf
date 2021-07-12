provider "aws" {
  region = "us-east-1"
  access_key = "AKIATGEO3O4DVHG4BYW4"
  secret_key = "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"
}
resource "aws_network_interface" "test_interface_1" {
    subnet_id = "subnet-0068f3bc61736553f"
	security_groups = ["sg-01d2aeaa2fb86873d"]
}
resource "aws_instance" "test-instance_pub" {
    ami = "ami-00ddb0e5626798373"
	instance_type = "t2.micro"
	network_interface {
      network_interface_id = aws_network_interface.test_interface_1.id
      device_index         = 0
  }
  associate_public_ip_address = true
}
