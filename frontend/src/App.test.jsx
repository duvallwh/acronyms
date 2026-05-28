import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { downloadResultsAsCsv, downloadResultsAsJson } from './exportResults'

vi.mock('./exportResults', async () => {
  const actual = await vi.importActual('./exportResults')
  return {
    ...actual,
    downloadResultsAsCsv: vi.fn(),
    downloadResultsAsJson: vi.fn(),
  }
})

const sampleResults = [
  {
    acronym: 'NASA',
    definition: 'National Aeronautics and Space Administration',
    count: 2,
    first_page: 1,
    pages: [1, 3],
    examples: ['National Aeronautics and Space Administration (NASA)'],
  },
]

describe('App', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(sampleResults),
      }),
    )
  })

  it('uploads a PDF and renders extracted results', async () => {
    const user = userEvent.setup()

    render(<App />)

    await user.upload(screen.getByLabelText(/choose a pdf/i), new File(['pdf'], 'paper.pdf', { type: 'application/pdf' }))
    await user.click(screen.getByRole('button', { name: /extract acronyms/i }))

    await screen.findByText('Extraction complete.')
    expect(fetch).toHaveBeenCalledWith(
      '/api/extract',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      }),
    )
    expect(screen.getAllByText('NASA').length).toBeGreaterThan(0)
    expect(screen.getByDisplayValue('')).toBeInTheDocument()
    expect(screen.getByText(/showing 1 of 1 acronyms from paper.pdf/i)).toBeInTheDocument()
  })

  it('filters results and triggers JSON and CSV downloads', async () => {
    const user = userEvent.setup()

    render(<App />)

    await user.upload(screen.getByLabelText(/choose a pdf/i), new File(['pdf'], 'paper.pdf', { type: 'application/pdf' }))
    await user.click(screen.getByRole('button', { name: /extract acronyms/i }))
    await screen.findByText('Extraction complete.')

    await user.type(screen.getByPlaceholderText(/search acronym/i), 'missing')
    expect(screen.getByText(/no results match the current filter/i)).toBeInTheDocument()

    await user.clear(screen.getByPlaceholderText(/search acronym/i))
    await waitFor(() => expect(screen.getAllByText('NASA').length).toBeGreaterThan(0))

    await user.click(screen.getByRole('button', { name: /download json/i }))
    await user.click(screen.getByRole('button', { name: /download csv/i }))

    expect(downloadResultsAsJson).toHaveBeenCalledWith(sampleResults, 'paper.json')
    expect(downloadResultsAsCsv).toHaveBeenCalledWith(sampleResults, 'paper.csv')
  })

  it('shows API errors', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: 'Please upload a PDF file.' }),
    })

    const user = userEvent.setup()
    render(<App />)

    await user.upload(screen.getByLabelText(/choose a pdf/i), new File(['oops'], 'notes.txt', { type: 'text/plain' }))
    await user.click(screen.getByRole('button', { name: /extract acronyms/i }))

    await screen.findByText('Please upload a PDF file.')
  })
})
