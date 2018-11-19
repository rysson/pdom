#!/bin/sh

# # Print help
# test.sh --help
#
# # Test given URL (or file):
# test.sh <URL> <SEL>...
#
# # Test given HTML snippet
# test.sh -H <HTML> <SEL>...
#
# # Test selector parser
# test.sh -S <SEL>...

cd "${0%/*}"
python3 -m pdom "$@"
