import os
from typing import List, Dict, Any, Optional
import docx
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table


class HierarchicalDocxParser:
    """
    Parses DOCX documents while preserving:
    1. Sequential reading order (paragraphs and tables interwoven in order)
    2. Heading hierarchy (Breadcrumb: Doc > H1 > H2 > H3)
    3. Tabular semantics (converted to structured Markdown with row integrity)
    4. Enriched contextual chunks (every chunk includes its section breadcrumb)
    """

    def __init__(self, max_chunk_words: int = 400, overlap_words: int = 50):
        self.max_chunk_words = max_chunk_words
        self.overlap_words = overlap_words

    def table_to_markdown(self, table: Table) -> str:
        """Convert a docx Table to clean Markdown table representation."""
        rows = table.rows
        if not rows:
            return ""

        md_rows = []
        for i, row in enumerate(rows):
            cell_texts = []
            for cell in row.cells:
                # Clean cell text, replace internal newlines with space or <br>
                cleaned = cell.text.strip().replace("\n", " ")
                cleaned = cleaned.replace("|", "\\|")  # Escape markdown pipes
                cell_texts.append(cleaned)
            
            md_row = "| " + " | ".join(cell_texts) + " |"
            md_rows.append(md_row)

            # Insert markdown header separator after the first row (header row)
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
                md_rows.append(separator)

        return "\n".join(md_rows)

    def parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts all structured elements in sequential order, maintaining active breadcrumbs.
        Returns a list of elements:
        [
            {
                "type": "paragraph" | "table" | "heading",
                "content": str,
                "breadcrumb": str,
                "heading_level": int (if heading),
                "doc_name": str
            }
        ]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = docx.Document(file_path)
        doc_name = os.path.basename(file_path)

        elements: List[Dict[str, Any]] = []
        heading_stack: Dict[int, str] = {}  # level -> heading text
        doc_title = os.path.splitext(doc_name)[0]

        # Traverse body elements in raw XML order
        for child in doc.element.body:
            if isinstance(child, CT_P):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if not text:
                    continue

                style_name = p.style.name.lower() if p.style else ""

                # Detect headings
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
                    # Clear deeper levels
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
                    # Normal paragraph or list item
                    breadcrumb = self._format_breadcrumb(doc_title, heading_stack)
                    elements.append({
                        "type": "paragraph",
                        "content": text,
                        "breadcrumb": breadcrumb,
                        "doc_name": doc_name
                    })

            elif isinstance(child, CT_Tbl):
                table = Table(child, doc)
                md_table = self.table_to_markdown(table)
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
        parts = []
        if doc_title:
            parts.append(doc_title)
        for lvl in sorted(heading_stack.keys()):
            val = heading_stack[lvl]
            if val and val != doc_title and val not in parts:
                parts.append(val)
        return " > ".join(parts) if parts else "General"

    def create_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Creates context-enriched chunks from the document elements.
        - Preserves table atomicity whenever possible.
        - Attaches breadcrumb path at the top of each chunk.
        - Adds chunk metadata for vector search & retrieval citations.
        """
        elements = self.parse_document(file_path)
        doc_name = os.path.basename(file_path)
        chunks: List[Dict[str, Any]] = []

        current_text_buffer = []
        current_breadcrumb = ""
        current_word_count = 0
        chunk_index = 0

        def flush_buffer():
            nonlocal chunk_index, current_text_buffer, current_breadcrumb, current_word_count
            if not current_text_buffer:
                return
            
            body_text = "\n\n".join(current_text_buffer)
            # Prepend breadcrumb context header to make the chunk self-contained
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

            # If section changed significantly, flush existing buffer
            if current_breadcrumb and breadcrumb != current_breadcrumb and current_word_count > (self.max_chunk_words // 2):
                flush_buffer()

            current_breadcrumb = breadcrumb

            if el_type == "table":
                # Flush existing paragraph buffer first so table is cleanly isolated or enriched
                flush_buffer()
                
                # Tables get dedicated chunks enriched with section breadcrumb
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
                # Headings are buffer cues
                if current_word_count > self.max_chunk_words:
                    flush_buffer()
                current_text_buffer.append(f"### {content}")
                current_word_count += len(content.split())

            else:
                words = len(content.split())
                if current_word_count + words > self.max_chunk_words:
                    flush_buffer()
                current_text_buffer.append(content)
                current_word_count += words

        # Flush any remaining items
        flush_buffer()
        return chunks


if __name__ == "__main__":
    # Test parser directly on the SOP document
    import sys
    test_file = r"data/Standard Operating Procedure (SOP) - End-to-End FMCG Shampoo Supply Chain & Operations (Dove Model).docx"
    if os.path.exists(test_file):
        parser = HierarchicalDocxParser()
        result_chunks = parser.create_chunks(test_file)
        print(f"Successfully generated {len(result_chunks)} chunks.")
        for c in result_chunks[:3]:
            print("="*60)
            print(f"ID: {c['chunk_id']} | Type: {c['content_type']}")
            print(f"Breadcrumb: {c['breadcrumb']}")
            print(f"Text Preview:\n{c['text'][:200]}...")
