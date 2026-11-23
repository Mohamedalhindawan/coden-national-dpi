def transform(value):
    count = 0
    for flag in value:
        if flag == 'license_pending':
            count += 1
        elif flag == 'security_pending':
            count += 1
    return count
