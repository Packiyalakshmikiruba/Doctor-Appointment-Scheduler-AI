"""
Runs the full appointment automation pipeline in order:
Reminder -> Auto Confirmation -> Auto No-Show

Run: python manage.py run_automation
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Run the full appointment automation pipeline"

    def handle(self, *args, **kwargs):
        self.stdout.write("=== Step 1: Sending Reminders ===")
        call_command("send_reminders")

        self.stdout.write("\n=== Step 2: Auto-Confirming ===")
        call_command("auto_confirm")

        self.stdout.write("\n=== Step 3: Auto No-Show Detection ===")
        call_command("auto_noshow")

        self.stdout.write(self.style.SUCCESS("\nAutomation pipeline complete."))