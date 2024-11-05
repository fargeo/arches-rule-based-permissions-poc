"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import annotations

from django.contrib.auth.models import User
from arches.app.permissions.arches_default_deny import (
    ArchesDefaultDenyPermissionFramework,
)
from arches.app.search.elasticsearch_dsl_builder import Bool, Nested, Terms
from arches.app.search.search import SearchEngine
import rule_based_perms.permissions.rules as rules


class ArchesFilteredPermissionFramework(ArchesDefaultDenyPermissionFramework):

    def get_filtered_instances(
        self,
        user: User,
        search_engine: SearchEngine | None = None,
        allresources: bool = False,
        resources: list[str] | None = None,
    ):
        resources = rules.permission_handler(user)
        return self.__class__.is_exclusive, resources.values_list(
            "resourceinstanceid", flat=True
        )

    def get_permission_search_filter(self, user: User) -> Bool:
        return rules.permission_handler(user, filter="search")
