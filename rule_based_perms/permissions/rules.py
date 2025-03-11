from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models
from arches.app.search.elasticsearch_dsl_builder import Bool, Nested
from django.contrib.auth.models import User, Group
from django.db.models import Exists, OuterRef, Q
from django.db.models.fields.json import KT
from django.db.models.query import QuerySet
from django.http import HttpRequest
from rule_based_perms.models import RuleConfig


class PermissionRules:

    def __init__(self):
        self.configs = RuleConfig.objects.all()

    def filter_tile_has_value(
        self, nodegroupid, nodeid, value, user, filter="db", qs=None
    ):
        if filter == "db":
            nodegroups = [nodegroupid]
            tiles = (
                models.TileModel.objects.filter(
                    resourceinstance=OuterRef("resourceinstanceid"),
                    nodegroup_id__in=nodegroups,
                )
                .annotate(
                    node=KT(f"data__{nodeid}"),
                )
                .filter(Q(node=value))
            )
            return models.ResourceInstance.objects.filter(
                Q(Exists(tiles)) | Q(principaluser_id=user.id)
            )
        else:
            documents = Bool()
            string_factory = DataTypeFactory().get_instance("concept")
            val = {"op": "~", "val": value, "lang": "en"}
            string_factory.append_search_filters(
                val, models.Node.objects.get(nodeid=nodeid), documents, HttpRequest()
            )
            result = Bool()
            result.must(Nested(path="tiles", query=documents))
            return result

    def filter_tile_does_not_have_value(self, filter="db", actions=[], qs=None):
        pass

    def get_config_groups(self, user: User) -> QuerySet[Group]: 
        unique_user_groups = set()
        for rule_config in self.configs:
            groups = rule_config.groups.all().values_list("name", flat=True)
            unique_user_groups.update(list(groups))

        return user.groups.filter(name__in=unique_user_groups)

    def permission_handler(self, user, actions=["view_resourceinstance"], filter="db"):
        filters = {
            "filter_tile_has_value": self.filter_tile_has_value,
            "filter_tile_does_not_have_value": self.filter_tile_does_not_have_value,
        }

        user_groups = self.get_config_groups(user)
        res = None

        if len(user_groups):
            queries = []
            final_query = Bool()
            for rule_config in self.configs:
                if (rule_config.groups.all() & user_groups.all()).exists() and set(
                    rule_config.actions
                ).intersection(actions):
                    res = filters[rule_config.type](
                        rule_config.nodegroup_id,
                        rule_config.node_id,
                        rule_config.value["value"],
                        user,
                        filter,
                    )
                    if filter == "db":
                        queries.append(res)
                    else:
                        final_query.should(res)
        else:
            return models.ResourceInstance.objects.none()

        if filter == "db":
            return queries[0].union(*queries[1:]) if len(queries) > 1 else queries[0]
        else:
            return final_query
