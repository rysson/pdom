#!/bin/bash

# # Print help
# pdom-run.sh --help
#
# # Test given URL (or file):
# pdom-run.sh <URL> <SEL>...
#
# # Test given HTML snippet
# pdom-run.sh -H <HTML> <SEL>...
#
# # Test selector parser
# pdom-test.sh -S <SEL>...


python3 --version  >/dev/null 2>&1 && hasPy3='y'

py()
{
  local p="$1"
  shift
  case "$p" in
    python*)  "$p" "$@" ;;
    [23])     "python$1" "$@" ;;
    "")       [ y = "$hasPy3" ] && python3 "$@" || python "$@"
  esac
}

has()
{
  py "$1" -c 'import '"$2" >/dev/null 2>&1
}

if has python3 pdom; then
  has python3 requests || python3 -m pip install requests
  python3 - "$@" << EOF
import pdom.main
import sys
print(sys.argv)
if __name__ == "__main__":
    exit(pdom.main.main())
EOF
elif has pdom python; then
  has python requests || python -m pip install requests
  python - "$@" << EOF
import pdom.main
if __name__ == "__main__":
    exit(pdom.main.main())
EOF
else
  cd "${0%/*}/.."
  py '' -m pdom "$@"
fi


