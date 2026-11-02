INCLUDED_MIN = {"haircut": 30, "colour": 60, "spa": 90}


def extra_time_charge(service, duration_min, stylist_level, is_member):
    if service not in INCLUDED_MIN:
        raise ValueError("unknown service")
    if duration_min < 0:
        raise ValueError("invalid duration")
    included = INCLUDED_MIN[service]
    if is_member and service != "spa":
        included += 15
    extra = duration_min - included
    if extra <= 0:
        return 0
    if stylist_level == "junior":
        rate = 10
    else:
        rate = 18
    if extra > 60:
        rate = rate + 8
        if stylist_level == "senior":
            rate += 4
    return extra * rate


def can_book(party_size, services, is_walk_in):
    if is_walk_in:
        return party_size <= 2
    if party_size > 4:
        return False
    return services <= 2


def arrival_status(minutes_early, is_colour, is_weekend):
    if is_colour:
        cutoff = 10
    else:
        cutoff = 5
    if is_weekend:
        cutoff += 10
    if minutes_early >= cutoff:
        return "open"
    elif minutes_early >= cutoff - 15:
        return "late"
    return "closed"
