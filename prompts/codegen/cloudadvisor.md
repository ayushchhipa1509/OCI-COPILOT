# ☁️ Cloud Advisor Service Patterns (`optimizer`)

## Client Creation

```python
optimizer_client = get_client('optimizer', oci_config)
```

## Common Patterns

### 1. List Recommendations

```python
for compartment in all_compartments:
    try:
        response = optimizer_client.list_recommendations(compartment_id=compartment.id)
        for recommendation in response.data:
            results.append(to_dict(recommendation))

        while response.has_next_page:
            response = optimizer_client.list_recommendations(compartment_id=compartment.id, page=response.next_page)
            for recommendation in response.data:
                results.append(to_dict(recommendation))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Recommendations by Category

```python
category = "COST"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = optimizer_client.list_recommendations(
            compartment_id=compartment.id,
            category=category
        )
        for recommendation in response.data:
            results.append(to_dict(recommendation))

        while response.has_next_page:
            response = optimizer_client.list_recommendations(
                compartment_id=compartment.id,
                category=category,
                page=response.next_page
            )
            for recommendation in response.data:
                results.append(to_dict(recommendation))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Recommendations by Importance

```python
importance = "HIGH"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = optimizer_client.list_recommendations(compartment_id=compartment.id)
        for recommendation in response.data:
            if recommendation.importance == importance:
                results.append(to_dict(recommendation))

        while response.has_next_page:
            response = optimizer_client.list_recommendations(compartment_id=compartment.id, page=response.next_page)
            for recommendation in response.data:
                if recommendation.importance == importance:
                    results.append(to_dict(recommendation))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Resource Actions

```python
for compartment in all_compartments:
    try:
        response = optimizer_client.list_resource_actions(compartment_id=compartment.id)
        for resource_action in response.data:
            results.append(to_dict(resource_action))

        while response.has_next_page:
            response = optimizer_client.list_resource_actions(compartment_id=compartment.id, page=response.next_page)
            for resource_action in response.data:
                results.append(to_dict(resource_action))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Work Requests

```python
for compartment in all_compartments:
    try:
        response = optimizer_client.list_work_requests(compartment_id=compartment.id)
        for work_request in response.data:
            results.append(to_dict(work_request))

        while response.has_next_page:
            response = optimizer_client.list_work_requests(compartment_id=compartment.id, page=response.next_page)
            for work_request in response.data:
                results.append(to_dict(work_request))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `category` parameter for filtering by recommendation type (COST, PERFORMANCE, etc.)
- Importance filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Cloud Advisor resources are compartment-scoped
- Resource actions show what actions can be taken on recommendations
