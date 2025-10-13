# 🌐 Network Load Balancer Service Patterns (`network_load_balancer`)

## Client Creation

```python
nlb_client = get_client('network_load_balancer', oci_config)
```

## Common Patterns

### 1. List Network Load Balancers

```python
for compartment in all_compartments:
    try:
        response = nlb_client.list_network_load_balancers(compartment_id=compartment.id)
        for nlb in response.data:
            results.append(to_dict(nlb))

        while response.has_next_page:
            response = nlb_client.list_network_load_balancers(compartment_id=compartment.id, page=response.next_page)
            for nlb in response.data:
                results.append(to_dict(nlb))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Network Load Balancers by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = nlb_client.list_network_load_balancers(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for nlb in response.data:
            results.append(to_dict(nlb))

        while response.has_next_page:
            response = nlb_client.list_network_load_balancers(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for nlb in response.data:
                results.append(to_dict(nlb))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Backend Sets

```python
network_load_balancer_id = "ocid1.networkloadbalancer.oc1..."  # or from plan parameters

try:
    response = nlb_client.list_backend_sets(network_load_balancer_id=network_load_balancer_id)
    for backend_set in response.data:
        results.append(to_dict(backend_set))

    while response.has_next_page:
        response = nlb_client.list_backend_sets(network_load_balancer_id=network_load_balancer_id, page=response.next_page)
        for backend_set in response.data:
            results.append(to_dict(backend_set))
except oci.exceptions.ServiceError:
    pass  # Network load balancer not found or no access
```

### 4. List Backends

```python
network_load_balancer_id = "ocid1.networkloadbalancer.oc1..."  # or from plan parameters
backend_set_name = "backend-set-1"  # or from plan parameters

try:
    response = nlb_client.list_backends(
        network_load_balancer_id=network_load_balancer_id,
        backend_set_name=backend_set_name
    )
    for backend in response.data:
        results.append(to_dict(backend))

    while response.has_next_page:
        response = nlb_client.list_backends(
            network_load_balancer_id=network_load_balancer_id,
            backend_set_name=backend_set_name,
            page=response.next_page
        )
        for backend in response.data:
            results.append(to_dict(backend))
except oci.exceptions.ServiceError:
    pass  # Network load balancer not found or no access
```

### 5. List Listeners

```python
network_load_balancer_id = "ocid1.networkloadbalancer.oc1..."  # or from plan parameters

try:
    response = nlb_client.list_listeners(network_load_balancer_id=network_load_balancer_id)
    for listener in response.data:
        results.append(to_dict(listener))

    while response.has_next_page:
        response = nlb_client.list_listeners(network_load_balancer_id=network_load_balancer_id, page=response.next_page)
        for listener in response.data:
            results.append(to_dict(listener))
except oci.exceptions.ServiceError:
    pass  # Network load balancer not found or no access
```

### 6. List Health Checkers

```python
network_load_balancer_id = "ocid1.networkloadbalancer.oc1..."  # or from plan parameters
backend_set_name = "backend-set-1"  # or from plan parameters

try:
    response = nlb_client.get_health_checker(
        network_load_balancer_id=network_load_balancer_id,
        backend_set_name=backend_set_name
    )
    results.append(to_dict(response.data))
except oci.exceptions.ServiceError:
    pass  # Network load balancer not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Backend sets, backends, and listeners require a specific network load balancer ID
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Network load balancer resources are compartment-scoped


