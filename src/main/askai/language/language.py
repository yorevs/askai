#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.language.language
      @file: language.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from hspylib.core.enums.charset import Charset
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.preconditions import check_not_none
from hspylib.core.tools.dict_tools import get_or_default
from typing import TypeAlias

import re

AnyLocale: TypeAlias = str | tuple[str | str | None, ...]


class Language(Enumeration):
    """Enumeration to wrap all standard languages.
    Reference: https://docs.oracle.com/cd/E23824_01/html/E26033/glset.html
    """

    # fmt: off

    AF_ZA = 'af_ZA', 'Afrikaans', 'South Africa'
    AR_AE = 'ar_AE', 'Arabic', 'United Arab Emirates'
    AR_BH = 'ar_BH', 'Arabic', 'Bahrain'
    AR_DZ = 'ar_DZ', 'Arabic', 'Algeria'
    AR_EG = 'ar_EG', 'Arabic', 'Egypt'
    AR_IQ = 'ar_IQ', 'Arabic', 'Iraq'
    AR_JO = 'ar_JO', 'Arabic', 'Jordan'
    AR_KW = 'ar_KW', 'Arabic', 'Kuwait'
    AR_LY = 'ar_LY', 'Arabic', 'Libya'
    AR_MA = 'ar_MA', 'Arabic', 'Morocco'
    AR_OM = 'ar_OM', 'Arabic', 'Oman'
    AR_QA = 'ar_QA', 'Arabic', 'Qatar'
    AR_SA = 'ar_SA', 'Arabic', 'Saudi Arabia'
    AR_TN = 'ar_TN', 'Arabic', 'Tunisia'
    AR_YE = 'ar_YE', 'Arabic', 'Yemen'
    AS_IN = 'as_IN', 'Assamese', 'India'
    AZ_AZ = 'az_AZ', 'Azerbaijani', 'Azerbaijan'
    BE_BY = 'be_BY', 'Belarusian', 'Belarus'
    BG_BG = 'bg_BG', 'Bulgarian', 'Bulgaria'
    BN_IN = 'bn_IN', 'Bengali', 'India'
    BS_BA = 'bs_BA', 'Bosnian', 'Bosnia and Herzegovina'
    CA_ES = 'ca_ES', 'Catalan', 'Spain'
    CS_CZ = 'cs_CZ', 'Czech', 'Czech Republic'
    DA_DK = 'da_DK', 'Danish', 'Denmark'
    DE_AT = 'de_AT', 'German', 'Austria'
    DE_BE = 'de_BE', 'German', 'Belgium'
    DE_CH = 'de_CH', 'German', 'Switzerland'
    DE_DE = 'de_DE', 'German', 'Germany'
    DE_LI = 'de_LI', 'German', 'Liechtenstein'
    DE_LU = 'de_LU', 'German', 'Luxembourg'
    EL_CY = 'el_CY', 'Greek', 'Cyprus'
    EL_GR = 'el_GR', 'Greek', 'Greece'
    EN_AU = 'en_AU', 'English', 'Australia'
    EN_BW = 'en_BW', 'English', 'Botswana'
    EN_CA = 'en_CA', 'English', 'Canada'
    EN_GB = 'en_GB', 'English', 'United Kingdom'
    EN_HK = 'en_HK', 'English', 'Hong Kong SAR China'
    EN_IE = 'en_IE', 'English', 'Ireland'
    EN_IN = 'en_IN', 'English', 'India'
    EN_MT = 'en_MT', 'English', 'Malta'
    EN_NZ = 'en_NZ', 'English', 'New Zealand'
    EN_PH = 'en_PH', 'English', 'Philippines'
    EN_SG = 'en_SG', 'English', 'Singapore'
    EN_US = 'en_US', 'English', 'U.S.A.'
    EN_ZW = 'en_ZW', 'English', 'Zimbabwe'
    ES_AR = 'es_AR', 'Spanish', 'Argentina'
    ES_BO = 'es_BO', 'Spanish', 'Bolivia'
    ES_CL = 'es_CL', 'Spanish', 'Chile'
    ES_CO = 'es_CO', 'Spanish', 'Colombia'
    ES_CR = 'es_CR', 'Spanish', 'Costa Rica'
    ES_DO = 'es_DO', 'Spanish', 'Dominican Republic'
    ES_EC = 'es_EC', 'Spanish', 'Ecuador'
    ES_ES = 'es_ES', 'Spanish', 'Spain'
    ES_GT = 'es_GT', 'Spanish', 'Guatemala'
    ES_HN = 'es_HN', 'Spanish', 'Honduras'
    ES_MX = 'es_MX', 'Spanish', 'Mexico'
    ES_NI = 'es_NI', 'Spanish', 'Nicaragua'
    ES_PA = 'es_PA', 'Spanish', 'Panama'
    ES_PE = 'es_PE', 'Spanish', 'Peru'
    ES_PR = 'es_PR', 'Spanish', 'Puerto Rico'
    ES_PY = 'es_PY', 'Spanish', 'Paraguay'
    ES_SV = 'es_SV', 'Spanish', 'El Salvador'
    ES_US = 'es_US', 'Spanish', 'U.S.A.'
    ES_UY = 'es_UY', 'Spanish', 'Uruguay'
    ES_VE = 'es_VE', 'Spanish', 'Venezuela'
    ET_EE = 'et_EE', 'Estonian', 'Estonia'
    FI_FI = 'fi_FI', 'Finnish', 'Finland'
    FR_BE = 'fr_BE', 'French', 'Belgium'
    FR_CA = 'fr_CA', 'French', 'Canada'
    FR_CH = 'fr_CH', 'French', 'Switzerland'
    FR_FR = 'fr_FR', 'French', 'France'
    FR_LU = 'fr_LU', 'French', 'Luxembourg'
    GU_IN = 'gu_IN', 'Gujarati', 'India'
    HE_IL = 'he_IL', 'Hebrew', 'Israel'
    HI_IN = 'hi_IN', 'Hindi', 'India'
    HR_HR = 'hr_HR', 'Croatian', 'Croatia'
    HU_HU = 'hu_HU', 'Hungarian', 'Hungary'
    HY_AM = 'hy_AM', 'Armenian', 'Armenia'
    ID_ID = 'id_ID', 'Indonesian', 'Indonesia'
    IS_IS = 'is_IS', 'Icelandic', 'Iceland'
    IT_CH = 'it_CH', 'Italian', 'Switzerland'
    IT_IT = 'it_IT', 'Italian', 'Italy'
    JA_JP = 'ja_JP', 'Japanese', 'Japan'
    KA_GE = 'ka_GE', 'Georgian', 'Georgia'
    KK_KZ = 'kk_KZ', 'Kazakh', 'Kazakhstan'
    KN_IN = 'kn_IN', 'Kannada', 'India'
    KO_KR = 'ko_KR', 'Korean', 'Korea'
    KS_IN = 'ks_IN', 'Kashmiri', 'India'
    KU_TR = 'ku_TR', 'Kurdish', 'Turkey'
    KY_KG = 'ky_KG', 'Kirghiz', 'Kyrgyzstan'
    LT_LT = 'lt_LT', 'Lithuanian', 'Lithuania'
    LV_LV = 'lv_LV', 'Latvian', 'Latvia'
    MK_MK = 'mk_MK', 'Macedonian', 'Macedonia'
    ML_IN = 'ml_IN', 'Malayalam', 'India'
    MR_IN = 'mr_IN', 'Marathi', 'India'
    MS_MY = 'ms_MY', 'Malay', 'Malaysia'
    MT_MT = 'mt_MT', 'Maltese', 'Malta'
    NB_NO = 'nb_NO', 'Bokmal', 'Norway'
    NL_BE = 'nl_BE', 'Dutch', 'Belgium'
    NL_NL = 'nl_NL', 'Dutch', 'Netherlands'
    NN_NO = 'nn_NO', 'Nynorsk', 'Norway'
    OR_IN = 'or_IN', 'Oriya', 'India'
    PA_IN = 'pa_IN', 'Punjabi', 'India'
    PL_PL = 'pl_PL', 'Polish', 'Poland'
    PT_BR = 'pt_BR', 'Portuguese', 'Brazil'
    PT_PT = 'pt_PT', 'Portuguese', 'Portugal'
    RO_RO = 'ro_RO', 'Romanian', 'Romania'
    RU_RU = 'ru_RU', 'Russian', 'Russia'
    RU_UA = 'ru_UA', 'Russian', 'Ukraine'
    SA_IN = 'sa_IN', 'Sanskrit', 'India'
    SK_SK = 'sk_SK', 'Slovak', 'Slovakia'
    SL_SI = 'sl_SI', 'Slovenian', 'Slovenia'
    SQ_AL = 'sq_AL', 'Albanian', 'Albania'
    SR_ME = 'sr_ME', 'Serbian', 'Montenegro'
    SR_RS = 'sr_RS', 'Serbian', 'Serbia'
    SV_SE = 'sv_SE', 'Swedish', 'Sweden'
    TA_IN = 'ta_IN', 'Tamil', 'India'
    TE_IN = 'te_IN', 'Telugu', 'India'
    TH_TH = 'th_TH', 'Thai', 'Thailand'
    TR_TR = 'tr_TR', 'Turkish', 'Turkey'
    UK_UA = 'uk_UA', 'Ukrainian', 'Ukraine'
    VI_VN = 'vi_VN', 'Vietnamese', 'Vietnam'
    ZH_CN = 'zh_CN', 'Simplified Chinese', 'China'
    ZH_HK = 'zh_HK', 'Traditional Chinese', 'Hong Kong SAR China'
    ZH_SG = 'zh_SG', 'Chinese', 'Singapore'
    ZH_TW = 'zh_TW', 'Traditional Chinese', 'Taiwan'

    @staticmethod
    def of_locale(loc: AnyLocale) -> "Language":
        """Create a Language object based on a locale string or tuple containing the language code and encoding.
        :param loc: The locale to parse.
        :return: A Language instance corresponding to the provided locale.
        """
        # Replace possible 'loc[:.]charset' values
        loc_enc: tuple = tuple(map(
            lambda s: re.sub(r'(/C|C/|\'|\")+', '', s), loc
            if isinstance(loc, tuple)
            else re.split(r"[:.]", loc)
        ))
        # fmt: off
        lang: Language | None = next((
            Language[ln.upper()]
            for ln in list(map(
                lambda v: v.__getitem__(0), Language.values())) if ln.casefold() == loc_enc[0].casefold()
        ), None)
        # fmt: on
        check_not_none(lang, f"Unable to create Language from locale: '{loc}'")
        lang.encoding = get_or_default(loc_enc, 1, Charset.UTF_8.val)
        return lang

    def __init__(self, locale_str: str, name: str, country: str):
        loc_enc = re.split(r"[:.]", locale_str)
        self._locale: tuple[str, Charset] = loc_enc[0], get_or_default(loc_enc, 1, Charset.UTF_8.val)
        self._name: str = name
        self._country: str = country
        self._encoding: Charset = Charset.of_value(self._locale[1])
        self._idiom = self._locale[0]
        lang = locale_str.split("_")
        self._language, self._territory = lang[0], lang[1]

    def __str__(self):
        return f"{self.name} '{self.country.title()}', '{self.encoding}'"

    @property
    def locale(self) -> tuple[str, Charset]:
        """Return a tuple containing the locale attributes.
        :return: A tuple with locale attributes, e.g., (en_US, utf-8).
        """
        return self._locale

    @property
    def idiom(self) -> str:
        """Return a string representing the idiom.
        :return: The idiom as a string, e.g., en_US.
        """
        return self._idiom

    @property
    def encoding(self) -> Charset:
        """Return the charset (encoding) required for the language to be properly displayed.
        :return: The charset (encoding), e.g., utf-8.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, value: str | Charset) -> None:
        """Set the charset (encoding) required for the language to be properly displayed.
        :param value: The charset (encoding) as a string or Charset instance, e.g., utf-8.
        """
        self._encoding = value if isinstance(value, Charset) else Charset.of_value(value.casefold())

    @property
    def name(self) -> str:
        """Return the language name.
        :return: The name of the language, e.g., English.
        """
        return self._name

    @property
    def country(self) -> str:
        """Return the country where the language is spoken.
        :return: The country where the language is spoken, e.g., U.S.A.
        """
        return self._country

    @property
    def language(self) -> str:
        """Return a mnemonic representing the language.
        :return: The mnemonic representing the language, e.g., en.
        """
        return self._language

    @property
    def territory(self) -> str:
        """Return a mnemonic representing the territory (Alpha-2 code).
        :return: The mnemonic representing the territory, e.g., US.
        """
        return self._territory
