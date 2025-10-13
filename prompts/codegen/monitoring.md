# 📊 Monitoring Service Patterns (`monitoring`)

## Client Creation

```python
monitoring_client = get_client('monitoring', oci_config)
```

## Common Patterns

### 1. List Alarms

```python
for compartment in all_compartments:
    try:
        response = monitoring_client.list_alarms(compartment_id=compartment.id)
        for alarm in response.data:
            results.append(to_dict(alarm))

        while response.has_next_page:
            response = monitoring_client.list_alarms(compartment_id=compartment.id, page=response.next_page)
            for alarm in response.data:
                results.append(to_dict(alarm))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Alarms by State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = monitoring_client.list_alarms(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for alarm in response.data:
            results.append(to_dict(alarm))

        while response.has_next_page:
            response = monitoring_client.list_alarms(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for alarm in response.data:
                results.append(to_dict(alarm))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Metrics

```python
for compartment in all_compartments:
    try:
        response = monitoring_client.list_metrics(compartment_id=compartment.id)
        for metric in response.data:
            results.append(to_dict(metric))

        while response.has_next_page:
            response = monitoring_client.list_metrics(compartment_id=compartment.id, page=response.next_page)
            for metric in response.data:
                results.append(to_dict(metric))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Metric Data

```python
namespace = "oci_computeagent"  # or from plan parameters
metric_name = "CpuUtilization"  # or from plan parameters

try:
    response = monitoring_client.list_metric_data(
        compartment_id=compartment.id,
        namespace=namespace,
        metric_name=metric_name
    )
    for data_point in response.data:
        results.append(to_dict(data_point))

    while response.has_next_page:
        response = monitoring_client.list_metric_data(
            compartment_id=compartment.id,
            namespace=namespace,
            metric_name=metric_name,
            page=response.next_page
        )
        for data_point in response.data:
            results.append(to_dict(data_point))
except oci.exceptions.ServiceError:
    pass  # No data or access denied
```

### 5. List Alarm History

```python
alarm_id = "ocid1.alarm.oc1..."  # or from plan parameters

try:
    response = monitoring_client.list_alarm_history(alarm_id=alarm_id)
    for history in response.data:
        results.append(to_dict(history))

    while response.has_next_page:
        response = monitoring_client.list_alarm_history(alarm_id=alarm_id, page=response.next_page)
        for history in response.data:
            results.append(to_dict(history))
except oci.exceptions.ServiceError:
    pass  # Alarm not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Metric data requires namespace and metric name
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Monitoring resources are compartment-scoped


