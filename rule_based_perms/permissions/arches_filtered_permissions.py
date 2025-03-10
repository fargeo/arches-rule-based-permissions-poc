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
from django.contrib.gis.db.models import Model
from arches.app.search.search import SearchEngine
from arches.app.models.models import NodeGroup
from guardian.backends import check_support
from guardian.exceptions import WrongAppError
from arches.app.permissions.arches_permission_base import (ObjectPermissionChecker,
                                                           CachedObjectPermissionChecker,
                                                           CachedUserPermissionChecker)
import rule_based_perms.permissions.rules as rules


class ArchesFilteredPermissionFramework(ArchesDefaultDenyPermissionFramework):
    def __init__(self):
        self.rules = rules.PermissionRules()

    def get_filtered_instances(
        self,
        user: User,
        search_engine: SearchEngine | None = None,
        allresources: bool = False,
        resources: list[str] | None = None,
    ):
        resources = self.rules.permission_handler(user)
        return self.__class__.is_exclusive, resources.values_list(
            "resourceinstanceid", flat=True
        )

    def get_permission_search_filter(self, user: User) -> Bool:
        rule_access = self.rules.permission_handler(user, filter="search")
        principal_user = Terms(field="permissions.principal_user", terms=[str(user.id)])
        principal_user_term_filter = Nested(path="permissions", query=principal_user)
        has_access = Bool()
        has_access.should(principal_user_term_filter)
        if rule_access:
            has_access.should(rule_access)
        return has_access

    def has_perm(self, user_obj: User, perm: str, obj: Model | None = None) -> bool:
        if isinstance(obj, NodeGroup):
            # check if user_obj and object are supported (pulled directly from guardian)
            support, user_obj = check_support(user_obj, obj)
            if not support:
                return False

            if "." in perm:
                app_label, perm = perm.split(".")
                if app_label != obj._meta.app_label:
                    raise WrongAppError(
                        "Passed perm has app label of '%s' and "
                        "given obj has '%s'" % (app_label, obj._meta.app_label)
                    )

            if user_obj.is_superuser:
                return True

            obj_checker: ObjectPermissionChecker = CachedObjectPermissionChecker(
                user_obj, obj
            )
            explicitly_defined_perms = obj_checker.get_perms(obj)

            if len(explicitly_defined_perms) > 0:
                if "no_access_to_nodegroup" in explicitly_defined_perms:
                    return False
                else:
                    return perm in explicitly_defined_perms
            else:
                user_checker = CachedUserPermissionChecker(user_obj)
                return user_checker.user_has_permission(perm)
            
        else:
            if user_obj.is_superuser:
                return True
            resources = self.rules.permission_handler(user_obj, filter="db", actions=[perm])
            print('checking', resources, perm)
            return resources.filter(resourceinstanceid=obj.resourceinstanceid).exists()
        # return super().has_perm(user_obj, perm, obj)