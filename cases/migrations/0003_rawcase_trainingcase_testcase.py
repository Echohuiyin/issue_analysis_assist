# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_alter_kernelcase_options_kernelcase_answers_count_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RawCase',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('raw_content', models.TextField(help_text='爬取到的原始HTML或文本内容', verbose_name='原始内容')),
                ('source', models.CharField(default='', help_text='stackoverflow, csdn, zhihu等', max_length=50, verbose_name='来源')),
                ('source_url', models.URLField(blank=True, default='', verbose_name='原始URL')),
                ('source_id', models.CharField(blank=True, default='', max_length=100, verbose_name='源站ID')),
                ('fetched_at', models.DateTimeField(auto_now_add=True, verbose_name='爬取时间')),
                ('processed', models.BooleanField(default=False, verbose_name='是否已处理')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
            ],
            options={
                'verbose_name': '原始案例',
                'verbose_name_plural': '原始案例',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='TrainingCase',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500, verbose_name='标题')),
                ('phenomenon', models.TextField(default='', verbose_name='问题现象')),
                ('key_logs', models.TextField(default='', verbose_name='关键日志')),
                ('environment', models.TextField(default='', verbose_name='环境信息')),
                ('root_cause', models.TextField(default='', verbose_name='根本原因')),
                ('analysis_process', models.TextField(default='', verbose_name='分析过程')),
                ('solution', models.TextField(default='', verbose_name='解决方案')),
                ('related_code', models.TextField(blank=True, default='', verbose_name='相关代码')),
                ('fix_code', models.TextField(blank=True, default='', verbose_name='修复代码')),
                ('module', models.CharField(choices=[('memory', 'Memory Management'), ('network', 'Network'), ('scheduler', 'Scheduler'), ('lock', 'Lock/Synchronization'), ('timer', 'Timer'), ('storage', 'Storage/Filesystem'), ('irq', 'Interrupt'), ('driver', 'Device Driver'), ('other', 'Other')], default='other', max_length=50, verbose_name='内核模块')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='标签')),
                ('source', models.CharField(default='', max_length=50, verbose_name='来源')),
                ('source_url', models.URLField(blank=True, default='', verbose_name='原始URL')),
                ('quality_score', models.FloatField(default=0.0, verbose_name='质量分数')),
                ('confidence', models.FloatField(default=0.0, verbose_name='置信度')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('raw_case', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cases.rawcase', verbose_name='原始案例')),
            ],
            options={
                'verbose_name': '训练集案例',
                'verbose_name_plural': '训练集案例',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500, verbose_name='标题')),
                ('phenomenon', models.TextField(default='', verbose_name='问题现象')),
                ('key_logs', models.TextField(default='', verbose_name='关键日志')),
                ('environment', models.TextField(default='', verbose_name='环境信息')),
                ('root_cause', models.TextField(default='', verbose_name='根本原因')),
                ('analysis_process', models.TextField(default='', verbose_name='分析过程')),
                ('solution', models.TextField(default='', verbose_name='解决方案')),
                ('related_code', models.TextField(blank=True, default='', verbose_name='相关代码')),
                ('fix_code', models.TextField(blank=True, default='', verbose_name='修复代码')),
                ('module', models.CharField(choices=[('memory', 'Memory Management'), ('network', 'Network'), ('scheduler', 'Scheduler'), ('lock', 'Lock/Synchronization'), ('timer', 'Timer'), ('storage', 'Storage/Filesystem'), ('irq', 'Interrupt'), ('driver', 'Device Driver'), ('other', 'Other')], default='other', max_length=50, verbose_name='内核模块')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='标签')),
                ('source', models.CharField(default='', max_length=50, verbose_name='来源')),
                ('source_url', models.URLField(blank=True, default='', verbose_name='原始URL')),
                ('quality_score', models.FloatField(default=0.0, verbose_name='质量分数')),
                ('confidence', models.FloatField(default=0.0, verbose_name='置信度')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('raw_case', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cases.rawcase', verbose_name='原始案例')),
            ],
            options={
                'verbose_name': '测试集案例',
                'verbose_name_plural': '测试集案例',
                'ordering': ['id'],
            },
        ),
    ]