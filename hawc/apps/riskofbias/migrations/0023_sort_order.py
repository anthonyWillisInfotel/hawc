# Generated by Django 3.1.3 on 2021-05-13 16:45

import django.core.validators
from django.db import migrations, models


def set_default_sort_order(apps, schema_editor):
    Assessment = apps.get_model("assessment", "Assessment")
    RiskOfBiasDomain = apps.get_model("riskofbias", "RiskOfBiasDomain")
    RiskOfBiasMetric = apps.get_model("riskofbias", "RiskOfBiasMetric")

    assessments = Assessment.objects.all()
    all_domains = []
    for assessment in assessments:
        domains = list(assessment.rob_domains.all())
        for idx, domain in enumerate(domains, start=1):
            domain.sort_order = idx
        all_domains.extend(domains)
    RiskOfBiasDomain.objects.bulk_update(all_domains, ["sort_order"])

    domains = RiskOfBiasDomain.objects.all()
    all_metrics = []
    for domain in domains:
        metrics = domain.metrics.all()
        for idx, metric in enumerate(metrics, start=1):
            metric.sort_order = idx
        all_metrics.extend(metrics)
    RiskOfBiasMetric.objects.bulk_update(all_metrics, ["sort_order"])


class Migration(migrations.Migration):

    dependencies = [
        ("riskofbias", "0022_new_rob_scores"),
    ]

    operations = [
        migrations.AddField(
            model_name="riskofbiasdomain",
            name="sort_order",
            field=models.PositiveSmallIntegerField(
                default=0, validators=[django.core.validators.MinValueValidator(1)]
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="riskofbiasmetric",
            name="sort_order",
            field=models.PositiveSmallIntegerField(
                default=0, validators=[django.core.validators.MinValueValidator(1)]
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="riskofbiasdomain", options={"ordering": ("assessment", "sort_order")},
        ),
        migrations.AlterModelOptions(
            name="riskofbiasmetric", options={"ordering": ("domain", "sort_order")},
        ),
        migrations.RunPython(set_default_sort_order, reverse_code=migrations.RunPython.noop),
    ]
