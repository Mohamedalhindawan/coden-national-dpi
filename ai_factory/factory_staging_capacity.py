"""Estimate staged archive payload allocation; never install, extract or delete inputs."""


def plan_staging(records, *, capacity_bytes=960 * 1024**2, reserve_bytes=0,
                 page_bytes=4096):
    """Model replacement of verified disposable archives, not an install order.

    Expanded bytes plus per-member page rounding bound payload only. Source,
    filesystem metadata, installer duplication and output need separate evidence.
    No result from this function grants build permission.
    """
    for value in (capacity_bytes, reserve_bytes, page_bytes):
        if type(value) is not int or value < 0:
            raise ValueError('invalid budget')
    if (capacity_bytes == 0 or reserve_bytes > capacity_bytes or
            page_bytes == 0 or page_bytes & (page_bytes - 1)):
        raise ValueError('invalid capacity, reserve or page size')
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError('nonempty input inventory required')
    seen = set()
    inputs = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('invalid inventory record')
        name = record.get('name')
        if not isinstance(name, str) or not name or name.strip() != name or name in seen:
            raise ValueError('invalid or duplicate input name')
        compressed, expanded, members = (record.get(k) for k in
                                          ('compressed_bytes', 'expanded_bytes', 'members'))
        if (any(type(v) is not int for v in (compressed, expanded, members)) or
                compressed <= 0 or expanded < 0 or members <= 0):
            raise ValueError('invalid inventory counts')
        seen.add(name)
        rounded = ((compressed + page_bytes - 1) // page_bytes) * page_bytes
        inputs.append((name, rounded, expanded + (page_bytes - 1) * members))
    initial = sum(c for _, c, _ in inputs)
    concurrent = initial + sum(e for _, _, e in inputs)
    current = peak = initial
    steps = []
    # Minimize this replacement model's peak: reclaiming jobs first,
    # ordered by expanded payload; growing jobs last, ordered by decreasing
    # compressed payload. The adjacent-swap rule minimizes max(e1, d1+e2)
    # where d1=e1-c1; it does not model real installer or filesystem overhead.
    def staging_order(row):
        name, compressed, expanded = row
        return (0, expanded, name) if expanded <= compressed else (1, -compressed, name)

    for name, compressed, expanded in sorted(inputs, key=staging_order):
        transient = current + expanded
        current = transient - compressed
        peak = max(peak, transient)
        steps.append({'name': name, 'transient_bytes': transient,
                      'after_reclaim_bytes': current})
    return {'initial_bytes': initial, 'concurrent_bytes': concurrent,
            'peak_bytes': peak, 'remaining_bytes': capacity_bytes - peak,
            'reserve_bytes': reserve_bytes,
            'fits_model': peak + reserve_bytes <= capacity_bytes,
            'steps': steps, 'actual_peak_build_capacity_proven': False,
            'build_authorized': False, 'release_authorized': False}
