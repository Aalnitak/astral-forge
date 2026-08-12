from django.db import migrations
from django.db import models


def convert_approved_to_redeemed(apps, _schema_editor):
    reward_redemption = apps.get_model("rewards", "RewardRedemption")
    reward_redemption.objects.filter(status="approved").update(status="redeemed")


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(convert_approved_to_redeemed, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="rewardredemption",
            name="status",
            field=models.CharField(
                choices=[
                    ("requested", "Requested"),
                    ("redeemed", "Redeemed"),
                    ("rejected", "Rejected"),
                    ("fulfilled", "Fulfilled"),
                    ("canceled", "Canceled"),
                ],
                default="requested",
                max_length=16,
            ),
        ),
    ]
