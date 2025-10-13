# 🔑 Key Management Service Patterns (`key_management`)

## Client Creation

```python
kms_client = get_client('key_management', oci_config)
```

## Common Patterns

### 1. List Vaults

```python
for compartment in all_compartments:
    try:
        response = kms_client.list_vaults(compartment_id=compartment.id)
        for vault in response.data:
            results.append(to_dict(vault))

        while response.has_next_page:
            response = kms_client.list_vaults(compartment_id=compartment.id, page=response.next_page)
            for vault in response.data:
                results.append(to_dict(vault))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Vaults by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = kms_client.list_vaults(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for vault in response.data:
            results.append(to_dict(vault))

        while response.has_next_page:
            response = kms_client.list_vaults(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for vault in response.data:
                results.append(to_dict(vault))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Keys

```python
vault_id = "ocid1.vault.oc1..."  # or from plan parameters

try:
    response = kms_client.list_keys(vault_id=vault_id)
    for key in response.data:
        results.append(to_dict(key))

    while response.has_next_page:
        response = kms_client.list_keys(vault_id=vault_id, page=response.next_page)
        for key in response.data:
            results.append(to_dict(key))
except oci.exceptions.ServiceError:
    pass  # Vault not found or no access
```

### 4. List Keys by Lifecycle State

```python
vault_id = "ocid1.vault.oc1..."  # or from plan parameters
lifecycle_state = "ENABLED"  # or from plan parameters

try:
    response = kms_client.list_keys(vault_id=vault_id)
    for key in response.data:
        if key.lifecycle_state == lifecycle_state:
            results.append(to_dict(key))

    while response.has_next_page:
        response = kms_client.list_keys(vault_id=vault_id, page=response.next_page)
        for key in response.data:
            if key.lifecycle_state == lifecycle_state:
                results.append(to_dict(key))
except oci.exceptions.ServiceError:
    pass  # Vault not found or no access
```

### 5. List Key Versions

```python
key_id = "ocid1.key.oc1..."  # or from plan parameters

try:
    response = kms_client.list_key_versions(key_id=key_id)
    for version in response.data:
        results.append(to_dict(version))

    while response.has_next_page:
        response = kms_client.list_key_versions(key_id=key_id, page=response.next_page)
        for version in response.data:
            results.append(to_dict(version))
except oci.exceptions.ServiceError:
    pass  # Key not found or no access
```

### 6. List Key Versions by State

```python
key_id = "ocid1.key.oc1..."  # or from plan parameters
lifecycle_state = "ENABLED"  # or from plan parameters

try:
    response = kms_client.list_key_versions(key_id=key_id)
    for version in response.data:
        if version.lifecycle_state == lifecycle_state:
            results.append(to_dict(version))

    while response.has_next_page:
        response = kms_client.list_key_versions(key_id=key_id, page=response.next_page)
        for version in response.data:
            if version.lifecycle_state == lifecycle_state:
                results.append(to_dict(version))
except oci.exceptions.ServiceError:
    pass  # Key not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Keys require a specific vault ID
- Key versions require a specific key ID
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- KMS resources are compartment-scoped


