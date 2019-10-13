provider "aws" {
    region = "us-east-1"
}


resource "aws_vpc" "nachome-staging-vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "nachomeme-staging-subnet" {
    vpc_id = "${aws_vpc.nachome-staging-vpc}"
    cidr_block = "10.0.1.0/24"
}

resource "aws_network_interface" "interface" {
    subnet_id = "${aws_subnet.nachomeme-staging-subnet}"
    private_ips = ["10.0.1.100"]
}
resource "aws_internet_gateway" "gw" {
    vpc_id = "${aws_vpc.nachome-staging-vpc}"
  
}

resource "aws_key_pair" "deployer" {
    key_name = "deployer-key"
    public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGJA+ZGcXO6UTyiryCUOYSRpyHcj5wRftjb07xFnHuUtGyW4a47CrM0fM8mmCU+yEfP/w2P3DN2lS3rSaUNBCKa27HEh3UJ9znOkYOm/+KMnA7xUSAFQ1kbJxtzTU8SzzhGCMgw1CssST3x0jHiYQfdjT0h+NFztTpyocenHwNy9fp+A5Wt9dmaY3bujvJxQyYiyJ5THcY8+1TLJUvOJwtdIdXy14vUmpjfnrhEpegENG7LcjkCTSO/k7wkGO1lxvP3D4FsgF3GAtwNJ9GtMsaD4zBMRYX2PRuGHUZeBTJ97GzEvkMnlvLOYx1hsGh9COQ4yvtU+7sRIyPrjOnbaNH sam@Spartan.local"
}


resource "aws_instance" "nachomeme-staging" {
    depends_on = ["${aws_internet_gateway.gw}"]
  ami           = "ami-0607bfda7f358db2f"
  instance_type = "t2.micro"

  network_interface {
      network_interface_id = "${aws_network_interface.interface.id}"
      device_index = 0
  }
  
  tags = {
      Name = "nachomeme-staging"
  }
}
resource "aws_eip" "lb" {
    instance = "${aws_instance.nachomeme-staging}"
    vpc = true
}



output "IP" {
  value = "nachomeme-staging.public_ip"
}

