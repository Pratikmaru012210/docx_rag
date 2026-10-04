import os
from typing import List, Dict, Any
import docx
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table

from backend.parser.table_serializer import TableSerializer
from backend.config import settings


class HierarchicalDocxParser:
    """
    Parses DOCX documents with sequential reading order, heading breadcrumbs,
    and structured markdown table serialization.
    """

    def __init__(self, max_chunk_words: int = None, overlap_words: int = None):
        """Set chunk sizing options, falling back to the application configuration."""
        self.max_chunk_words = max_chunk_words or settings.MAX_CHUNK_WORDS
        self.overlap_words = overlap_words or settings.CHUNK_OVERLAP_WORDS

    def parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Extracts elements in raw XML sequential order while tracking active heading breadcrumbs."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = docx.Document(file_path)
        doc_name = os.path.basename(file_path)
        doc_title = os.path.splitext(doc_name)[0]

        elements: List[Dict[str, Any]] = []
        heading_stack: Dict[int, str] = {}

        for child in doc.element.body:
            if isinstance(child, CT_P):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if not text:
                    continue

                style_name = p.style.name.lower() if p.style else ""

                if "title" in style_name:
                    doc_title = text
                    heading_stack.clear()
                    heading_stack[0] = text
                    elements.append({
                        "type": "title",
                        "content": text,
                        "breadcrumb": text,
                        "doc_name": doc_name
                    })
                elif "heading 1" in style_name:
                    heading_stack = {k: v for k, v in heading_stack.items() if k < 1}
                    heading_stack[1] = text
                    elements.append({
                        "type": "heading",
                        "heading_level": 1,
                        "content": text,
                        "breadcrumb": self._format_breadcrumb(doc_title, heading_stack),
                        "doc_name": doc_name
                    })
                elif "heading 2" in style_name:
                    heading_stack = {k: v for k, v in heading_stack.items() if k < 2}
                    heading_stack[2] = text
                    elements.append({
                        "type": "heading",
                        "heading_level": 2,
                        "content": text,
                        "breadcrumb": self._format_breadcrumb(doc_title, heading_stack),
                        "doc_name": doc_name
                    })
                elif "heading 3" in style_name:
                    heading_stack = {k: v for k, v in heading_stack.items() if k < 3}
                    heading_stack[3] = text
                    elements.append({
                        "type": "heading",
                        "heading_level": 3,
                        "content": text,
                        "breadcrumb": self._format_breadcrumb(doc_title, heading_stack),
                        "doc_name": doc_name
                    })
                else:
                    breadcrumb = self._format_breadcrumb(doc_title, heading_stack)
                    elements.append({
                        "type": "paragraph",
                        "content": text,
                        "breadcrumb": breadcrumb,
                        "doc_name": doc_name
                    })

            elif isinstance(child, CT_Tbl):
                table = Table(child, doc)
                md_table = TableSerializer.to_markdown(table)
                if md_table:
                    breadcrumb = self._format_breadcrumb(doc_title, heading_stack)
                    elements.append({
                        "type": "table",
                        "content": md_table,
                        "breadcrumb": breadcrumb,
                        "doc_name": doc_name
                    })

        return elements

    def _format_breadcrumb(self, doc_title: str, heading_stack: Dict[int, str]) -> str:
        """Combine the document title and active headings into a readable section path."""
        parts = []
        if doc_title:
            parts.append(doc_title)
        for lvl in sorted(heading_stack.keys()):
            val = heading_stack[lvl]
            if val and val != doc_title and val not in parts:
                parts.append(val)
        return " > ".join(parts) if parts else "General"

    def create_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """Creates context-enriched chunks with breadcrumbs prepended to each chunk."""
        elements = self.parse_document(file_path)
        doc_name = os.path.basename(file_path)
        chunks: List[Dict[str, Any]] = []

        current_text_buffer = []
        current_breadcrumb = ""
        current_word_count = 0
        chunk_index = 0

        def flush_buffer():
            """Emit the buffered paragraphs as one chunk and reset its word count."""
            nonlocal chunk_index, current_text_buffer, current_breadcrumb, current_word_count
            if not current_text_buffer:
                return

            body_text = "\n\n".join(current_text_buffer)
            enriched_text = f"**Document Hierarchy:** {current_breadcrumb}\n\n{body_text}"

            chunks.append({
                "chunk_id": f"{doc_name}_chunk_{chunk_index:04d}",
                "doc_name": doc_name,
                "breadcrumb": current_breadcrumb,
                "content_type": "text",
                "text": enriched_text,
                "raw_content": body_text,
                "word_count": len(enriched_text.split())
            })
            chunk_index += 1
            current_text_buffer = []
            current_word_count = 0

        for el in elements:
            el_type = el["type"]
            content = el["content"]
            breadcrumb = el["breadcrumb"]

            # Split at substantial section changes so a chunk does not mix unrelated headings.
            if current_breadcrumb and breadcrumb != current_breadcrumb and current_word_count > (self.max_chunk_words // 2):
                flush_buffer()

            current_breadcrumb = breadcrumb

            if el_type == "table":
                # Keep tables intact as individual chunks rather than splitting their rows.
                flush_buffer()
                enriched_table_text = f"**Document Hierarchy:** {breadcrumb}\n**Table Context:**\n\n{content}"
                chunks.append({
                    "chunk_id": f"{doc_name}_chunk_{chunk_index:04d}",
                    "doc_name": doc_name,
                    "breadcrumb": breadcrumb,
                    "content_type": "table",
                    "text": enriched_table_text,
                    "raw_content": content,
                    "word_count": len(enriched_table_text.split())
                })
                chunk_index += 1

            elif el_type in ["heading", "title"]:
                if current_word_count > self.max_chunk_words:
                    flush_buffer()
                current_text_buffer.append(f"### {content}")
                current_word_count += len(content.split())

            else:
                words = len(content.split())
                if current_word_count + words > self.max_chunk_words:
                    # Paragraphs remain whole; flush first when the next one would exceed the limit.
                    flush_buffer()
                current_text_buffer.append(content)
                current_word_count += words

        flush_buffer()
        return chunks
