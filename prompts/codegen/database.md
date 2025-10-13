# 🗄️ Database Service Patterns (`database`)

## Client Creation

```python
database_client = get_client('database', oci_config)
```

## Common Patterns

### 1. List All Databases

```python
for compartment in all_compartments:
    try:
        response = database_client.list_databases(compartment_id=compartment.id)
        for database in response.data:
            results.append(to_dict(database))

        while response.has_next_page:
            response = database_client.list_databases(compartment_id=compartment.id, page=response.next_page)
            for database in response.data:
                results.append(to_dict(database))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Autonomous Databases

```python
for compartment in all_compartments:
    try:
        response = database_client.list_autonomous_databases(compartment_id=compartment.id)
        for autonomous_db in response.data:
            results.append(to_dict(autonomous_db))

        while response.has_next_page:
            response = database_client.list_autonomous_databases(compartment_id=compartment.id, page=response.next_page)
            for autonomous_db in response.data:
                results.append(to_dict(autonomous_db))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Autonomous Databases by Lifecycle State

```python
lifecycle_state = "AVAILABLE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = database_client.list_autonomous_databases(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for autonomous_db in response.data:
            results.append(to_dict(autonomous_db))

        while response.has_next_page:
            response = database_client.list_autonomous_databases(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for autonomous_db in response.data:
                results.append(to_dict(autonomous_db))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Database Systems

```python
for compartment in all_compartments:
    try:
        response = database_client.list_db_systems(compartment_id=compartment.id)
        for db_system in response.data:
            results.append(to_dict(db_system))

        while response.has_next_page:
            response = database_client.list_db_systems(compartment_id=compartment.id, page=response.next_page)
            for db_system in response.data:
                results.append(to_dict(db_system))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Database Homes

```python
for compartment in all_compartments:
    try:
        response = database_client.list_db_homes(compartment_id=compartment.id)
        for db_home in response.data:
            results.append(to_dict(db_home))

        while response.has_next_page:
            response = database_client.list_db_homes(compartment_id=compartment.id, page=response.next_page)
            for db_home in response.data:
                results.append(to_dict(db_home))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Database Backups

```python
for compartment in all_compartments:
    try:
        response = database_client.list_backups(compartment_id=compartment.id)
        for backup in response.data:
            results.append(to_dict(backup))

        while response.has_next_page:
            response = database_client.list_backups(compartment_id=compartment.id, page=response.next_page)
            for backup in response.data:
                results.append(to_dict(backup))
    except oci.exceptions.ServiceError:
        continue
```

### 7. List Database Patches

```python
for compartment in all_compartments:
    try:
        response = database_client.list_patches(compartment_id=compartment.id)
        for patch in response.data:
            results.append(to_dict(patch))

        while response.has_next_page:
            response = database_client.list_patches(compartment_id=compartment.id, page=response.next_page)
            for patch in response.data:
                results.append(to_dict(patch))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Autonomous databases are different from regular databases
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Database resources are compartment-scoped


