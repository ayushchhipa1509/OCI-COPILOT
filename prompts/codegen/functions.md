# ⚡ Functions Service Patterns (`functions`)

## Client Creation

```python
functions_client = get_client('functions', oci_config)
```

## Common Patterns

### 1. List Applications

```python
for compartment in all_compartments:
    try:
        response = functions_client.list_applications(compartment_id=compartment.id)
        for application in response.data:
            results.append(to_dict(application))

        while response.has_next_page:
            response = functions_client.list_applications(compartment_id=compartment.id, page=response.next_page)
            for application in response.data:
                results.append(to_dict(application))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Applications by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = functions_client.list_applications(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for application in response.data:
            results.append(to_dict(application))

        while response.has_next_page:
            response = functions_client.list_applications(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for application in response.data:
                results.append(to_dict(application))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Functions

```python
application_id = "ocid1.fnapp.oc1..."  # or from plan parameters

try:
    response = functions_client.list_functions(application_id=application_id)
    for function in response.data:
        results.append(to_dict(function))

    while response.has_next_page:
        response = functions_client.list_functions(application_id=application_id, page=response.next_page)
        for function in response.data:
            results.append(to_dict(function))
except oci.exceptions.ServiceError:
    pass  # Application not found or no access
```

### 4. List Functions by Lifecycle State

```python
application_id = "ocid1.fnapp.oc1..."  # or from plan parameters
lifecycle_state = "ACTIVE"  # or from plan parameters

try:
    response = functions_client.list_functions(application_id=application_id)
    for function in response.data:
        if function.lifecycle_state == lifecycle_state:
            results.append(to_dict(function))

    while response.has_next_page:
        response = functions_client.list_functions(application_id=application_id, page=response.next_page)
        for function in response.data:
            if function.lifecycle_state == lifecycle_state:
                results.append(to_dict(function))
except oci.exceptions.ServiceError:
    pass  # Application not found or no access
```

### 5. List Invocations

```python
function_id = "ocid1.fnfunc.oc1..."  # or from plan parameters

try:
    response = functions_client.list_invocations(function_id=function_id)
    for invocation in response.data:
        results.append(to_dict(invocation))

    while response.has_next_page:
        response = functions_client.list_invocations(function_id=function_id, page=response.next_page)
        for invocation in response.data:
            results.append(to_dict(invocation))
except oci.exceptions.ServiceError:
    pass  # Function not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Functions require a specific application ID
- Invocations require a specific function ID
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Functions resources are compartment-scoped


