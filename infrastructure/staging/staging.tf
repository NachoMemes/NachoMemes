provider "aws" {
  profile    = "default"
  region     = var.aws_region
}

resource "aws_instance" "nachomeme" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}