import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { MagnifyingGlass, ArrowRight, Buildings } from '@phosphor-icons/react'
import { api, readableError, type CanonicalSummary } from '../api'
import { Card, SectionTitle, NmcTag, OrgChip, DemoNote } from '../components/ui'

/**
 * 06 — Standardization explorer.
 *
 * The screen that shows this is a catalogue rather than a single matcher.
 * Sorted by how many organisations hold each material, because that ordering
 * is the actual finding: the materials at the top are where harmonisation is
 * worth the most.
 */
export function Explorer() {
  const [q, setQ] = useState('')
  const [rows, setRows] = useState<CanonicalSummary[]>([])
  const [meta, setMeta] = useState({ total: 0, matched: 0 })
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const t = setTimeout(() => {
      api.canonicalList(q, 30)
        .then((d) => { setRows(d.results); setMeta({ total: d.total, matched: d.matched }) })
        .catch((e) => setErr(readableError(e)))
    }, q ? 180 : 0)          // debounce typing, but load immediately on mount
    return () => clearTimeout(t)
  }, [q])

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-[24px] font-bold tracking-[-0.015em] mb-1">Standardized materials</h1>
        <p className="text-[14px] text-[var(--color-text-2)]">
          {meta.total.toLocaleString()} canonical materials, each holding the source codes of every
          organisation that described it.
        </p>
      </div>

      <Card className="flex items-center gap-2 px-3.5 py-1" spotlight>
        <MagnifyingGlass size={16} weight="bold" aria-hidden="true" style={{ color: 'var(--color-text-3)' }} />
        <label htmlFor="ex" className="sr-only">Search materials</label>
        <input
          id="ex" value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Search by description, item type or NMC id"
          autoComplete="off"
          className="flex-1 bg-transparent py-3 text-[14px] outline-none placeholder:text-[var(--color-text-3)]"
        />
        {q && (
          <span className="mono text-[12px] text-[var(--color-text-3)] whitespace-nowrap">
            {meta.matched.toLocaleString()} found
          </span>
        )}
      </Card>

      {err && (
        <p role="alert" className="rounded-lg border px-4 py-3 text-[13.5px]"
           style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)', color: 'var(--color-distinct)' }}>
          {err}
        </p>
      )}

      <SectionTitle hint="most widely held first">Results</SectionTitle>

      <ul className="list-none m-0 p-0 grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
        {rows.map((r, i) => (
          <motion.li key={r.nmc_id}
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: Math.min(0.03 * i, 0.3), ease: [0.23, 1, 0.32, 1] }}>
            <Link to={`/platform/material/${r.nmc_id}`} className="block h-full">
              <Card interactive spotlight className="p-4 h-full flex flex-col">
                <div className="flex items-start justify-between gap-2 mb-2.5">
                  <NmcTag id={r.nmc_id} size="sm" />
                  <ArrowRight size={14} weight="bold" aria-hidden="true"
                              style={{ color: 'var(--color-text-3)' }} />
                </div>
                <p className="text-[14px] font-semibold leading-snug">{r.item_name}</p>
                <p className="mono text-[12px] text-[var(--color-text-2)] mt-1 leading-snug flex-1">
                  {r.canonical_text}
                </p>
                <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-[var(--color-line)]">
                  <span className="flex items-center gap-1">
                    {r.orgs.map((o) => <OrgChip key={o} org={o} />)}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11.5px] text-[var(--color-text-3)]">
                    <Buildings size={12} weight="fill" aria-hidden="true" />
                    {r.source_count} records
                  </span>
                </div>
              </Card>
            </Link>
          </motion.li>
        ))}
      </ul>

      {rows.length === 0 && !err && (
        <Card className="p-8 text-center">
          <p className="text-[14px] font-medium">No materials match &ldquo;{q}&rdquo;</p>
          <p className="text-[13px] text-[var(--color-text-3)] mt-1">
            Try a broader term such as BOLT, VALVE or BEARING.
          </p>
        </Card>
      )}

      <DemoNote>
        Demonstration corpus. Canonical identifiers are opaque and derived deterministically, so
        the same corpus always produces the same identifiers.
      </DemoNote>
    </div>
  )
}
