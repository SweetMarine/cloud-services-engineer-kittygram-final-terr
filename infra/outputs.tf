output "vm_name" {
  value       = yandex_compute_instance.kittygram_vm.name
  description = "Name of the provisioned VM"
}

output "vm_external_ip" {
  value       = yandex_compute_instance.kittygram_vm.network_interface[0].nat_ip_address
  description = "Public IPv4 address of the VM"
}

output "vm_internal_ip" {
  value       = yandex_compute_instance.kittygram_vm.network_interface[0].ip_address
  description = "Internal IPv4 address of the VM"
}

output "vm_fqdn" {
  value       = yandex_compute_instance.kittygram_vm.fqdn
  description = "FQDN of the VM"
}