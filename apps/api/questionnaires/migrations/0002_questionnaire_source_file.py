from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("questionnaires", "0001_initial")]
    operations = [
        migrations.AddField(model_name="questionnaire", name="processing_status", field=models.CharField(default="QUEUED", max_length=20)),
        migrations.AddField(model_name="questionnaire", name="processing_error", field=models.CharField(blank=True, max_length=240)),
        migrations.AddField(model_name="questionnaire", name="source_file", field=models.FileField(blank=True, upload_to="questionnaires/%Y/%m/")),
        migrations.AddField(model_name="questionnaire", name="original_filename", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="questionnaire", name="file_hash", field=models.CharField(blank=True, max_length=64)),
    ]
