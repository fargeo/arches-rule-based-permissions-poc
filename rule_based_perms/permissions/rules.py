from arches.app.models import models
from django.db.models.fields.json import KT
from django.db.models import Q
from django.db.models import Exists, OuterRef


def filter_tile_has_value(nodegroupid, nodeid, value, filter="db", qs=None):
    nodegroups = [nodegroupid]
    tiles = (
        models.TileModel.objects.filter(resourceinstance=OuterRef("resourceinstanceid"), nodegroup_id__in=nodegroups)
        .annotate(
            node=KT(f"data__{nodeid}"),
        )
        .filter(Q(node__contains=value))
    )
    return models.ResourceInstance.objects.filter(Exists(tiles))


def filter_tile_does_not_have_value(filter="db", actions=[], qs=None):
    pass


filters = {
    "filter_tile_has_value": filter_tile_has_value, 
    "filter_tile_does_not_have_value": filter_tile_does_not_have_value
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
        "description": "Allow access to resources with tiles that have the value 75"
    }
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


def permission_handler(user, actions=["read"]):
    unique_user_groups = set()
    for config in configs:
        unique_user_groups.update(config["groups"])

    user_groups = user.groups.filter(name__in=unique_user_groups)
    res = None
    if len(user_groups):
        for perm in configs:
            if set(perm["groups"]).intersection(user_groups.values_list("name", flat=True)) and set(perm["actions"]).intersection(actions):
                res = filters[perm["type"]](perm["nodegroupid"], perm["nodeid"], perm["value"])

    return res
