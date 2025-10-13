# 🎯 Optimizer Service Patterns (`optimizer`)

## Client Creation

```python
optimizer_client = get_client('optimizer', oci_config)
```

## Common Patterns

### 1. List Profiles

```python
for compartment in all_compartments:
    try:
        response = optimizer_client.list_profiles(compartment_id=compartment.id)
        for profile in response.data:
            results.append(to_dict(profile))

        while response.has_next_page:
            response = optimizer_client.list_profiles(compartment_id=compartment.id, page=response.next_page)
            for profile in response.data:
                results.append(to_dict(profile))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Profiles by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = optimizer_client.list_profiles(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for profile in response.data:
            results.append(to_dict(profile))

        while response.has_next_page:
            response = optimizer_client.list_profiles(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for profile in response.data:
                results.append(to_dict(profile))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Recommendations

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

### 4. List Recommendations by Category

```python
category = "COST"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = optimizer_client.list_recommendations(compartment_id=compartment.id)
        for recommendation in response.data:
            if recommendation.category == category:
                results.append(to_dict(recommendation))

        while response.has_next_page:
            response = optimizer_client.list_recommendations(compartment_id=compartment.id, page=response.next_page)
            for recommendation in response.data:
                if recommendation.category == category:
                    results.append(to_dict(recommendation))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Recommendations by Importance

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

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Category and importance filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Optimizer resources are compartment-scoped


