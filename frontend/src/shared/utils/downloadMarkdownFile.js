export function downloadMarkdownFile(filename, content) {
  const element = document.createElement('a');
  const file = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(file);

  element.href = url;
  element.download = filename.endsWith('.md') ? filename : `${filename}.md`;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
  URL.revokeObjectURL(url);
}
