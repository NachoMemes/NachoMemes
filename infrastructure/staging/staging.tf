# Set AWS Provider, all options will be read from ENV
provider "aws" {}

# Sets a variable input for the public key used later for ansible
variable "public_key" {
  type = string
}

# Basic VPC with a /24 block
resource "aws_vpc" "staging-vpc" {
  cidr_block = "10.0.0.0/24"
}

# Should only need a single subnet
resource "aws_subnet" "staging-subnet" {
  vpc_id     = "${aws_vpc.staging-vpc.id}"
  cidr_block = "10.0.0.0/24"
  map_public_ip_on_launch = "true"
}

# HTTPS security group
resource "aws_security_group" "allow_https" {
  name        = "Allow_https"
  description = "Allow HTTPS traffic"
  vpc_id      = "${aws_vpc.staging-vpc.id}"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for pinging
resource "aws_security_group" "accept_ping" {
  name        = "accept_ping"
  description = "Allow Pinging the instance"
  vpc_id      = "${aws_vpc.staging-vpc.id}"
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
     from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

# Route table to get in and out
resource "aws_route_table" "rtb_public" {
  vpc_id = "${aws_vpc.staging-vpc.id}"
  route {
      cidr_block = "0.0.0.0/0"
      gateway_id = "${aws_internet_gateway.gw.id}"
  }

}

#Associate route table with our subnet
resource "aws_route_table_association" "rta_subnet_public" {
  subnet_id      = "${aws_subnet.staging-subnet.id}"
  route_table_id = "${aws_route_table.rtb_public.id}"
  
}


# Allow SSH access for ansible. Ideally in the future this should be limited to Azure IPs for CI
resource "aws_security_group" "allow_ssh" {
  name        = "allow_ssh"
  description = "Allow SSH Traffic"
  vpc_id      = "${aws_vpc.staging-vpc.id}"

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }
}

# Static IP address
resource "aws_eip" "ip" {
  instance = "${aws_instance.nachomeme.id}"
  vpc      = true
}

# Find the right Ubuntu AMI. Default username is 'ubuntu'
data "aws_ami" "latest-ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] #Canonical


}
resource "aws_internet_gateway" "gw" {
  vpc_id = "${aws_vpc.staging-vpc.id}"
}

resource "aws_key_pair" "deploy-key" {
  key_name = "deploy-key"
  public_key = var.public_key
}


# Main EC2 instance
resource "aws_instance" "nachomeme" {
  ami                    = "${data.aws_ami.latest-ubuntu.id}"
  instance_type          = "t2.micro"
  vpc_security_group_ids = ["${aws_security_group.allow_https.id}", "${aws_security_group.allow_ssh.id}", "${aws_security_group.accept_ping.id}"]
  subnet_id              = "${aws_subnet.staging-subnet.id}"
  key_name = "${aws_key_pair.deploy-key.key_name}"
}

# Output static IP to the console for ansible
output "public_ip" {
  value = aws_eip.ip.public_ip
}
