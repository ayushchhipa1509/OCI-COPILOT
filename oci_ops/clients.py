# oci_ops/clients.py
from typing import Dict, Any
import oci

# This map ensures only known, approved clients can be created.
# Comprehensive list of OCI services for maximum coverage.
ALLOWED_CLIENTS = {
    # Identity & Security Services
    "identity": oci.identity.IdentityClient,
    "cloudguard": oci.cloud_guard.CloudGuardClient,
    "vulnerability_scanning": oci.vulnerability_scanning.VulnerabilityScanningClient,
    "threat_intelligence": oci.threat_intelligence.ThreatintelClient,
    "key_management": oci.key_management.KmsManagementClient,
    "kms_vault": oci.key_management.KmsVaultClient,
    "vault": oci.vault.VaultsClient,
    "secrets": oci.secrets.SecretsClient,
    "bastion": oci.bastion.BastionClient,
    "audit": oci.audit.AuditClient,
    "data_safe": oci.data_safe.DataSafeClient,

    # Core IaaS Services
    "compute": oci.core.ComputeClient,
    "blockstorage": oci.core.BlockstorageClient,
    "virtualnetwork": oci.core.VirtualNetworkClient,
    "loadbalancer": oci.load_balancer.LoadBalancerClient,
    "network_load_balancer": oci.network_load_balancer.NetworkLoadBalancerClient,

    # Storage Services
    "objectstorage": oci.object_storage.ObjectStorageClient,
    "file_storage": oci.file_storage.FileStorageClient,

    # Oracle Database Services
    "database": oci.database.DatabaseClient,
    "database_management": oci.database_management.DbManagementClient,
    "database_tools": oci.database_tools.DatabaseToolsClient,
    "golden_gate": oci.golden_gate.GoldenGateClient,
    "mysql": oci.mysql.DbSystemClient,
    "postgresql": oci.psql.PostgresqlClient,
    "nosql": oci.nosql.NosqlClient,

    # Analytics & AI Services
    "analytics": oci.analytics.AnalyticsClient,
    "bds": oci.bds.BdsClient,
    "data_catalog": oci.data_catalog.DataCatalogClient,
    "data_integration": oci.data_integration.DataIntegrationClient,
    "data_flow": oci.data_flow.DataFlowClient,
    "streaming": oci.streaming.StreamAdminClient,
    "data_science": oci.data_science.DataScienceClient,
    "ai_vision": oci.ai_vision.AIServiceVisionClient,
    "oda": oci.oda.OdaClient,

    # Monitoring and Management
    "monitoring": oci.monitoring.MonitoringClient,
    "apm_domain": oci.apm_control_plane.ApmDomainClient,
    "apm_synthetics": oci.apm_synthetics.ApmSyntheticClient,
    "apm_traces": oci.apm_traces.TraceClient,
    "budget": oci.budget.BudgetClient,
    "events": oci.events.EventsClient,
    "functions": oci.functions.FunctionsManagementClient,
    "healthchecks": oci.healthchecks.HealthChecksClient,
    "limits": oci.limits.LimitsClient,
    "quotas": oci.limits.QuotasClient,
    "log_analytics": oci.log_analytics.LogAnalyticsClient,
    "logging": oci.logging.LoggingManagementClient,
    "notifications": oci.ons.NotificationDataPlaneClient,
    "operations_insights": oci.opsi.OperationsInsightsClient,
    "queue": oci.queue.QueueAdminClient,
    "resource_manager": oci.resource_manager.ResourceManagerClient,
    "stack_monitoring": oci.stack_monitoring.StackMonitoringClient,

    # Networking Services
    "dns": oci.dns.DnsClient,
    "waas": oci.waas.WaasClient,
    "email": oci.email.EmailClient,

    # Cloud Advisor (Optimizer)
    "optimizer": oci.optimizer.OptimizerClient,

    # Container and DevOps
    "container_engine": oci.container_engine.ContainerEngineClient,
    "container_instances": oci.container_instances.ContainerInstanceClient,
    "devops": oci.devops.DevopsClient,

    # Application Integration
    "integration": oci.integration.IntegrationInstanceClient,

    # Blockchain
    "blockchain": oci.blockchain.BlockchainPlatformClient,

    # Other PaaS Services
    "service_catalog": oci.service_catalog.ServiceCatalogClient,
    "usage_api": oci.usage_api.UsageapiClient,

    # Legacy aliases for backward compatibility
    "regions": oci.identity.IdentityClient,
    "autonomous_database": oci.database.DatabaseClient,
    "advisor": oci.optimizer.OptimizerClient,
}


def get_client(service_name: str, config: Dict[str, Any]):
    """Gets an initialized OCI client for a given service."""
    client_class = ALLOWED_CLIENTS.get(service_name.lower())
    if not client_class:
        raise ValueError(
            f"Service '{service_name}' is not a supported client.")
    return client_class(config)


def build_config(oci_creds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds an OCI configuration dictionary from credentials.
    Supports both key_file path and key_content (pasted private key).
    Falls back to default OCI config file if credentials are incomplete.
    """
    import os
    import tempfile

    # Check if we have key_content (pasted private key)
    if 'key_content' in oci_creds and oci_creds['key_content']:
        # Create a temporary file for the private key
        temp_key_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.pem')
        temp_key_file.write(oci_creds['key_content'])
        temp_key_file.close()

        # Use the temporary file path
        key_file_path = temp_key_file.name
    elif 'key_file' in oci_creds and oci_creds['key_file']:
        key_file_path = oci_creds['key_file']
    else:
        key_file_path = None

    # Try to use provided credentials first
    if all(key in oci_creds and oci_creds[key] for key in ['tenancy', 'user', 'fingerprint', 'region']) and key_file_path:
        return {
            'tenancy': oci_creds['tenancy'],
            'user': oci_creds['user'],
            'fingerprint': oci_creds['fingerprint'],
            'key_file': key_file_path,
            'region': oci_creds['region']
        }

    # Fall back to default OCI config
    try:
        from oci.config import from_file
        return from_file()
    except Exception:
        # If no default config, try environment variables
        return {
            'tenancy': os.getenv('OCI_TENANCY', ''),
            'user': os.getenv('OCI_USER', ''),
            'fingerprint': os.getenv('OCI_FINGERPRINT', ''),
            'key_file': os.getenv('OCI_KEY_FILE', ''),
            'region': os.getenv('OCI_REGION', 'us-ashburn-1')
        }
