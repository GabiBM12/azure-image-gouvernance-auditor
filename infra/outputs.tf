output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.func.name
}

output "storage_account_name" {
  value = azurerm_storage_account.sa.name
}

output "reports_container_name" {
  value = azurerm_storage_container.reports.name
}

output "managed_identity_principal_id" {
  value = azurerm_linux_function_app.func.identity[0].principal_id
}