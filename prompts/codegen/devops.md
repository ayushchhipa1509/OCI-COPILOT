# 🚀 DevOps Service Patterns (`devops`)

## Client Creation

```python
devops_client = get_client('devops', oci_config)
```

## Common Patterns

### 1. List Projects

```python
for compartment in all_compartments:
    try:
        response = devops_client.list_projects(compartment_id=compartment.id)
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = devops_client.list_projects(compartment_id=compartment.id, page=response.next_page)
            for project in response.data:
                results.append(to_dict(project))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Projects by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = devops_client.list_projects(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = devops_client.list_projects(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for project in response.data:
                results.append(to_dict(project))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Build Pipelines

```python
for compartment in all_compartments:
    try:
        response = devops_client.list_build_pipelines(compartment_id=compartment.id)
        for pipeline in response.data:
            results.append(to_dict(pipeline))

        while response.has_next_page:
            response = devops_client.list_build_pipelines(compartment_id=compartment.id, page=response.next_page)
            for pipeline in response.data:
                results.append(to_dict(pipeline))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Deployments

```python
for compartment in all_compartments:
    try:
        response = devops_client.list_deployments(compartment_id=compartment.id)
        for deployment in response.data:
            results.append(to_dict(deployment))

        while response.has_next_page:
            response = devops_client.list_deployments(compartment_id=compartment.id, page=response.next_page)
            for deployment in response.data:
                results.append(to_dict(deployment))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Deployments by Lifecycle State

```python
lifecycle_state = "SUCCEEDED"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = devops_client.list_deployments(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for deployment in response.data:
            results.append(to_dict(deployment))

        while response.has_next_page:
            response = devops_client.list_deployments(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for deployment in response.data:
                results.append(to_dict(deployment))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Repositories

```python
for compartment in all_compartments:
    try:
        response = devops_client.list_repositories(compartment_id=compartment.id)
        for repository in response.data:
            results.append(to_dict(repository))

        while response.has_next_page:
            response = devops_client.list_repositories(compartment_id=compartment.id, page=response.next_page)
            for repository in response.data:
                results.append(to_dict(repository))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- DevOps resources are compartment-scoped


