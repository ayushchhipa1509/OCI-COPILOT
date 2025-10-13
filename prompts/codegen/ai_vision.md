# 👁️ AI Vision Service Patterns (`ai_vision`)

## Client Creation

```python
ai_vision_client = get_client('ai_vision', oci_config)
```

## Common Patterns

### 1. List Projects

```python
for compartment in all_compartments:
    try:
        response = ai_vision_client.list_projects(compartment_id=compartment.id)
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = ai_vision_client.list_projects(compartment_id=compartment.id, page=response.next_page)
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
        response = ai_vision_client.list_projects(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for project in response.data:
            results.append(to_dict(project))

        while response.has_next_page:
            response = ai_vision_client.list_projects(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for project in response.data:
                results.append(to_dict(project))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Models

```python
for compartment in all_compartments:
    try:
        response = ai_vision_client.list_models(compartment_id=compartment.id)
        for model in response.data:
            results.append(to_dict(model))

        while response.has_next_page:
            response = ai_vision_client.list_models(compartment_id=compartment.id, page=response.next_page)
            for model in response.data:
                results.append(to_dict(model))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Models by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = ai_vision_client.list_models(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for model in response.data:
            results.append(to_dict(model))

        while response.has_next_page:
            response = ai_vision_client.list_models(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for model in response.data:
                results.append(to_dict(model))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Datasets

```python
for compartment in all_compartments:
    try:
        response = ai_vision_client.list_datasets(compartment_id=compartment.id)
        for dataset in response.data:
            results.append(to_dict(dataset))

        while response.has_next_page:
            response = ai_vision_client.list_datasets(compartment_id=compartment.id, page=response.next_page)
            for dataset in response.data:
                results.append(to_dict(dataset))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Annotations

```python
dataset_id = "ocid1.dataset.oc1..."  # or from plan parameters

try:
    response = ai_vision_client.list_annotations(dataset_id=dataset_id)
    for annotation in response.data:
        results.append(to_dict(annotation))

    while response.has_next_page:
        response = ai_vision_client.list_annotations(dataset_id=dataset_id, page=response.next_page)
        for annotation in response.data:
            results.append(to_dict(annotation))
except oci.exceptions.ServiceError:
    pass  # Dataset not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Annotations require a specific dataset ID
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- AI Vision resources are compartment-scoped


