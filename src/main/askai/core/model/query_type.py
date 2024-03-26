from hspylib.core.enums.enumeration import Enumeration


class QueryType(Enumeration):
    """TODO"""

    ANALYSIS_QUERY      = 'AnalysisQuery'

    COMMAND_QUERY       = 'CommandQuery'

    GENERIC_QUERY       = 'GenericQuery'

    INTERNET_QUERY      = 'InternetQuery'

    OUTPUT_QUERY        = 'OutputQuery'

    SUMMARY_QUERY       = 'SummaryQuery'

    def __str__(self):
        return self.value[0]

    @property
    def proc_name(self) -> str:
        return self.value[0].replace('Query', 'Processor')
