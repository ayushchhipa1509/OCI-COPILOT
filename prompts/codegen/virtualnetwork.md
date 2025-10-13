# 🌐 Virtual Network Service Patterns (`virtualnetwork`)

## Client Creation

```python
network_client = get_client('virtualnetwork', oci_config)
```

## Common Patterns

### 1. List VCNs

```python
for compartment in all_compartments:
    try:
        response = network_client.list_vcns(compartment_id=compartment.id)
        for vcn in response.data:
            results.append(to_dict(vcn))

        while response.has_next_page:
            response = network_client.list_vcns(compartment_id=compartment.id, page=response.next_page)
            for vcn in response.data:
                results.append(to_dict(vcn))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Subnets

```python
for compartment in all_compartments:
    try:
        response = network_client.list_subnets(compartment_id=compartment.id)
        for subnet in response.data:
            results.append(to_dict(subnet))

        while response.has_next_page:
            response = network_client.list_subnets(compartment_id=compartment.id, page=response.next_page)
            for subnet in response.data:
                results.append(to_dict(subnet))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Security Lists

```python
for compartment in all_compartments:
    try:
        response = network_client.list_security_lists(compartment_id=compartment.id)
        for security_list in response.data:
            results.append(to_dict(security_list))

        while response.has_next_page:
            response = network_client.list_security_lists(compartment_id=compartment.id, page=response.next_page)
            for security_list in response.data:
                results.append(to_dict(security_list))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Security Lists with Open Rules (0.0.0.0/0)

```python
for compartment in all_compartments:
    try:
        response = network_client.list_security_lists(compartment_id=compartment.id)
        all_security_lists = response.data
        while response.has_next_page:
            response = network_client.list_security_lists(compartment_id=compartment.id, page=response.next_page)
            all_security_lists.extend(response.data)

        for security_list in all_security_lists:
            has_open_rules = False
            for rule in security_list.ingress_security_rules:
                if rule.source == '0.0.0.0/0':
                    has_open_rules = True
                    break

            if has_open_rules:
                results.append(to_dict(security_list))

    except oci.exceptions.ServiceError:
        continue
```

### 5. List Route Tables

```python
for compartment in all_compartments:
    try:
        response = network_client.list_route_tables(compartment_id=compartment.id)
        for route_table in response.data:
            results.append(to_dict(route_table))

        while response.has_next_page:
            response = network_client.list_route_tables(compartment_id=compartment.id, page=response.next_page)
            for route_table in response.data:
                results.append(to_dict(route_table))
    except oci.exceptions.ServiceError:
        continue
```

### 6. List Internet Gateways

```python
for compartment in all_compartments:
    try:
        response = network_client.list_internet_gateways(compartment_id=compartment.id)
        for igw in response.data:
            results.append(to_dict(igw))

        while response.has_next_page:
            response = network_client.list_internet_gateways(compartment_id=compartment.id, page=response.next_page)
            for igw in response.data:
                results.append(to_dict(igw))
    except oci.exceptions.ServiceError:
        continue
```

### 7. List NAT Gateways

```python
for compartment in all_compartments:
    try:
        response = network_client.list_nat_gateways(compartment_id=compartment.id)
        for nat_gateway in response.data:
            results.append(to_dict(nat_gateway))

        while response.has_next_page:
            response = network_client.list_nat_gateways(compartment_id=compartment.id, page=response.next_page)
            for nat_gateway in response.data:
                results.append(to_dict(nat_gateway))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Always implement pagination for all list operations
- For security list filtering, check the `ingress_security_rules` attribute
- Use `lifecycle_state` parameter for filtering by state
- Handle service errors gracefully with try/except blocks
- Network resources are compartment-scoped


