#!/usr/bin/env bash

if [ $# -ne 1 ]; then
    exit 1;
fi

filename=$(cut -d ";" -f 1 <<< "$1")
URL=$(cut -d ";" -f 2 <<< "$1")

# Make sure to check both URL *and* redirections (--location) for excluded domains
full_info=$(curl -I --silent --insecure --location -- "$URL")
LOCATION=$(curl -I --silent --insecure -- "$URL" | perl -n -e '/^[Ll]ocation: (.*)$/ && print "$1\n"')
if [[ "$full_info + $URL" =~ 'drive.google.com'|'pipeline-hemis'|'sciencedirect.com'|'wiley.com'|'sagepub.com'|'ncbi.nlm.nih.gov'|'oxfordjournals.org'|'docker.com'|'ieeexplore.ieee.org'|'liebertpub.com'|'tandfonline.com'|'pnas.org'|'neurology.org'|'academic.oup.com'|'journals.lww.com'|'science.org'|'%s' ]]; then
    echo -e "$filename: \x1B[33m⚠️  Warning - Skipping: $URL --> $LOCATION\x1B[0m"
    exit 0
fi

# Get the status code for the original URL
status_code=$(curl --write-out '%{http_code}' --silent --insecure --output /dev/null -- "$URL")

# If there is a redirection, then re-run curl with --location, then continue to check success/failure
if [[ $status_code -ge 300 && $status_code -le 399 ]];then
    echo "($status_code) $URL ($filename)" >> redirected_urls.txt
    echo -e "$filename: \x1B[33m⚠️  Warning - Redirection - code: $status_code for URL $URL --> $LOCATION \x1B[0m"
    status_code=$(curl --write-out '%{http_code}' --silent --insecure --location --output /dev/null -- "$URL")
    URL=$LOCATION
fi

# Check for success
if [[ $status_code -ge 200 && $status_code -le 299 ]];then
    echo "($status_code) $URL ($filename)" >> valid_urls.txt
    echo -e "$filename: \x1B[32m✅ OK status code: $status_code for domain $URL  \x1B[0m"
    exit 0
fi

# Report failure
echo "($status_code) $URL ($filename)" >> invalid_urls.txt
echo -e "$filename: \x1B[31m⛔ Error status code: $status_code for URL: $URL \x1B[0m"
