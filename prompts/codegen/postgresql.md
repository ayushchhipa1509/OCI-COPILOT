# 🐘 PostgreSQL Service Patterns (`postgresql`)

## Client Creation

```python
postgresql_client = get_client('postgresql', oci_config)
```

## Common Patterns

### 1. List PostgreSQL DB Systems

```python
for compartment in all_compartments:
    try:
        response = postgresql_client.list_db_systems(compartment_id=compartment.id)
        for db_system in response.data:
            results.append(to_dict(db_system))

        while response.has_next_page:
            response = postgresql_client.list_db_systems(compartment_id=compartment.id, page=response.next_page)
            for db_system in response.data:
                results.append(to_dict(db_system))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List PostgreSQL DB Systems by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = postgresql_client.list_db_systems(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for db_system in response.data:
            results.append(to_dict(db_system))

        while response.has_next_page:
            response = postgresql_client.list_db_systems(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for db_system in response.data:
                results.append(to_dict(db_system))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List PostgreSQL Backups

```python
for compartment in all_compartments:
    try:
        response = postgresql_client.list_backups(compartment_id=compartment.id)
        for backup in response.data:
            results.append(to_dict(backup))

        while response.has_next_page:
            response = postgresql_client.list_backups(compartment_id=compartment.id, page=response.next_page)
            for backup in response.data:
                results.append(to_dict(backup))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List PostgreSQL Configurations

```python
for compartment in all_compartments:
    try:
        response = postgresql_client.list_configurations(compartment_id=compartment.id)
        for configuration in response.data:
            results.append(to_dict(configuration))

        while response.has_next_page:
            response = postgresql_client.list_configurations(compartment_id=compartment.id, page=response.next_page)
            for configuration in response.data:
                results.append(to_dict(configuration))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List PostgreSQL Databases

```python
for compartment in all_compartments:
    try:
        response = postgresql_client.list_databases(compartment_id=compartment.id)
        for database in response.data:
            results.append(to_dict(database))

        while response.has_next_page:
            response = postgresql_client.list_databases(compartment_id=compartment.id, page=response.next_page)
            for database in response.data:
                results.append(to_dict(database))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- PostgreSQL resources are compartment-scoped
- Databases are separate from DB systems


