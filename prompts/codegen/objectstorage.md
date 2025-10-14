# 🪣 Object Storage Service Patterns (`objectstorage`)

## Client Creation

```python
objectstorage_client = get_client('objectstorage', oci_config)
# CRITICAL: Always fetch namespace dynamically
namespace = objectstorage_client.get_namespace().data
```

## Common Patterns

### 1. List All Buckets

```python
for compartment in all_compartments:
    try:
        response = objectstorage_client.list_buckets(
            namespace_name=namespace,
            compartment_id=compartment.id
        )
        for bucket in response.data:
            results.append(to_dict(bucket))

        while response.has_next_page:
            response = objectstorage_client.list_buckets(
                namespace_name=namespace,
                compartment_id=compartment.id,
                page=response.next_page
            )
            for bucket in response.data:
                results.append(to_dict(bucket))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Empty Buckets (Multi-step with Performance Optimization)

```python
for compartment in all_compartments:
    try:
        # Get ALL buckets in the compartment
        response = objectstorage_client.list_buckets(
            namespace_name=namespace,
            compartment_id=compartment.id
        )
        all_buckets = response.data
        while response.has_next_page:
            response = objectstorage_client.list_buckets(
                namespace_name=namespace,
                compartment_id=compartment.id,
                page=response.next_page
            )
            all_buckets.extend(response.data)

        # Check each bucket for emptiness (optimized with limit=1)
        for bucket in all_buckets:
            try:
                objects_response = objectstorage_client.list_objects(
                    namespace_name=namespace,
                    bucket_name=bucket.name,
                    limit=1  # CRITICAL PERFORMANCE OPTIMIZATION
                )
                if not objects_response.data.objects:
                    results.append(to_dict(bucket))
            except oci.exceptions.ServiceError:
                continue  # Skip buckets we cannot access

    except oci.exceptions.ServiceError:
        continue
```

### 3. List Bucket Objects

```python
bucket_name = "my-bucket"  # or from plan parameters

try:
    response = objectstorage_client.list_objects(
        namespace_name=namespace,
        bucket_name=bucket_name
    )
    for obj in response.data.objects:
        results.append(to_dict(obj))

    while response.has_next_page:
        response = objectstorage_client.list_objects(
            namespace_name=namespace,
            bucket_name=bucket_name,
            page=response.next_page
        )
        for obj in response.data.objects:
            results.append(to_dict(obj))
except oci.exceptions.ServiceError:
    pass  # Bucket not found or no access
```

### 4. List Bucket Objects with Size Filter

```python
bucket_name = "my-bucket"  # or from plan parameters
min_size = 1024  # 1KB minimum size

try:
    response = objectstorage_client.list_objects(
        namespace_name=namespace,
        bucket_name=bucket_name
    )
    for obj in response.data.objects:
        if obj.size >= min_size:
            results.append(to_dict(obj))

    while response.has_next_page:
        response = objectstorage_client.list_objects(
            namespace_name=namespace,
            bucket_name=bucket_name,
            page=response.next_page
        )
        for obj in response.data.objects:
            if obj.size >= min_size:
                results.append(to_dict(obj))
except oci.exceptions.ServiceError:
    pass  # Bucket not found or no access
```

### 5. List Bucket Objects by Prefix

```python
bucket_name = "my-bucket"  # or from plan parameters
prefix = "logs/"  # or from plan parameters

try:
    response = objectstorage_client.list_objects(
        namespace_name=namespace,
        bucket_name=bucket_name,
        prefix=prefix
    )
    for obj in response.data.objects:
        results.append(to_dict(obj))

    while response.has_next_page:
        response = objectstorage_client.list_objects(
            namespace_name=namespace,
            bucket_name=bucket_name,
            prefix=prefix,
            page=response.next_page
        )
        for obj in response.data.objects:
            results.append(to_dict(obj))
except oci.exceptions.ServiceError:
    pass  # Bucket not found or no access
```

### 6. Get Bucket Details

```python
bucket_name = "my-bucket"  # or from plan parameters

try:
    bucket = objectstorage_client.get_bucket(
        namespace_name=namespace,
        bucket_name=bucket_name
    ).data
    results.append(to_dict(bucket))
except oci.exceptions.ServiceError:
    pass  # Bucket not found or no access
```

## Key Points

- **CRITICAL**: Always fetch namespace dynamically with `get_namespace()`
- **NEVER** assume namespace exists in `oci_config`
- Use `limit=1` for existence checks to optimize performance
- Objects are accessed via `response.data.objects`
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Buckets are compartment-scoped

### 5. Create Action: `create_bucket`

When the plan action is `create_bucket`, you must generate code to create an Object Storage bucket. The parameters will be provided in the plan. This code incorporates security best practices from the CIS OCI Foundations Benchmark.

```python
from oci.util import to_dict

# Create Object Storage client
objectstorage_client = get_client('objectstorage', oci_config)
namespace = objectstorage_client.get_namespace().data

# Extract details from the plan's params
bucket_name = plan['params'].get('name')
compartment_id = plan['params'].get('compartment_id')

# Define the details for the new bucket
create_bucket_details = oci.object_storage.models.CreateBucketDetails(
    name=bucket_name,
    compartment_id=compartment_id,
    # CIS Benchmark 5.1.1: Ensure buckets are not publicly visible by default
    public_access_type='NoPublicAccess',
    storage_tier='Standard',
    # CIS Benchmark 5.1.3: Ensure versioning is enabled to protect against overwrites and deletions
    versioning='Enabled'
    # NOTE: CIS Benchmark 5.1.2 recommends using a Customer-Managed Key (CMK) for encryption.
    # This can be added via the 'kms_key_id' parameter if a key OCID is provided.
)

# Create the bucket
created_bucket_response = objectstorage_client.create_bucket(
    namespace_name=namespace,
    create_bucket_details=create_bucket_details
)

# Append the created resource details (as a dictionary) to the results
results.append(to_dict(created_bucket_response.data))
```
