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

**CRITICAL**: This pattern correctly identifies truly empty buckets by checking object count.

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
                # Check if bucket is truly empty
                if not objects_response.data.objects or len(objects_response.data.objects) == 0:
                    # Add bucket info with empty confirmation
                    bucket_info = to_dict(bucket)
                    bucket_info['is_empty'] = True
                    bucket_info['object_count'] = 0
                    results.append(bucket_info)
            except oci.exceptions.ServiceError as e:
                # Skip buckets we cannot access, but log the reason
                print(f"Cannot check bucket {bucket.name}: {e.message}")
                continue

    except oci.exceptions.ServiceError:
        continue
```

### 2a. Alternative: List Empty Buckets with Object Count Verification

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

        # Check each bucket for emptiness with proper verification
        for bucket in all_buckets:
            try:
                # First, try to get object count with limit=1 for performance
                objects_response = objectstorage_client.list_objects(
                    namespace_name=namespace,
                    bucket_name=bucket.name,
                    limit=1
                )

                # If we get here, the bucket exists and we can check it
                if objects_response.data.objects is None or len(objects_response.data.objects) == 0:
                    # Double-check by getting the actual count
                    try:
                        # Get a more comprehensive check
                        full_objects_response = objectstorage_client.list_objects(
                            namespace_name=namespace,
                            bucket_name=bucket.name,
                            limit=1000  # Reasonable limit for verification
                        )

                        # Count all objects (handle pagination if needed)
                        total_objects = len(full_objects_response.data.objects)
                        while full_objects_response.has_next_page:
                            full_objects_response = objectstorage_client.list_objects(
                                namespace_name=namespace,
                                bucket_name=bucket.name,
                                page=full_objects_response.next_page,
                                limit=1000
                            )
                            total_objects += len(full_objects_response.data.objects)

                        # Only add if truly empty
                        if total_objects == 0:
                            bucket_info = to_dict(bucket)
                            bucket_info['is_empty'] = True
                            bucket_info['object_count'] = 0
                            bucket_info['verified_empty'] = True
                            results.append(bucket_info)

                    except oci.exceptions.ServiceError:
                        # If we can't verify, skip this bucket
                        continue

            except oci.exceptions.ServiceError as e:
                # Skip buckets we cannot access
                print(f"Cannot access bucket {bucket.name}: {e.message}")
                continue

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
public_access = plan['params'].get('public_access', False)

# Determine public access type based on user preference
public_access_type = 'ObjectRead' if public_access else 'NoPublicAccess'

# Define the details for the new bucket
create_bucket_details = oci.object_storage.models.CreateBucketDetails(
    name=bucket_name,
    compartment_id=compartment_id,
    # Use user-specified public access preference
    public_access_type=public_access_type,
    storage_tier='Standard',
    # CIS Benchmark 5.1.3: Ensure versioning is enabled to protect against overwrites and deletions
    versioning='Enabled'
    # NOTE: CIS Benchmark 5.1.2 recommends using a Customer-Managed Key (CMK) for encryption.
    # This can be added via the 'kms_key_id' parameter if a key OCID is provided.
)

# Create the bucket with error handling
try:
    created_bucket_response = objectstorage_client.create_bucket(
        namespace_name=namespace,
        create_bucket_details=create_bucket_details
    )
    # Append the created resource details to results
    results.append(to_dict(created_bucket_response.data))
except oci.exceptions.ServiceError as e:
    # Append error result
    results.append({
        'action': 'create_bucket',
        'name': bucket_name,
        'status': 'error',
        'message': f'Failed to create bucket: {e.message}'
    })
```

### 6. Delete Action: `delete_bucket`

When the plan action is `delete_bucket`, you must generate code to delete an Object Storage bucket. **WARNING**: This is a destructive operation that cannot be undone.

```python
from oci.util import to_dict

# Create Object Storage client
objectstorage_client = get_client('objectstorage', oci_config)
namespace = objectstorage_client.get_namespace().data

# Extract details from the plan's params
bucket_name = plan['params'].get('name')

# Delete the bucket
# WARNING: This operation is irreversible
try:
    delete_bucket_response = objectstorage_client.delete_bucket(
        namespace_name=namespace,
        bucket_name=bucket_name
    )

    # Bucket deletion doesn't return data, so we create a confirmation message
    results.append({
        'action': 'delete_bucket',
        'bucket_name': bucket_name,
        'status': 'deleted',
        'message': f'Bucket {bucket_name} has been successfully deleted'
    })

except oci.exceptions.ServiceError as e:
    # Handle common deletion errors
    if e.status == 404:
        results.append({
            'action': 'delete_bucket',
            'bucket_name': bucket_name,
            'status': 'not_found',
            'message': f'Bucket {bucket_name} not found or already deleted'
        })
    elif e.status == 409:
        results.append({
            'action': 'delete_bucket',
            'bucket_name': bucket_name,
            'status': 'not_empty',
            'message': f'Cannot delete bucket {bucket_name} - bucket is not empty. Please delete all objects first.'
        })
    else:
        results.append({
            'action': 'delete_bucket',
            'bucket_name': bucket_name,
            'status': 'error',
            'message': f'Failed to delete bucket {bucket_name}: {e.message}'
        })
```
