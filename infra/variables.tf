variable "location" {
  type    = string
  default = "westeurope"
}

variable "name_prefix" {
  description = "Neutral prefix used for naming. Do not include personal names."
  type        = string
  default     = "azimg-governance-dev"
}

variable "subscription_id_to_scan" {
  description = "Single subscription ID this Function should scan."
  type        = string
}

variable "schedule_cron" {
  description = "Azure Functions NCRONTAB (6 fields). Runs in UTC."
  type        = string
  default     = "0 0 7 * * *" # 07:00 UTC daily
}

variable "tags" {
  type = map(string)
  default = {
    project   = "azure-image-governance-auditor"
    milestone = "2"
  }
}

variable "plan_sku" {
  description = "App Service Plan SKU"
  type        = string
  default     = "Y1"
}