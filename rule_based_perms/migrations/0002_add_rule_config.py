# Generated by Django 4.2.17 on 2025-02-02 13:36

from django.db import migrations
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('rule_based_perms', '0001_initial'),
    ]

    def add_rule_config(apps, schema_editor):
        Group = apps.get_model("auth", "Group")
        RuleConfig = apps.get_model("rule_based_perms", "RuleConfig")
        resource_reviewers = Group.objects.get(name="Resource Reviewer")
        rc = RuleConfig.objects.create(
            id=uuid.UUID("baca30f6-96f6-4191-9fa1-f65cb0e3808d"),
            type="filter_tile_has_value",
            node_id=uuid.UUID("8f3f9562-9dc5-11ed-a2fb-0242ac130004"),
            nodegroup_id=uuid.UUID("8f3f9562-9dc5-11ed-a2fb-0242ac130004"),
            value={"value": 75, "op": "eq"},
            name="Allow access to resources with tiles that have the value 75",
        )
        rc.groups.set((resource_reviewers,))

        resource_life_cycle_config = RuleConfig.objects.create(
            id=uuid.UUID("5888b10c-429a-44e9-8297-e507c3e1085c"),
            type="filter_resource_has_lifecycle_state",
            node_id=uuid.UUID("8f3f9562-9dc5-11ed-a2fb-0242ac130004"),
            nodegroup_id=uuid.UUID("8f3f9562-9dc5-11ed-a2fb-0242ac130004"),
            value={"op": "eq","value": ["f75bb034-36e3-4ab4-8167-f520cf0b4c58"]},
            name="Allow access to resources with active state",
        )

        resource_life_cycle_config.groups.set((resource_reviewers,))

    def remove_rule_config(apps, schema_editor):
        RuleConfig = apps.get_model("rule_based_perms", "RuleConfig")
        RuleConfig.objects.get(id=uuid.UUID("baca30f6-96f6-4191-9fa1-f65cb0e3808d")).delete()
        RuleConfig.objects.get(id=uuid.UUID("5888b10c-429a-44e9-8297-e507c3e1085c")).delete()

    operations = [
        migrations.RunPython(add_rule_config, remove_rule_config),
    ]
