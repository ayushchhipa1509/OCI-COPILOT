# 🛡️ Cloud Guard Service Patterns (`cloudguard`)

## Client Creation

```python
cloudguard_client = get_client('cloudguard', oci_config)
```

## Common Patterns

### 1. List Detectors

```python
for compartment in all_compartments:
    try:
        response = cloudguard_client.list_detectors(compartment_id=compartment.id)
        for detector in response.data:
            results.append(to_dict(detector))

        while response.has_next_page:
            response = cloudguard_client.list_detectors(compartment_id=compartment.id, page=response.next_page)
            for detector in response.data:
                results.append(to_dict(detector))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Detectors by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = cloudguard_client.list_detectors(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for detector in response.data:
            results.append(to_dict(detector))

        while response.has_next_page:
            response = cloudguard_client.list_detectors(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for detector in response.data:
                results.append(to_dict(detector))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Problems

```python
for compartment in all_compartments:
    try:
        response = cloudguard_client.list_problems(compartment_id=compartment.id)
        for problem in response.data:
            results.append(to_dict(problem))

        while response.has_next_page:
            response = cloudguard_client.list_problems(compartment_id=compartment.id, page=response.next_page)
            for problem in response.data:
                results.append(to_dict(problem))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Problems by Severity

```python
severity = "HIGH"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = cloudguard_client.list_problems(compartment_id=compartment.id)
        for problem in response.data:
            if problem.severity == severity:
                results.append(to_dict(problem))

        while response.has_next_page:
            response = cloudguard_client.list_problems(compartment_id=compartment.id, page=response.next_page)
            for problem in response.data:
                if problem.severity == severity:
                    results.append(to_dict(problem))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Responder Rules

```python
for compartment in all_compartments:
    try:
        response = cloudguard_client.list_responder_rules(compartment_id=compartment.id)
        for rule in response.data:
            results.append(to_dict(rule))

        while response.has_next_page:
            response = cloudguard_client.list_responder_rules(compartment_id=compartment.id, page=response.next_page)
            for rule in response.data:
                results.append(to_dict(rule))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Targets

```python
for compartment in all_compartments:
    try:
        response = cloudguard_client.list_targets(compartment_id=compartment.id)
        for target in response.data:
            results.append(to_dict(target))

        while response.has_next_page:
            response = cloudguard_client.list_targets(compartment_id=compartment.id, page=response.next_page)
            for target in response.data:
                results.append(to_dict(target))
    except oci.exceptions.ServiceError:
        continue
```

### 7. Get Cloud Guard Configuration

```python
# Get Cloud Guard configuration for the tenancy (root compartment)
tenancy_id = oci_config['tenancy']

try:
    # CORRECT: Use get_configuration method (not list_configurations)
    response = cloudguard_client.get_configuration(compartment_id=tenancy_id)

    # The response.data is a single configuration object, not a list
    # No loop needed - append directly to results
    results.append(to_dict(response.data))

except oci.exceptions.ServiceError as e:
    # Handle cases where Cloud Guard is not enabled or permission issues
    pass
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Severity filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Cloud Guard resources are compartment-scoped
- **CRITICAL:** Use `get_configuration()` for Cloud Guard status, not `list_configurations()`
