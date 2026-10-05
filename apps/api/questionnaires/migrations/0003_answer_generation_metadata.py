from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("questionnaires", "0002_questionnaire_source_file")]
    operations = [
        migrations.AddField(model_name="answerdraft", name="generated_by_model", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="answerdraft", name="prompt_version", field=models.CharField(blank=True, max_length=40)),
    ]
