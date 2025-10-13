# 🗂️ Identity Service Patterns (`identity`)

## Client Creation

```python
identity_client = get_client('identity', oci_config)
```

## Common Patterns

### 1. List All Users

```python
# oci_config is available directly in execution context
tenancy_id = oci_config['tenancy']
response = identity_client.list_users(compartment_id=tenancy_id)
for user in response.data:
    results.append(to_dict(user))

while response.has_next_page:
    response = identity_client.list_users(compartment_id=tenancy_id, page=response.next_page)
    for user in response.data:
        results.append(to_dict(user))
```

### 2. List Users with MFA Disabled (Multi-step)

```python
# oci_config is available directly in execution context
tenancy_id = oci_config['tenancy']
response = identity_client.list_users(compartment_id=tenancy_id)
all_users = response.data
while response.has_next_page:
    response = identity_client.list_users(compartment_id=tenancy_id, page=response.next_page)
    all_users.extend(response.data)

for user in all_users:
    try:
        # Check MFA devices for this user
        mfa_devices_response = identity_client.list_mfa_totp_devices(user_id=user.id)

        # User has MFA DISABLED if no devices found
        if not mfa_devices_response.data:
            results.append(to_dict(user))

    except oci.exceptions.ServiceError:
        continue  # Skip users we cannot check
```

### 3. List Groups

```python
tenancy_id = oci_config['tenancy']
response = identity_client.list_groups(compartment_id=tenancy_id)
for group in response.data:
    results.append(to_dict(group))

while response.has_next_page:
    response = identity_client.list_groups(compartment_id=tenancy_id, page=response.next_page)
    for group in response.data:
        results.append(to_dict(group))
```

### 4. List Users in Specific Group (Multi-step)

```python
tenancy_id = oci_config['tenancy']
group_name = "Administrators"  # or from plan parameters

# First, find the group
response = identity_client.list_groups(compartment_id=tenancy_id)
target_group = None
for group in response.data:
    if group.name == group_name:
        target_group = group
        break

if target_group:
    # Get group memberships
    memberships_response = identity_client.list_user_group_memberships(compartment_id=tenancy_id, group_id=target_group.id)
    for membership in memberships_response.data:
        # Get full user details
        user = identity_client.get_user(user_id=membership.user_id).data
        results.append(to_dict(user))

    while memberships_response.has_next_page:
        memberships_response = identity_client.list_user_group_memberships(
            compartment_id=tenancy_id,
            group_id=target_group.id,
            page=memberships_response.next_page
        )
        for membership in memberships_response.data:
            user = identity_client.get_user(user_id=membership.user_id).data
            results.append(to_dict(user))
```

### 5. List Policies

```python
for compartment in all_compartments:
    try:
        response = identity_client.list_policies(compartment_id=compartment.id)
        for policy in response.data:
            results.append(to_dict(policy))

        while response.has_next_page:
            response = identity_client.list_policies(compartment_id=compartment.id, page=response.next_page)
            for policy in response.data:
                results.append(to_dict(policy))
    except oci.exceptions.ServiceError:
        continue
```

### 6. Find Duplicate Policy Statements (Multi-step Analysis)

```python
import collections

# Get all policies from all compartments
all_policies = []
for compartment in all_compartments:
    try:
        response = identity_client.list_policies(compartment_id=compartment.id)
        all_policies.extend(response.data)
        while response.has_next_page:
            response = identity_client.list_policies(compartment_id=compartment.id, page=response.next_page)
            all_policies.extend(response.data)
    except oci.exceptions.ServiceError:
        continue

# Count all statements
statement_counts = collections.Counter()
for policy in all_policies:
    for statement in policy.statements:
        # Normalize statement (remove extra whitespace)
        normalized_statement = statement.strip()
        statement_counts[normalized_statement] += 1

# Find duplicates
for statement, count in statement_counts.items():
    if count > 1:
        results.append({
            'duplicate_statement': statement,
            'occurrence_count': count
        })
```

### 7. List Compartments

```python
tenancy_id = oci_config['tenancy']
response = identity_client.list_compartments(compartment_id=tenancy_id)
for compartment in response.data:
    results.append(to_dict(compartment))

while response.has_next_page:
    response = identity_client.list_compartments(compartment_id=tenancy_id, page=response.next_page)
    for compartment in response.data:
        results.append(to_dict(compartment))
```

## Key Points

- Users and groups are tenancy-scoped, not compartment-scoped
- MFA status requires a separate API call for each user
- Policy statements are stored as a list of strings
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
