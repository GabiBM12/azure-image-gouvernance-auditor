resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

locals {
  # Azure naming constraints:
  # - Storage account: 3-24 chars, lowercase letters and numbers only
  # - Function app name: can include hyphens, but keep it short
  base_compact = lower(replace(var.name_prefix, "/[^a-z0-9]/", ""))
  sa_name      = substr("${local.base_compact}${random_string.suffix.result}", 0, 24)
  rg_name      = "${var.name_prefix}-rg"
  func_name    = "${var.name_prefix}-func-${random_string.suffix.result}"
  ai_name      = "${var.name_prefix}-ai-${random_string.suffix.result}"
}

resource "azurerm_resource_group" "rg" {
  name     = local.rg_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "sa" {
  name                     = local.sa_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"

  tags = var.tags
}

resource "azurerm_storage_container" "reports" {
  name                  = "reports"
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

resource "azurerm_service_plan" "plan" {
  name                = "${var.name_prefix}-plan-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  os_type  = "Linux"
  sku_name = var.plan_sku

  tags = var.tags
}

resource "azurerm_application_insights" "ai" {
  name                = local.ai_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  tags                = var.tags
}

resource "azurerm_linux_function_app" "func" {
  name                = local.func_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    # Functions runtime
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "AzureWebJobsFeatureFlags" = "EnableWorkerIndexing"

    # App Insights
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = azurerm_application_insights.ai.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.ai.connection_string

    # Our app config (env vars)
    "AZIMG_SUBSCRIPTIONS"     = var.subscription_id_to_scan
    "AZIMG_STORAGE_ACCOUNT"   = azurerm_storage_account.sa.name
    "AZIMG_STORAGE_CONTAINER" = azurerm_storage_container.reports.name
    "AZIMG_STORAGE_PREFIX"    = "vm_inventory/"
    "AZIMG_TIMER_SCHEDULE"    = var.schedule_cron
    "AZIMG_DEBUG"             = "0"
  }

  tags = var.tags
}

# RBAC: Function MI can read resources in the target subscription
resource "azurerm_role_assignment" "mi_reader" {
  scope                = "/subscriptions/${var.subscription_id_to_scan}"
  role_definition_name = "Reader"
  principal_id         = azurerm_linux_function_app.func.identity[0].principal_id
}

# RBAC: Function MI can upload blobs to the report storage account
resource "azurerm_role_assignment" "mi_blob_contrib" {
  scope                = azurerm_storage_account.sa.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.func.identity[0].principal_id
}