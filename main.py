import hashlib
import re
import uuid
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider  # Note: Nlp, not NLP
from presidio_anonymizer import AnonymizerEngine

# Configure Presidio to use the lightweight SpaCy model
provider = NlpEngineProvider(
    nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
)

nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()

# Test run
results = analyzer.analyze(
    text="My name is John Doe and email is john@example.com", language="en"
)
print(results)