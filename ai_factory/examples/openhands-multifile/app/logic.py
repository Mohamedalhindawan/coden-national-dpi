def transform(value):
    counts = {}
    for item in value:
        counts[item] = counts.get(item, 0) + 1
    return counts
