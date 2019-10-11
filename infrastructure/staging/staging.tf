provider "aws" {
  profile    = "default"
  region     = var.aws_region
}

resource "aws_ecs_service" "nachomeme" {
  name       = 
}