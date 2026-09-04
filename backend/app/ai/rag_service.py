import math
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("ai.rag")


class DocumentChunk(BaseModel):
    id: str
    title: str
    content: str
    source: str
    authority: str
    document_type: str  # bulletin, sop, advisory, climatology
    date: str
    location: str
    keywords: List[str] = []


class RAGService:
    def __init__(self):
        self.corpus: List[DocumentChunk] = self._init_corpus()

    def _init_corpus(self) -> List[DocumentChunk]:
        return [
            DocumentChunk(
                id="DOC-AGRI-001",
                title="IMD District Agromet Advisory: Paddy Water Management",
                content=(
                    "For transplanted paddy at tillering to panicle initiation stage: Maintain 2-3 cm shallow standing water. "
                    "If heavy rainfall (>50 mm) or thunderstorm is forecast, temporarily halt scheduled irrigation, "
                    "drain excess ponded water, and avoid nitrogen top-dressing to prevent lodging and bacterial leaf blight."
                ),
                source="ICAR - IMD Agromet Field Unit (AMFU)",
                authority="Ministry of Earth Sciences, Govt of India",
                document_type="advisory",
                date="2026-08-15",
                location="Telangana & Andhra Pradesh",
                keywords=["paddy", "irrigation", "tillering", "drainage", "fertilizer", "field"]
            ),
            DocumentChunk(
                id="DOC-AGRI-002",
                title="Pesticide Spraying Meteorological Guidelines (PPV & FR)",
                content=(
                    "Foliar chemical spraying must only be conducted during calm wind conditions (< 15 km/h) to prevent spray drift. "
                    "Do not apply pesticides if rainfall probability exceeds 40% within the next 24 hours, as rainwash invalidates "
                    "the treatment. Spraying in temperatures above 35°C accelerates evaporation and can burn foliage."
                ),
                source="Directorate of Plant Protection, Quarantine and Storage",
                authority="Ministry of Agriculture & Farmers Welfare",
                document_type="sop",
                date="2026-07-10",
                location="All India",
                keywords=["spray", "pesticide", "chemical", "wind", "rain", "temperature", "fungicide"]
            ),
            DocumentChunk(
                id="DOC-NDMA-001",
                title="National Disaster Management Guidelines: Heatwave Action Plan",
                content=(
                    "During IMD Yellow and Orange Heatwave warnings: Municipalities must supply ORS and potable water kiosks. "
                    "Workers must avoid peak sun hours between 12:00 and 15:00. Symptoms of heat exhaustion include heavy sweating, "
                    "weakness, cold pale skin, and dizziness. Administer cool shade and fluid immediately."
                ),
                source="NDMA Heat Action Plan Guidelines",
                authority="National Disaster Management Authority",
                document_type="sop",
                date="2026-04-01",
                location="Pan India",
                keywords=["heatwave", "heat", "sun", "water", "ors", "temperature", "dehydration"]
            ),
            DocumentChunk(
                id="DOC-CYCLONE-001",
                title="Standard Operating Procedure for Coastal Cyclonic Storms",
                content=(
                    "Fishermen warning is hoisted when wind speeds reach 45 kmph. At Orange stage (Cyclone Alert), "
                    "coastal fishing operations are fully suspended. Population living in thatched huts within 5 km of coast "
                    "must be evacuated to cyclone relief shelters. Secure loose tin roofing and board up window panes."
                ),
                source="IMD Cyclone Warning Division",
                authority="India Meteorological Department",
                document_type="bulletin",
                date="2026-05-20",
                location="East and West Coast Maritime Zones",
                keywords=["cyclone", "storm", "squall", "fisherman", "sea", "evacuate", "wind"]
            )
        ]

    def search(self, query: str, top_k: int = 2) -> List[DocumentChunk]:
        """
        Retrieves top relevant contextual documents using tokenized keyword-semantic matching.
        """
        tokens = set(re.findall(r"\w+", query.lower()))
        scored = []

        for doc in self.corpus:
            doc_tokens = set(re.findall(r"\w+", (doc.title + " " + doc.content).lower()))
            # Keyword score
            score = 0
            for t in tokens:
                if t in doc_tokens:
                    score += 1.0
                if t in doc.keywords:
                    score += 2.0
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]


rag_service = RAGService()
