V_TAG_NAME="v1.2.9"
VERSION="${V_TAG_NAME#v}"
CUR_DATE="$(git log -1 v"${VERSION}" --pretty=format:'%ad' --date=format:'%Y/%m/%d')"
CUR_DATE="${CUR_DATE:-$(date '+%Y/%m/%d')}"
CHG_LOG="$(git log --oneline --pretty='%h %ad %s' --date=short v"${VERSION}"..HEAD)"
CHG_LOG_UNIQ="$(echo "${CHG_LOG}" | tr -s '[:blank:]' ' ' | cut -d ' ' -f3- | sed -E 's/[[:space:]]*-[[:space:]]*[0-9]+//' | awk '!seen[$0]++' | grep -Ev '^[[:space:]]*(Merge|New)\b' | sort | uniq)"

ADDED=$(echo "${CHG_LOG_UNIQ}" | grep -Ei '^[Aa](dd(ing)?|dded)\b' | tr -s '[:blank:]' ' ' | cut -d ' ' -f2- | sed 's/^/* Added: /')
FIXED=$(echo "${CHG_LOG_UNIQ}" | grep -Ei '^([Bb]ug)?[Ff](ix(ing|ups)?|ixed)\b' | tr -s '[:blank:]' ' ' | cut -d ' ' -f2- | sed 's/^/* Fixed: /')
UPDATED=$(echo "${CHG_LOG_UNIQ}" | grep -Ei '^[Uu](pdat(e|ing)|pdated)\b' | tr -s '[:blank:]' ' ' | cut -d ' ' -f2- | sed 's/^/* Updated: /')
OTHER=$(echo "${CHG_LOG_UNIQ}" | grep -Ev '^([Aa](dd(ing)?|dded)|([Bb]ug)?[Ff](ix(ing|ups)?|ixed))|([Uu](pdat(e|ing)|pdated))|([Rr](emov(e|ing)|emoved)))\b' | sed 's/^/* Updated: /')
REMOVED=$(echo "${CHG_LOG_UNIQ}" | grep -Ei '^[Rr](emov(e|ing)|emoved)\b' | tr -s '[:blank:]' ' ' | cut -d ' ' -f2- | sed 's/^/* Removed: /')

OUTPUT="## Changelog v${VERSION} - ${CUR_DATE}

> The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/).
----

### Added

${ADDED:-**Nothing has been added**}

### Fixed

${FIXED:-**Nothing has been fixed**}

### Updated

${UPDATED:-**No updates**}
${OTHER}

### Removed

${REMOVED:-**Nothing has been removed**}
"
OUTPUT_ESCAPED="$(echo "${OUTPUT}" | sed 's/^%[][()\/\\`$"'"'"']/\\&/g')"
echo "$OUTPUT_ESCAPED"
