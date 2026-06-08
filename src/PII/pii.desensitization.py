"""
# Example code to utlize Microsoft Presidio package for PII detection and desensitization.

## Dependencyies:
! pip install presidio-analyzer presidio-anonymizer

## Execution sample:
! python -m spacy download en_core_web_lg

```

spaCy is an open-source software library for advanced natural language processing, 
written in the programming languages Python and Cython.

```

## Sample output:

原文: Hi, I'm John Smith, my email is john@example.com and SSN is 123-45-6789.
脱敏: Hi, I'm <PERSON>, my email is <EMAIL_ADDRESS> and SSN is <US_SSN>.

原文: Call me at +1-800-555-0199, I live at 123 Main St, Seattle WA 98101.
脱敏: Call me at <PHONE_NUMBER>, I live at <LOCATION>.

## Fuerther improvement:
Presidio 默认识别 PERSON、EMAIL、PHONE、SSN、CREDIT_CARD、LOCATION 等 20+ 
实体类型，底层用 spaCy NER + 正则双引擎。如需自定义实体或替换策略（如用假名
替换而非标签），可以扩展 RecognizerRegistry 和 OperatorConfig。

"""


from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer, anonymizer = AnalyzerEngine(), AnonymizerEngine()

texts = [
    "Hi, I'm John Smith, my email is john@example.com and SSN is 123-45-6789.",
    "Call me at +1-800-555-0199, I live at 123 Main St, Seattle WA 98101.",
]

for text in texts:
    results = analyzer.analyze(text=text, language="en")
    cleaned = anonymizer.anonymize(text=text, analyzer_results=results)
    print(f"原文: {text}\n脱敏: {cleaned.text}\n")


