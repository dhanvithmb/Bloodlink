"""Demo donor data and weighted k-nearest-neighbors ranking."""

import json
from pathlib import Path

DONORS = json.loads(Path(__file__).with_name("donors.json").read_text(encoding="utf-8"))


def _distance(left, right):
    """Distance across categorical features and normalized activity time."""
    group = left["group"] != right["group"]
    city = left["city"].casefold() != right["city"].casefold()
    minutes = abs(left["minutes"] - right["minutes"]) / 35
    return 0.4 * group + 0.35 * city + 0.25 * minutes


def _availability_probability(index, neighbors=5):
    """Predict availability from the five most similar other donor records."""
    donor = DONORS[index]
    nearest = sorted(
        ((_distance(donor, other), other_index, other)
        for other_index, other in enumerate(DONORS)
        if other_index != index),
        key=lambda item: item[0],
    )[:neighbors]
    weights = [1 / (distance + 0.05) for distance, _, _ in nearest]
    probability = sum(
        weight * int(other["available"])
        for weight, (_, _, other) in zip(weights, nearest)
    ) / sum(weights)
    return round(probability * 100)


def recommend_donors(group="all", city="all"):
    """Filter to exact requested group/city and rank by the KNN estimate."""
    group = group.upper()
    city = city.casefold()
    ranked = []
    for index, donor in enumerate(DONORS):
        if group != "ALL" and donor["group"] != group:
            continue
        if city != "all" and donor["city"].casefold() != city:
            continue
        ranked.append({**donor, "availabilityEstimate": _availability_probability(index)})

    ranked.sort(
        key=lambda donor: (
            -donor["availabilityEstimate"],
            -int(donor["available"]),
            donor["minutes"],
        )
    )
    return ranked
