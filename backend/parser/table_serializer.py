from docx.table import Table


class TableSerializer:
    """Specialized serializer converting docx.table.Table objects into GitHub-Flavored Markdown."""

    @staticmethod
    def to_markdown(table: Table) -> str:
        rows = table.rows
        if not rows:
            return ""

        md_rows = []
        for i, row in enumerate(rows):
            cell_texts = []
            for cell in row.cells:
                # Clean cell text, escape markdown pipes, replace linebreaks with spaces
                cleaned = cell.text.strip().replace("\n", " ").replace("|", "\\|")
                cell_texts.append(cleaned)

            md_row = "| " + " | ".join(cell_texts) + " |"
            md_rows.append(md_row)

            # Insert markdown header separator line after the 1st (header) row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
                md_rows.append(separator)

        return "\n".join(md_rows)
