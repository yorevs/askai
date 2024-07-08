import re
from datetime import datetime
from textwrap import dedent

from hspylib.core.metaclass.singleton import Singleton


class CronUtils(metaclass=Singleton):
    """Provide Crontab utilities."""

    INSTANCE: 'CronUtils'

    # Cron based days of the week.
    DAY_NAME: list[str] = [
        'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

    # Calendar month names.
    MONTH_NAME: list[str] = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Define regex pattern for simple time; asterisks allowed.

    # Define regex pattern for ISO 8601 date-time; asterisks allowed.
    RE_ISO8601_DATETIME: str = r"^(\d{4}|\*)[-/](\d{2}|\*)[-/](\d{2}|\*)[T\s](\d{2}|\*):(\d{2}|\*):(\d{2}|\*)?$"

    @classmethod
    def ordinal(
        cls,
        str_num: str
    ) -> str:
        """Return the ordinal representation of a number."""
        if str_num.isdecimal():
            num = int(str_num)
            if 11 <= (num % 100) <= 13:
                suffix = 'th'
            else:
                suffix = ['th', 'st', 'nd', 'rd', 'th'][min(num % 10, 4)]
            return str(num) + suffix
        return str_num

    @classmethod
    def iso_to_cron(
        cls,
        iso_string: str,
        every_minute: bool = False,
        every_hour: bool = False,
        every_day: bool = False,
        every_month: bool = False,
        every_weekday: bool = False
    ) -> str:
        """Convert an ISO 8601 formatted date-time string to a cron expression.
        :param iso_string: ISO 8601 formatted date-time string (e.g., "2024-07-08T14:*:00"). Can include asterisks "*".
        :param every_minute: If True ignore the minute value and set it in the cron expression as '*'.
        :param every_hour: If True ignore the hour value and set it in the cron expression as '*'.
        :param every_day: If True ignore the day value and set it in the cron expression as '*'.
        :param every_month: If True ignore the month value and set it in the cron expression as '*'.
        :param every_weekday: If True ignore the weekday value and set it in the cron expression as '*'.
        :return str: A cron expression string (e.g., "45 14 8 7 1").
        """
        iso_pattern = re.compile(cls.RE_ISO8601_DATETIME)

        # Validate the ISO formatted date-time string
        if not iso_pattern.match(iso_string):
            raise ValueError("Invalid ISO date-time format")

        # Parse the ISO formatted date-time string
        parts = re.split('[T ]', iso_string)
        date_part = parts[0] if len(parts) > 0 else ''
        time_part = parts[1] if len(parts) > 1 else parts[0]

        c_date = re.split('[-/]', date_part)
        c_time = time_part.split(':')

        year, month, day = c_date[0], c_date[1], c_date[2]
        hour, minute = c_time[0], c_time[1]

        # Determine the day of the week if not using '*'
        if year != '*' and month != '*' and day != '*':
            dt = datetime(int(year), int(month), int(day))
            weekday = (dt.weekday() + 1) % 7  # Convert to cron format (Sunday is '0' or '7')
        else:
            weekday = '*'

        # Adjust fields based on boolean parameters
        minute = '*' if every_minute else f"{int(minute) if minute != '*' else '*'}"
        hour = '*' if every_hour else f"{int(hour) if hour != '*' else '*'}"
        day = '*' if every_day else f"{int(day) if day != '*' else '*'}"
        month = '*' if every_month else f"{int(month) if month != '*' else '*'}"
        weekday = '*' if every_weekday else f"{int(weekday) if weekday != '*' else '*'}"

        return f"{minute} {hour} {day} {month} {weekday}"

    @classmethod
    def human_readable_cron(
        cls,
        cron_expression: str
    ) -> str:
        """
        Generate a human-readable explanation for the given cron expression.

        Parameters:
        cron_expression (str): A cron expression string (e.g., "45 14 8 7 1").

        Returns:
        str: A human-readable explanation of the cron expression.
        """
        components = cron_expression.split()

        if len(components) != 5:
            raise ValueError("Invalid cron expression. It should have exactly 5 components.")

        minute, hour, day, month, weekday = components
        explanation = []
        dom = cls.ordinal(day)

        explanation.append('Runs')
        if hour == '*' and day == '*' and month == '*' and weekday == '*':
            explanation.append(f"every {minute + ' minute(s)' if minute != '*' else 'minute'} every day.")
        else:
            if hour == '*':
                explanation.append(f"every {cls.ordinal(minute) + ' ' if minute != '*' else ''}minute of every hour")
            else:
                time = f"at {minute if minute != '*' else 'every minute'}"
                time += f" past {hour}"
                explanation.append(f"{time}")

            if day != '*' and month != '*' and weekday != '*':
                explanation.append(
                    f"on the {dom} and every {cls.DAY_NAME[int(weekday)]} in {cls.MONTH_NAME[int(month) - 1]}.")
            elif day != '*' and month != '*' and weekday == '*':
                explanation.append(f"on {cls.MONTH_NAME[int(month) - 1]} {dom}.")
            elif day == '*' and month != '*' and weekday != '*':
                explanation.append(f"every {cls.DAY_NAME[int(weekday)]} in {cls.MONTH_NAME[int(month) - 1]}.")
            elif day != '*' and month == '*' and weekday != '*':
                explanation.append(f"every month on {cls.DAY_NAME[int(weekday)]}.")
            elif day == '*' and month == '*' and weekday != '*':
                explanation.append(f"every {cls.DAY_NAME[int(weekday)]}.")
            elif day != '*' and month == '*' and weekday == '*':
                explanation.append(f"every month, on the {dom} day.")
            elif day == '*' and month != '*' and weekday == '*':
                explanation.append(f"every day in {cls.MONTH_NAME[int(month) - 1]}.")
            elif day != '*' and month == '*' and weekday == '*':
                explanation.append(f"every month, on the {dom} day.")
            else:
                explanation.append(f", every day.")

        return ' '.join(explanation).replace(" .", ".").replace("the *th ", "every ").replace('* minutes', 'minute')

    @classmethod
    def explain_cron(
        cls,
        cron_exp: str
    ) -> str:
        """Explain a cron expression in human-readable format.
        :param cron_exp: A cron expression string (e.g., "45 14 * * 1").
        :return str: A detailed explanation of the cron expression.
        """

        def sep(digits: str | int) -> str:
            sep_str: str = ' ' * len(str(digits))
            return f'|{sep_str}'

        if (components := cron_exp.split()) and (lc := len(components)) != 5:
            raise ValueError(f"Invalid cron expression. It should have exactly 5 components, but found {lc}")

        # Split the cron expression into its components
        minute, hour, day, month, weekday = components
        padding = 2
        s4 = f"{sep(minute)}{sep(hour)}{sep(day)}{sep(month)}"
        s3 = f"{sep(minute)}{sep(hour)}{sep(day)}"
        s2 = f"{sep(minute)}{sep(hour)}"
        s1 = f"{sep(minute)}"

        l5 = len(cron_exp) + padding
        l4 = l5 - len(s1)
        l3 = l5 - len(s2)
        l2 = l5 - len(s3)
        l1 = l5 - len(s4)

        d5 = f"+{'-' * l5}"
        d4 = f"+{'-' * l4}"
        d3 = f"+{'-' * l3}"
        d2 = f"+{'-' * l2}"
        d1 = f"+{'-' * l1}"

        # Create explanations for each component
        moy_str: str = cls.MONTH_NAME[int(month) - 1] if month != '*' else '*'
        dow_str: str = cls.DAY_NAME[int(weekday)] if weekday != '*' else '*'

        minute_exp = f"{d5} [0-59]  Minute: '{cls.ordinal(minute) + ' minute' if minute != '*' else 'Every minute'}'"
        hour_exp = f"{s1}{d4} [0-23]    Hour: '{cls.ordinal(hour) + ' hour' if hour != '*' else 'Every hour'}'"
        day_exp = f"{s2}{d3} [1-31]     Day: '{cls.ordinal(day) + ' day' if day != '*' else 'Every day'}'"
        month_exp = f"{s3}{d2} [1-12]   Month: '{moy_str if month != '*' else 'Every month'}'"
        day_of_week_exp = f"{s4}{d1} [0-7]  Weekday: '{dow_str if dow_str != '*' else 'Every weekday'}'"

        # Combine explanations into a single string
        explanation = dedent(f"""
        {cron_exp}
        {'-' * len(minute)} {'-' * len(hour)} {'-' * len(day)} {'-' * len(month)} {'-' * len(weekday)}
        {sep(minute)}{sep(hour)}{sep(day)}{sep(month)}{sep(weekday)}
        {day_of_week_exp}
        {month_exp}
        {day_exp}
        {hour_exp}
        {minute_exp}
        """).strip()

        return f"\n{explanation}\n"


assert (cron := CronUtils().INSTANCE) is not None


if __name__ == '__main__':
    cron_e = cron.iso_to_cron('2024/08/12 *:*:00', every_weekday=True)
    print(cron.explain_cron(cron_e))
    print(cron.human_readable_cron(cron_e))
    cron_e = cron.iso_to_cron('2024/*/09T*:*:00')
    print(cron.explain_cron(cron_e))
    print(cron.human_readable_cron(cron_e))
