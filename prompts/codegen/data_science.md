# 🤖 Data Science Service Patterns (`data_science`)

## Client Creation

```python
data_science_client = get_client('data_science', oci_config)
```

## Common Patterns

### 1. List Projects

```python
for compartment in all_compartments:
    try:
        response = data_science_client.list_projects(compartment_id=compartment.id)
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = data_science_client.list_projects(compartment_id=compartment.id, page=response.next_page)
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
        response = data_science_client.list_projects(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = data_science_client.list_projects(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for project in response.data:
                results.append(to_dict(project))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Notebook Sessions

```python
for compartment in all_compartments:
    try:
        response = data_science_client.list_notebook_sessions(compartment_id=compartment.id)
        for session in response.data:
            results.append(to_dict(session))

        while response.has_next_page:
            response = data_science_client.list_notebook_sessions(compartment_id=compartment.id, page=response.next_page)
            for session in response.data:
                results.append(to_dict(session))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Notebook Sessions by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = data_science_client.list_notebook_sessions(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for session in response.data:
            results.append(to_dict(session))

        while response.has_next_page:
            response = data_science_client.list_notebook_sessions(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for session in response.data:
                results.append(to_dict(session))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Models

```python
for compartment in all_compartments:
    try:
        response = data_science_client.list_models(compartment_id=compartment.id)
        for model in response.data:
            results.append(to_dict(model))

        while response.has_next_page:
            response = data_science_client.list_models(compartment_id=compartment.id, page=response.next_page)
            for model in response.data:
                results.append(to_dict(model))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Model Deployments

```python
for compartment in all_compartments:
    try:
        response = data_science_client.list_model_deployments(compartment_id=compartment.id)
        for deployment in response.data:
            results.append(to_dict(deployment))

        while response.has_next_page:
            response = data_science_client.list_model_deployments(compartment_id=compartment.id, page=response.next_page)
            for deployment in response.data:
                results.append(to_dict(deployment))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Data Science resources are compartment-scoped


