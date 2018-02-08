from django.core.management.base import BaseCommand
from django.db import transaction, connection

from datetime import timedelta

# How long should we keep logs?
LOG_KEEP_DAYS=300

class Command(BaseCommand):
	help = "Delete old logs"

	def handle(self, *args, **options):
		with transaction.atomic():
			curs = connection.cursor()
			curs.execute("DELETE FROM aggregatorlog WHERE success AND ts < NOW()-%(age)s", {
				'age': timedelta(LOG_KEEP_DAYS),
			})
