from django.http import HttpRequest
from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models
from django.db.models.fields.json import KT
from django.db.models import Q
from django.db.models import Exists, OuterRef

from arches.app.search.elasticsearch_dsl_builder import Bool, Nested, Terms


def filter_tile_has_value(nodegroupid, nodeid, value, filter="db", qs=None):
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
            .filter(Q(node__contains=value))
        )
        return models.ResourceInstance.objects.filter(Exists(tiles))
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


def filter_tile_does_not_have_value(filter="db", actions=[], qs=None):
    pass


filters = {
    "filter_tile_has_value": filter_tile_has_value,
    "filter_tile_does_not_have_value": filter_tile_does_not_have_value,
}


# REQUIRES synthetic-resources APP
configs = [  # This will be a table. Records indicating which filters apply to each group
    {
        "type": "filter_tile_has_value",
        "ohp_resource": "ohp_resource",
        "nodeid": "8f3f9562-9dc5-11ed-a2fb-0242ac130004",
        "nodegroupid": "8f3f9562-9dc5-11ed-a2fb-0242ac130004",
        "value": 2,
        "groups": ["Resource Reviewer", "Graph Designer"],
        "actions": ["read"],
        "description": "Allow access to resources with tiles that have the value 75",
    },
    {
        "type": "filter_tile_has_value",
        "ohp_resource": "ohp_resource",
        "nodeid": "3faca866-29c7-11ef-ad5f-faffc210b420",
        "nodegroupid": "5b11ec40-1d2b-11ef-bfd8-faffc210b420",
        "value": "14a04982-f28c-406b-94ce-2d889769c421",
        "groups": ["EIC Viewer"],
        "actions": ["read"],
        "description": "Allow access to resources with EIC value",
    },
]
# perms = {
#     'elite_group': {
#         'return_confidential_resources': ['read'],
#     }
#     'ohp_group': {
#         'return_ohp_resources': ['read', 'write', 'delete'],
#     },
#     'ndic': {
#         'return_ndic_resources': ['read', 'write', 'delete'],
#         'return_ohp_resources': ['read']
#     },
#     'ohp_intern_group': {
#         'return_ohp_resources_without_confidential': ['read', 'write', 'delete'],
#     },
# }


def permission_handler(user, actions=["read"], filter="db"):
    unique_user_groups = set()
    for config in configs:
        unique_user_groups.update(config["groups"])

    user_groups = user.groups.filter(name__in=unique_user_groups)
    res = None
    if len(user_groups):
        for perm in configs:
            if set(perm["groups"]).intersection(
                user_groups.values_list("name", flat=True)
            ) and set(perm["actions"]).intersection(actions):
                res = filters[perm["type"]](
                    perm["nodegroupid"], perm["nodeid"], perm["value"], filter
                )

    return res
