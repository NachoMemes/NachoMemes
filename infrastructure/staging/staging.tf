# Set AWS Provider, all options will be read from ENV
provider "aws" { }

# Need a VPC, subnet, interface, eip, security group

resource "aws_vpc" "staging-vpc" {
cidr_block = "10.0.0.0/24"
}

resource "aws_subnet" "staging-subnet" {
  vpc_id = "${aws_vpc.staging-vpc0}"
  cidr_block = "10.0.0.0/24"
}

resource "aws_security_group" "allow_https" {
  name = "Allow_https"
  description = "Allow HTTPS traffic"
  vpc_id = "${aws_vpc.staging-vpc}"

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Ideally in the future this should be limited to Azure IPs for CI
resource "aws_security_group" "allow_ssh" {
  name = "allow_ssh"
  description = "Allow SSH Traffic"
  vpc_id = "${aws_vpc.staging-vpc}"

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
  }

  egress {
    from_port = 22
    to_port = 22
    protocol = "tcp"

  }
}
resource "aws_instance" "nachomeme" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

resource "aws_eip" "ip" {
  instance = "${aws_instance.nachomeme.id}"
  vpc = true
}


resource "aws_instance" "nachomeme" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  vpc_security_group_ids = ["${aws_security_group.allow_https}", "${aws_security_group.allow_ssh}"]
  subnet_id = "${aws_subnet.staging-subnet}"
}