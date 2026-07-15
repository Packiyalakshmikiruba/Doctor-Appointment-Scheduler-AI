from django.core.management.base import BaseCommand
from django.core.management import call_command
from chatbot.rag_tool import build_vectorstore


class Command(BaseCommand):
    help = "Extracts DB data to text AND rebuilds the FAISS vector index in one step"

    def handle(self, *args, **kwargs):
        call_command("build_knowledge_base")
        build_vectorstore()
        self.stdout.write(self.style.SUCCESS("Knowledge base + vector index rebuilt."))