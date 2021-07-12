import pulumi


def get_route53_record_name_by_convention(record_name, record_type, suffix=None):
    resource_name = f"{record_name}-{record_type}"
    if suffix is not None:
        suffix += 1
        # since all arrays are starting at 0 we must always add one to make it count form 1
        resource_name = f"{resource_name}_{suffix}"
    resource_name_tag = {'Name': resource_name}
    return resource_name, resource_name_tag
