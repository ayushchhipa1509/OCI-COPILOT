# ⚖️ Load Balancer Service Patterns (`loadbalancer`)

## Client Creation

```python
loadbalancer_client = get_client('loadbalancer', oci_config)
```

## Common Patterns

### 1. List All Load Balancers

```python
for compartment in all_compartments:
    try:
        response = loadbalancer_client.list_load_balancers(compartment_id=compartment.id)
        for lb in response.data:
            results.append(to_dict(lb))

        while response.has_next_page:
            response = loadbalancer_client.list_load_balancers(compartment_id=compartment.id, page=response.next_page)
            for lb in response.data:
                results.append(to_dict(lb))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Load Balancers by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = loadbalancer_client.list_load_balancers(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for lb in response.data:
            results.append(to_dict(lb))

        while response.has_next_page:
            response = loadbalancer_client.list_load_balancers(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for lb in response.data:
                results.append(to_dict(lb))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Load Balancer Backend Sets

```python
load_balancer_id = "ocid1.loadbalancer.oc1..."  # or from plan parameters

try:
    response = loadbalancer_client.list_backend_sets(load_balancer_id=load_balancer_id)
    for backend_set in response.data:
        results.append(to_dict(backend_set))

    while response.has_next_page:
        response = loadbalancer_client.list_backend_sets(
            load_balancer_id=load_balancer_id,
            page=response.next_page
        )
        for backend_set in response.data:
            results.append(to_dict(backend_set))
except oci.exceptions.ServiceError:
    pass  # Load balancer not found or no access
```

### 4. Create Action: `create_load_balancer`

When the plan action is `create_load_balancer`, you must generate code to create a Load Balancer. This is a more complex pattern requiring multiple sub-components like backend sets and listeners.

```python
from oci.util import to_dict

# Create Load Balancer client
loadbalancer_client = get_client('loadbalancer', oci_config)

# Extract details from the plan's params
compartment_id = plan['params'].get('compartment_id')
display_name = plan['params'].get('display_name')
shape_name = plan['params'].get('shape_name')
subnet_ids = plan['params'].get('subnet_ids')  # Expects a list of subnet OCIDs

# Define the details for the new load balancer
create_load_balancer_details = oci.load_balancer.models.CreateLoadBalancerDetails(
    compartment_id=compartment_id,
    display_name=display_name,
    shape_name=shape_name,
    subnet_ids=subnet_ids,
    # Example: Define a default backend set and listener for a simple web server
    backend_sets={
        "my_backend_set": oci.load_balancer.models.BackendSetDetails(
            policy="ROUND_ROBIN",
            health_checker=oci.load_balancer.models.HealthCheckerDetails(
                protocol="HTTP",
                url_path="/",
                port=80,
                return_code=200,
                interval_in_millis=10000,
                timeout_in_millis=3000,
                retries=3
            )
        )
    },
    listeners={
        "my_http_listener": oci.load_balancer.models.ListenerDetails(
            default_backend_set_name="my_backend_set",
            protocol="HTTP",
            port=80
        )
    }
)

# Create the load balancer
# This is an asynchronous operation, so we get a work request ID back
create_load_balancer_response = loadbalancer_client.create_load_balancer(
    create_load_balancer_details=create_load_balancer_details
)

# For asynchronous operations, we can wait for the work request to succeed
work_request_id = create_load_balancer_response.headers['opc-work-request-id']
oci.wait_until(loadbalancer_client, loadbalancer_client.get_work_request(work_request_id), 'lifecycle_state', 'SUCCEEDED')

# After waiting, get the load balancer details using the ID from the work request
lb_ocid = loadbalancer_client.get_work_request(work_request_id).data.load_balancer_id
load_balancer = loadbalancer_client.get_load_balancer(lb_ocid).data

# Append the final resource details (as a dictionary) to the results
results.append(to_dict(load_balancer))
```

## Key Points

- Load balancers are asynchronous operations that return work request IDs
- Always wait for work requests to complete before considering the operation successful
- Backend sets and listeners are configured during creation
- Health checkers are required for backend sets
- Load balancers require at least one subnet in the subnet_ids list
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
