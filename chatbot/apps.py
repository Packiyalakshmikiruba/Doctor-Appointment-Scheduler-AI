from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    # NOTE: no ready() override here on purpose. An earlier version tried to
    # "warm up" the agent/embeddings in a background thread inside ready(),
    # but that requires importing chatbot.booking_service (which imports
    # Django models) -- and if that import is ever hoisted to module level
    # (by hand, by an IDE's "organize imports", or by copy-pasting only part
    # of the file), Django crashes on startup with AppRegistryNotReady.
    #
    # Skipping warm-up entirely removes that whole class of bug. The only
    # cost is the very first chat message being a couple of seconds slower
    # (loading the embedding model + agent for the first time) -- every
    # message after that is already fast because agent.py caches both.
