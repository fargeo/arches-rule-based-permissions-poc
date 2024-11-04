import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(re.sub(r"_", r"-", r"rule_based_perms"), "rule_based_perms.urls", name="rule_based_perms"),
)
