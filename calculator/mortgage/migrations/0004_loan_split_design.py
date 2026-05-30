# Generated migration for new loan split design

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('mortgage', '0003_savedscenario_offset_amount_and_more'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='savedscenario',
            name='annual_rate',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='loan_amount',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='loan_term_years',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='offset_amount',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='rate_type',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='repayment_amount',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='repayment_frequency',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='repayment_type',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='total_interest',
        ),
        migrations.RemoveField(
            model_name='savedscenario',
            name='total_repayment',
        ),
        migrations.AlterField(
            model_name='savedscenario',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_scenarios', to='users.user'),
        ),
        migrations.CreateModel(
            name='LoanSplit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('annual_rate', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01')), django.core.validators.MaxValueValidator(Decimal('20.00'))])),
                ('rate_type', models.CharField(choices=[('variable', 'Variable'), ('fixed', 'Fixed')], max_length=10)),
                ('repayment_type', models.CharField(choices=[('principal_and_interest', 'Principal & Interest'), ('interest_only', 'Interest Only')], max_length=25)),
                ('repayment_frequency', models.CharField(choices=[('weekly', 'Weekly'), ('fortnightly', 'Fortnightly'), ('monthly', 'Monthly')], max_length=15)),
                ('loan_term_years', models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(40)])),
                ('fixed_rate_period_years', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('revert_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01')), django.core.validators.MaxValueValidator(Decimal('20.00'))])),
                ('offset_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Offset account for variable rate loans only', max_digits=12)),
                ('repayment_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_interest', models.DecimalField(decimal_places=2, max_digits=15)),
                ('total_repayment', models.DecimalField(decimal_places=2, max_digits=15)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='splits', to='mortgage.savedscenario')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='loansplit',
            unique_together={('scenario', 'order')},
        ),
    ]
