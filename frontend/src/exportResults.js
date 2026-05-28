function escapeCsv(value) {
  const normalized = value == null ? '' : String(value)
  if (!/[",\n]/.test(normalized)) {
    return normalized
  }

  return `"${normalized.replaceAll('"', '""')}"`
}

export function buildJsonExport(results) {
  return `${JSON.stringify(results, null, 2)}\n`
}

export function buildCsvExport(results) {
  const rows = [
    ['acronym', 'definition', 'count', 'first_page', 'pages', 'examples'],
    ...results.map((result) => [
      result.acronym,
      result.definition ?? '',
      result.count,
      result.first_page ?? '',
      result.pages.join('; '),
      result.examples.join(' | '),
    ]),
  ]

  return `${rows.map((row) => row.map(escapeCsv).join(',')).join('\n')}\n`
}

function triggerDownload(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function downloadResultsAsJson(results, filename) {
  triggerDownload(filename, buildJsonExport(results), 'application/json;charset=utf-8')
}

export function downloadResultsAsCsv(results, filename) {
  triggerDownload(filename, buildCsvExport(results), 'text/csv;charset=utf-8')
}
