# 🌐 Virtual Network Service Patterns (`virtualnetwork`)

## Client Creation

```python
virtual_network_client = get_client('virtualnetwork', oci_config)
```

## Common Patterns

### 1. List All VCNs

```python
for compartment in all_compartments:
    try:
        response = virtual_network_client.list_vcns(compartment_id=compartment.id)
        for vcn in response.data:
            results.append(to_dict(vcn))

        while response.has_next_page:
            response = virtual_network_client.list_vcns(compartment_id=compartment.id, page=response.next_page)
            for vcn in response.data:
                results.append(to_dict(vcn))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Subnets

```python
for compartment in all_compartments:
    try:
        response = virtual_network_client.list_subnets(compartment_id=compartment.id)
        for subnet in response.data:
            results.append(to_dict(subnet))

        while response.has_next_page:
            response = virtual_network_client.list_subnets(compartment_id=compartment.id, page=response.next_page)
            for subnet in response.data:
                results.append(to_dict(subnet))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Security Lists

```python
for compartment in all_compartments:
    try:
        response = virtual_network_client.list_security_lists(compartment_id=compartment.id)
        for security_list in response.data:
            results.append(to_dict(security_list))

        while response.has_next_page:
            response = virtual_network_client.list_security_lists(compartment_id=compartment.id, page=response.next_page)
            for security_list in response.data:
                results.append(to_dict(security_list))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Route Tables

```python
for compartment in all_compartments:
    try:
        response = virtual_network_client.list_route_tables(compartment_id=compartment.id)
        for route_table in response.data:
            results.append(to_dict(route_table))

        while response.has_next_page:
            response = virtual_network_client.list_route_tables(compartment_id=compartment.id, page=response.next_page)
            for route_table in response.data:
                results.append(to_dict(route_table))
    except oci.exceptions.ServiceError:
        continue
```

### 5. Create Action: `create_vcn`

When the plan action is `create_vcn`, you must generate code to create a Virtual Cloud Network. VCNs are a foundational component for organizing and isolating cloud resources. The CIS Benchmark recommends that resources should not be created in the root compartment.

```python
import oci
from oci.util import to_dict

# Create the Virtual Network client
virtual_network_client = get_client('virtualnetwork', oci_config)

# Extract the required parameters from the plan
compartment_id = plan['params'].get('compartment_id')
cidr_block = plan['params'].get('cidr_block')
display_name = plan['params'].get('display_name')

# Define the details for the new VCN
create_vcn_details = oci.core.models.CreateVcnDetails(
    compartment_id=compartment_id,
    cidr_block=cidr_block,
    display_name=display_name
)

# Create the VCN with error handling. This is an asynchronous operation.
try:
    create_vcn_response = virtual_network_client.create_vcn(
        create_vcn_details=create_vcn_details
    )

    # Best Practice: Use a waiter to confirm the resource is fully provisioned.
    # We get the new VCN's OCID from the response data.
    vcn_ocid = create_vcn_response.data.id

    # Wait until the VCN's lifecycle state becomes 'AVAILABLE'.
    get_vcn_response = oci.wait_until(
        virtual_network_client,
        virtual_network_client.get_vcn(vcn_ocid),
        'lifecycle_state',
        'AVAILABLE'
    )

    # Once the wait is successful, the fully provisioned VCN details are in the response.
    # Append the final, confirmed resource details to results.
    results.append(to_dict(get_vcn_response.data))

except oci.exceptions.ServiceError as e:
    # Append error result
    results.append({
        'action': 'create_vcn',
        'display_name': display_name,
        'status': 'error',
        'message': f'Failed to create VCN: {e.message}'
    })
```

### 6. Create Action: `create_subnet`

When the plan action is `create_subnet`, you must generate code to create a subnet within a VCN.

```python
from oci.util import to_dict

# Extract the required parameters from the plan
compartment_id = plan['params'].get('compartment_id')
vcn_id = plan['params'].get('vcn_id')
cidr_block = plan['params'].get('cidr_block')
display_name = plan['params'].get('display_name')
availability_domain = plan['params'].get('availability_domain')

# Define the details for the new subnet
create_subnet_details = oci.core.models.CreateSubnetDetails(
    compartment_id=compartment_id,
    vcn_id=vcn_id,
    cidr_block=cidr_block,
    display_name=display_name,
    availability_domain=availability_domain
)

# Create the subnet
create_subnet_response = virtual_network_client.create_subnet(
    create_subnet_details=create_subnet_details
)

# Wait until the subnet's lifecycle state becomes 'AVAILABLE'
subnet_ocid = create_subnet_response.data.id
get_subnet_response = oci.wait_until(
    virtual_network_client,
    virtual_network_client.get_subnet(subnet_ocid),
    'lifecycle_state',
    'AVAILABLE'
)

# Append the final resource details to the results
results.append(to_dict(get_subnet_response.data))
```

## Key Points

- VCNs are foundational networking components that must be created before subnets
- Always use `oci.wait_until()` for asynchronous operations to ensure completion
- CIDR blocks must not overlap with existing VCNs in the same region
- Subnets require an availability domain
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- VCNs are compartment-scoped resources
