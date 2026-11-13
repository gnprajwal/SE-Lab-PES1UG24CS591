import math


def parse_booking(text):
    if not isinstance(text, str) or ":" not in text:
        return ("", 0.0)
    parts = text.split(":")
    if len(parts) != 2:
        return ("", 0.0)
    service, minutes_str = parts
    service_clean = service.strip().title()
    if not service_clean:
        return ("", 0.0)
    try:
        minutes = float(minutes_str.strip())
        if math.isnan(minutes) or math.isinf(minutes) or minutes < 0:
            return (service_clean, 0.0)
        return (service_clean, minutes)
    except ValueError:
        return (service_clean, 0.0)


def duration_average(durations_csv):
    if not isinstance(durations_csv, str) or not durations_csv.strip():
        return 0
    values = []
    for r in durations_csv.split(","):
        r_clean = r.strip()
        if r_clean:
            try:
                val = int(r_clean)
                if val >= 0:
                    values.append(val)
            except ValueError:
                continue
    if not values:
        return 0
    return sum(values) // len(values)


def payable_bill(text):
    if not isinstance(text, str) or "|" not in text:
        return 0.0
    parts = text.split("|")
    if len(parts) != 2:
        return 0.0
    bill_str, discount_str = parts
    try:
        bill = float(bill_str.strip())
        discount = float(discount_str.strip())
        if (
            math.isnan(bill)
            or math.isinf(bill)
            or math.isnan(discount)
            or math.isinf(discount)
            or bill < 0
            or discount < 0
        ):
            return 0.0
        total = bill * 1.18 - discount
        return max(total, 0.0)
    except ValueError:
        return 0.0


def main():
    print("==== Running parse_booking ====")
    user_input = input("Enter service:duration in min (e.g. haircut:45): ")
    result = parse_booking(user_input)
    print("Service and Duration:", result)

    print("\n==== Running duration_average ====")
    user_input = input("Enter durations as CSV (e.g. 30,45,60): ")
    result = duration_average(user_input)
    print("Average Duration:", result)

    print("\n==== Running payable_bill ====")
    user_input = input("Enter bill|discount (e.g. 800|100): ")
    result = payable_bill(user_input)
    print("Payable Bill:", result)


if __name__ == "__main__":
    main()