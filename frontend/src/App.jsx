import { useMemo, useState } from 'react'
import './App.css'
import { downloadResultsAsCsv, downloadResultsAsJson } from './exportResults'

function defaultExportName(filename, extension) {
  if (!filename) {
    return `acronyms${extension}`
  }

  return filename.replace(/\.[^.]+$/u, extension)
}

function matchesQuery(result, query) {
  if (!query) {
    return true
  }

  const normalizedQuery = query.toLowerCase()
  return [result.acronym, result.definition ?? '', result.examples.join(' ')]
    .join(' ')
    .toLowerCase()
    .includes(normalizedQuery)
}

function summarizeResults(results) {
  const pages = new Set(results.flatMap((result) => result.pages))
  return {
    acronyms: results.length,
    pages: pages.size,
  }
}

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [results, setResults] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [sourceFilename, setSourceFilename] = useState('')

  const filteredResults = useMemo(
    () => results.filter((result) => matchesQuery(result, query)),
    [query, results],
  )
  const summary = useMemo(() => summarizeResults(results), [results])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!selectedFile) {
      setError('Choose a PDF to extract acronyms.')
      return
    }

    setStatus('loading')
    setError('')

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error(payload?.detail ?? 'Extraction failed.')
      }

      setResults(payload)
      setSourceFilename(selectedFile.name)
      setQuery('')
      setStatus('done')
    } catch (requestError) {
      setResults([])
      setStatus('error')
      setError(requestError.message)
    }
  }

  const hasResults = results.length > 0

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">React interface for the Python extractor</p>
          <h1>Acronym Extractor</h1>
          <p className="lede">
            Upload a PDF, review extracted acronyms, and download JSON or CSV output without using the CLI.
          </p>
        </div>
        <dl className="summary-grid">
          <div>
            <dt>Acronyms</dt>
            <dd>{summary.acronyms}</dd>
          </div>
          <div>
            <dt>Pages</dt>
            <dd>{summary.pages}</dd>
          </div>
        </dl>
      </header>

      <main className="content-grid">
        <section className="panel upload-panel">
          <h2>Upload PDF</h2>
          <form className="upload-form" onSubmit={handleSubmit}>
            <label className="file-picker" htmlFor="pdf-upload">
              <span>Choose a PDF</span>
              <input
                id="pdf-upload"
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <p className="selected-file">{selectedFile ? selectedFile.name : 'No file selected yet.'}</p>
            <button type="submit" disabled={status === 'loading'}>
              {status === 'loading' ? 'Extracting…' : 'Extract acronyms'}
            </button>
          </form>
          <div className="status-area" aria-live="polite">
            {status === 'loading' && <p>Uploading PDF and extracting acronyms…</p>}
            {status === 'done' && <p>Extraction complete.</p>}
            {error && <p className="error-message">{error}</p>}
          </div>
        </section>

        <section className="panel results-panel">
          <div className="results-toolbar">
            <div>
              <h2>Results</h2>
              <p>
                {hasResults
                  ? `Showing ${filteredResults.length} of ${results.length} acronyms from ${sourceFilename}.`
                  : 'Results will appear here after a successful upload.'}
              </p>
            </div>
            <div className="actions">
              <button
                type="button"
                disabled={!hasResults}
                onClick={() => downloadResultsAsJson(results, defaultExportName(sourceFilename, '.json'))}
              >
                Download JSON
              </button>
              <button
                type="button"
                disabled={!hasResults}
                onClick={() => downloadResultsAsCsv(results, defaultExportName(sourceFilename, '.csv'))}
              >
                Download CSV
              </button>
            </div>
          </div>

          <label className="filter-field">
            <span>Filter acronyms</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search acronym, definition, or example"
              disabled={!hasResults}
            />
          </label>

          {hasResults ? (
            filteredResults.length > 0 ? (
              <>
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>Acronym</th>
                        <th>Definition</th>
                        <th>Count</th>
                        <th>First page</th>
                        <th>Pages</th>
                        <th>Examples</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredResults.map((result) => (
                        <tr key={result.acronym}>
                          <td>{result.acronym}</td>
                          <td>{result.definition || '—'}</td>
                          <td>{result.count}</td>
                          <td>{result.first_page ?? '—'}</td>
                          <td>{result.pages.join(', ')}</td>
                          <td>{result.examples.join(' | ') || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="result-cards" aria-label="Mobile results">
                  {filteredResults.map((result) => (
                    <article className="result-card" key={`${result.acronym}-card`}>
                      <div className="card-heading">
                        <h3>{result.acronym}</h3>
                        <span>{result.count} matches</span>
                      </div>
                      <p><strong>Definition:</strong> {result.definition || '—'}</p>
                      <p><strong>First page:</strong> {result.first_page ?? '—'}</p>
                      <p><strong>Pages:</strong> {result.pages.join(', ')}</p>
                      <p><strong>Examples:</strong> {result.examples.join(' | ') || '—'}</p>
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <p className="empty-state">No results match the current filter.</p>
            )
          ) : (
            <p className="empty-state">Upload a PDF to populate the results view.</p>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
