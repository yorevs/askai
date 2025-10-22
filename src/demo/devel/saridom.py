# Time dilation calculator with h/m/s formatting and total days if hours > 24

# Constants
time_dilation_ratio = 45.96  # 1 hour inside = 45.96 hours outside
hours_per_day = 24
days_per_year = 365.25
months_per_year = 12
days_per_month = days_per_year / months_per_year  # ≈30.44


def months_and_days(decimal_years):
    total_months = decimal_years * months_per_year
    full_months = int(total_months)
    remaining_days = (total_months - full_months) * days_per_month
    return full_months, remaining_days


def hours_to_hms_days(decimal_hours):
    total_days = decimal_hours / hours_per_day
    hours = int(decimal_hours)
    minutes_float = (decimal_hours - hours) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)
    return hours, minutes, seconds, total_days


if __name__ == '__main__':
    print("Time Dilation Calculator")
    print("Select the time direction:")
    print("1: Convert from outside → inside")
    print("2: Convert from inside → outside")

    match input("Enter 1 or 2: "):
        case "1":
            print("\nYou chose: Outside → Inside")
            print("Input unit: (1) hours, (2) days, (3) years")
            match input("Enter 1, 2, or 3: "):
                case "1":
                    outside_hours = float(input("Enter hours outside: "))
                    island_hours = outside_hours / time_dilation_ratio
                    h, m, s, d = hours_to_hms_days(island_hours)
                    print(f"\n{outside_hours:.2f} hours outside = {h} hours, {m} minutes, {s} seconds inside")
                    if island_hours > 24:
                        print(f"→ Total inside time: {d:.2f} days")

                case "2":
                    outside_days = float(input("Enter days outside: "))
                    outside_hours = outside_days * hours_per_day
                    island_hours = outside_hours / time_dilation_ratio
                    h, m, s, d = hours_to_hms_days(island_hours)
                    print(f"\n{outside_days:.2f} days outside = {h}h {m}m {s}s inside")
                    print(f"→ Total inside time: {d:.2f} days")

                case "3":
                    outside_years = float(input("Enter years outside: "))
                    outside_hours = outside_years * days_per_year * hours_per_day
                    island_hours = outside_hours / time_dilation_ratio
                    island_days = island_hours / hours_per_day
                    island_years = island_days / days_per_year
                    if island_years < 1:
                        months, days = months_and_days(island_years)
                        print(f"\n{outside_years:.2f} years outside = {months} months and {days:.1f} days inside")
                    else:
                        print(f"\n{outside_years:.2f} years outside = {island_years:.2f} years inside")
                    print(f"→ Total inside time: {island_days:.2f} days")

                case _:
                    print("Invalid unit selection.")

        case "2":
            print("\nYou chose: Inside → Outside")
            print("Input unit: (1) hours, (2) days, (3) years")
            match input("Enter 1, 2, or 3: "):
                case "1":
                    island_hours = float(input("Enter hours inside: "))
                    outside_hours = island_hours * time_dilation_ratio
                    h, m, s, d = hours_to_hms_days(outside_hours)
                    print(f"\n{island_hours:.2f} hours inside = {h} hours, {m} minutes, {s} seconds outside")
                    if outside_hours > 24:
                        print(f"→ Total outside time: {d:.2f} days")

                case "2":
                    island_days = float(input("Enter days inside: "))
                    island_hours = island_days * hours_per_day
                    outside_hours = island_hours * time_dilation_ratio
                    h, m, s, d = hours_to_hms_days(outside_hours)
                    print(f"\n{island_days:.2f} days inside = {h}h {m}m {s}s outside")
                    print(f"→ Total outside time: {d:.2f} days")

                case "3":
                    island_years = float(input("Enter years inside: "))
                    island_hours = island_years * days_per_year * hours_per_day
                    outside_hours = island_hours * time_dilation_ratio
                    outside_days = outside_hours / hours_per_day
                    outside_years = outside_days / days_per_year
                    if outside_years < 1:
                        months, days = months_and_days(outside_years)
                        print(f"\n{island_years:.2f} years inside = {months} months and {days:.1f} days outside")
                    else:
                        print(f"\n{island_years:.2f} years inside = {outside_years:.2f} years outside")
                    print(f"→ Total outside time: {outside_days:.2f} days")

                case _:
                    print("Invalid unit selection.")

        case _:
            print("Invalid direction choice. Please enter 1 or 2.")
