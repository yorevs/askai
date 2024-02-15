import re

from hspylib.core.enums.charset import Charset
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.tools.dict_tools import get_or_default
from typing import Tuple


class Language(Enumeration):
    """Enumeration to wrap all standard languages.
    Ref:. https://docs.oracle.com/cd/E23824_01/html/E26033/glset.html
    """

    # fmt: off

    AF_ZA = 'af_ZA.utf-8', 'Afrikaans', 'South Africa'
    AR_AE = 'ar_AE.utf-8', 'Arabic', 'United Arab Emirates'
    AR_BH = 'ar_BH.utf-8', 'Arabic', 'Bahrain'
    AR_DZ = 'ar_DZ.utf-8', 'Arabic', 'Algeria'
    AR_EG = 'ar_EG.utf-8', 'Arabic', 'Egypt'
    AR_IQ = 'ar_IQ.utf-8', 'Arabic', 'Iraq'
    AR_JO = 'ar_JO.utf-8', 'Arabic', 'Jordan'
    AR_KW = 'ar_KW.utf-8', 'Arabic', 'Kuwait'
    AR_LY = 'ar_LY.utf-8', 'Arabic', 'Libya'
    AR_MA = 'ar_MA.utf-8', 'Arabic', 'Morocco'
    AR_OM = 'ar_OM.utf-8', 'Arabic', 'Oman'
    AR_QA = 'ar_QA.utf-8', 'Arabic', 'Qatar'
    AR_SA = 'ar_SA.utf-8', 'Arabic', 'Saudi Arabia'
    AR_TN = 'ar_TN.utf-8', 'Arabic', 'Tunisia'
    AR_YE = 'ar_YE.utf-8', 'Arabic', 'Yemen'
    AS_IN = 'as_IN.utf-8', 'Assamese', 'India'
    AZ_AZ = 'az_AZ.utf-8', 'Azerbaijani', 'Azerbaijan'
    BE_BY = 'be_BY.utf-8', 'Belarusian', 'Belarus'
    BG_BG = 'bg_BG.utf-8', 'Bulgarian', 'Bulgaria'
    BN_IN = 'bn_IN.utf-8', 'Bengali', 'India'
    BS_BA = 'bs_BA.utf-8', 'Bosnian', 'Bosnia and Herzegovina'
    CA_ES = 'ca_ES.utf-8', 'Catalan', 'Spain'
    CS_CZ = 'cs_CZ.utf-8', 'Czech', 'Czech Republic'
    DA_DK = 'da_DK.utf-8', 'Danish', 'Denmark'
    DE_AT = 'de_AT.utf-8', 'German', 'Austria'
    DE_BE = 'de_BE.utf-8', 'German', 'Belgium'
    DE_CH = 'de_CH.utf-8', 'German', 'Switzerland'
    DE_DE = 'de_DE.utf-8', 'German', 'Germany'
    DE_LI = 'de_LI.utf-8', 'German', 'Liechtenstein'
    DE_LU = 'de_LU.utf-8', 'German', 'Luxembourg'
    EL_CY = 'el_CY.utf-8', 'Greek', 'Cyprus'
    EL_GR = 'el_GR.utf-8', 'Greek', 'Greece'
    EN_AU = 'en_AU.utf-8', 'English', 'Australia'
    EN_BW = 'en_BW.utf-8', 'English', 'Botswana'
    EN_CA = 'en_CA.utf-8', 'English', 'Canada'
    EN_GB = 'en_GB.utf-8', 'English', 'United Kingdom'
    EN_HK = 'en_HK.utf-8', 'English', 'Hong Kong SAR China'
    EN_IE = 'en_IE.utf-8', 'English', 'Ireland'
    EN_IN = 'en_IN.utf-8', 'English', 'India'
    EN_MT = 'en_MT.utf-8', 'English', 'Malta'
    EN_NZ = 'en_NZ.utf-8', 'English', 'New Zealand'
    EN_PH = 'en_PH.utf-8', 'English', 'Philippines'
    EN_SG = 'en_SG.utf-8', 'English', 'Singapore'
    EN_US = 'en_US.utf-8', 'English', 'U.S.A.'
    EN_ZW = 'en_ZW.utf-8', 'English', 'Zimbabwe'
    ES_AR = 'es_AR.utf-8', 'Spanish', 'Argentina'
    ES_BO = 'es_BO.utf-8', 'Spanish', 'Bolivia'
    ES_CL = 'es_CL.utf-8', 'Spanish', 'Chile'
    ES_CO = 'es_CO.utf-8', 'Spanish', 'Colombia'
    ES_CR = 'es_CR.utf-8', 'Spanish', 'Costa Rica'
    ES_DO = 'es_DO.utf-8', 'Spanish', 'Dominican Republic'
    ES_EC = 'es_EC.utf-8', 'Spanish', 'Ecuador'
    ES_ES = 'es_ES.utf-8', 'Spanish', 'Spain'
    ES_GT = 'es_GT.utf-8', 'Spanish', 'Guatemala'
    ES_HN = 'es_HN.utf-8', 'Spanish', 'Honduras'
    ES_MX = 'es_MX.utf-8', 'Spanish', 'Mexico'
    ES_NI = 'es_NI.utf-8', 'Spanish', 'Nicaragua'
    ES_PA = 'es_PA.utf-8', 'Spanish', 'Panama'
    ES_PE = 'es_PE.utf-8', 'Spanish', 'Peru'
    ES_PR = 'es_PR.utf-8', 'Spanish', 'Puerto Rico'
    ES_PY = 'es_PY.utf-8', 'Spanish', 'Paraguay'
    ES_SV = 'es_SV.utf-8', 'Spanish', 'El Salvador'
    ES_US = 'es_US.utf-8', 'Spanish', 'U.S.A.'
    ES_UY = 'es_UY.utf-8', 'Spanish', 'Uruguay'
    ES_VE = 'es_VE.utf-8', 'Spanish', 'Venezuela'
    ET_EE = 'et_EE.utf-8', 'Estonian', 'Estonia'
    FI_FI = 'fi_FI.utf-8', 'Finnish', 'Finland'
    FR_BE = 'fr_BE.utf-8', 'French', 'Belgium'
    FR_CA = 'fr_CA.utf-8', 'French', 'Canada'
    FR_CH = 'fr_CH.utf-8', 'French', 'Switzerland'
    FR_FR = 'fr_FR.utf-8', 'French', 'France'
    FR_LU = 'fr_LU.utf-8', 'French', 'Luxembourg'
    GU_IN = 'gu_IN.utf-8', 'Gujarati', 'India'
    HE_IL = 'he_IL.utf-8', 'Hebrew', 'Israel'
    HI_IN = 'hi_IN.utf-8', 'Hindi', 'India'
    HR_HR = 'hr_HR.utf-8', 'Croatian', 'Croatia'
    HU_HU = 'hu_HU.utf-8', 'Hungarian', 'Hungary'
    HY_AM = 'hy_AM.utf-8', 'Armenian', 'Armenia'
    ID_ID = 'id_ID.utf-8', 'Indonesian', 'Indonesia'
    IS_IS = 'is_IS.utf-8', 'Icelandic', 'Iceland'
    IT_CH = 'it_CH.utf-8', 'Italian', 'Switzerland'
    IT_IT = 'it_IT.utf-8', 'Italian', 'Italy'
    JA_JP = 'ja_JP.utf-8', 'Japanese', 'Japan'
    KA_GE = 'ka_GE.utf-8', 'Georgian', 'Georgia'
    KK_KZ = 'kk_KZ.utf-8', 'Kazakh', 'Kazakhstan'
    KN_IN = 'kn_IN.utf-8', 'Kannada', 'India'
    KO_KR = 'ko_KR.utf-8', 'Korean', 'Korea'
    KS_IN = 'ks_IN.utf-8', 'Kashmiri', 'India'
    KU_TR = 'ku_TR.utf-8', 'Kurdish', 'Turkey'
    KY_KG = 'ky_KG.utf-8', 'Kirghiz', 'Kyrgyzstan'
    LT_LT = 'lt_LT.utf-8', 'Lithuanian', 'Lithuania'
    LV_LV = 'lv_LV.utf-8', 'Latvian', 'Latvia'
    MK_MK = 'mk_MK.utf-8', 'Macedonian', 'Macedonia'
    ML_IN = 'ml_IN.utf-8', 'Malayalam', 'India'
    MR_IN = 'mr_IN.utf-8', 'Marathi', 'India'
    MS_MY = 'ms_MY.utf-8', 'Malay', 'Malaysia'
    MT_MT = 'mt_MT.utf-8', 'Maltese', 'Malta'
    NB_NO = 'nb_NO.utf-8', 'Bokmal', 'Norway'
    NL_BE = 'nl_BE.utf-8', 'Dutch', 'Belgium'
    NL_NL = 'nl_NL.utf-8', 'Dutch', 'Netherlands'
    NN_NO = 'nn_NO.utf-8', 'Nynorsk', 'Norway'
    OR_IN = 'or_IN.utf-8', 'Oriya', 'India'
    PA_IN = 'pa_IN.utf-8', 'Punjabi', 'India'
    PL_PL = 'pl_PL.utf-8', 'Polish', 'Poland'
    PT_BR = 'pt_BR.utf-8', 'Portuguese', 'Brazil'
    PT_PT = 'pt_PT.utf-8', 'Portuguese', 'Portugal'
    RO_RO = 'ro_RO.utf-8', 'Romanian', 'Romania'
    RU_RU = 'ru_RU.utf-8', 'Russian', 'Russia'
    RU_UA = 'ru_UA.utf-8', 'Russian', 'Ukraine'
    SA_IN = 'sa_IN.utf-8', 'Sanskrit', 'India'
    SK_SK = 'sk_SK.utf-8', 'Slovak', 'Slovakia'
    SL_SI = 'sl_SI.utf-8', 'Slovenian', 'Slovenia'
    SQ_AL = 'sq_AL.utf-8', 'Albanian', 'Albania'
    SR_ME = 'sr_ME.utf-8', 'Serbian', 'Montenegro'
    SR_RS = 'sr_RS.utf-8', 'Serbian', 'Serbia'
    SV_SE = 'sv_SE.utf-8', 'Swedish', 'Sweden'
    TA_IN = 'ta_IN.utf-8', 'Tamil', 'India'
    TE_IN = 'te_IN.utf-8', 'Telugu', 'India'
    TH_TH = 'th_TH.utf-8', 'Thai', 'Thailand'
    TR_TR = 'tr_TR.utf-8', 'Turkish', 'Turkey'
    UK_UA = 'uk_UA.utf-8', 'Ukrainian', 'Ukraine'
    VI_VN = 'vi_VN.utf-8', 'Vietnamese', 'Vietnam'
    ZH_CN = 'zh_CN.utf-8', 'Simplified Chinese', 'China'
    ZH_HK = 'zh_HK.utf-8', 'Traditional Chinese', 'Hong Kong SAR China'
    ZH_SG = 'zh_SG.utf-8', 'Chinese', 'Singapore'
    ZH_TW = 'zh_TW.utf-8', 'Traditional Chinese', 'Taiwan'

    # fmt: on

    @staticmethod
    def of_locale(locale: str | Tuple[str, str, str]) -> "Language":
        """Create a Language object based on a locale string or tuple containing the language code and encoding.
        :param locale: The locale to parse.
        """
        # Replace possible 'loc:charset' values
        loc_enc: tuple = locale if isinstance(locale, tuple) else tuple(re.split(r'[:.]', locale))
        lang = get_or_default(loc_enc, 0, Language.EN_US.language)
        encoding = get_or_default(loc_enc, 1, Charset.UTF_8.val).lower()
        locale = f"{lang}.{encoding}"
        return next((Language.of_value(ln) for ln in Language.values() if ln[0] == locale), None)

    def __init__(self, locale: str, name: str, country: str):
        self._locale: tuple = tuple(re.split(r'[:.]', locale))
        self._name: str = name
        self._country: str = country
        self._encoding: Charset = Charset.of_value(self._locale[1])
        self._idiom = self._locale[0]
        lang = locale.split('_')
        self._language, self._territory = lang[0], lang[1]

    def __str__(self):
        return f"Language(Name='{self.name}'  Country='{self.country}'  Encoding='{self.encoding}')"

    @property
    def locale(self) -> tuple:
        return self._locale

    @property
    def idiom(self) -> str:
        return self._idiom

    @property
    def name(self) -> str:
        return self._name

    @property
    def country(self) -> str:
        return self._country

    @property
    def language(self) -> str:
        return self._language

    @property
    def territory(self) -> str:
        return self._territory

    @property
    def encoding(self) -> Charset:
        return self._encoding
