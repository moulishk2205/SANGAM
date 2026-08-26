import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowLeft, Buildings, ArrowRight } from '@phosphor-icons/react'
import { api, readableError, type CanonicalDetail } from '../api'
import { Card, SectionTitle, NmcTag, OrgChip, DemoNote } from '../components/ui'

/**
 * 05 — Canonical material identity.
 *
 * The screen the problem statement is actually about. Finding duplicates is
 * the easy half; the requirement is a standardized identity that keeps
 * traceability to every originating organisation's own code. So the source
 * list is not a footnote here, it is the second half of the record, and the
 * codes are rendered at full weight rather than as metadata.
 */
export function Canonical() {
  const { nmc } = useParams()
  const [rec, setRec] = useState<CanonicalDetail | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!nmc) return
    setRec(null); setErr(null)
    api.canonical(nmc).then(setRec).catch((e) => setErr(readableError(e)))
  }, [nmc])

  if (err) return (
    <p role="alert" className="rounded-lg border px-4 py-3 text-[13.5px]"
       style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)', color: 'var(--color-distinct)' }}>
      {err}
    </p>
  )
  if (!rec) return <p className="text-[14px] text-[var(--color-text-3)]">Loading record…</p>

  return (
    <div className="grid gap-6">
      <div>
        <Link to="/platform/explorer" className="press link inline-flex items-center gap-1.5 text-[13px] font-medium mb-4">
          <ArrowLeft size={13} weight="bold" aria-hidden="true" /> All materials
        </Link>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.36, ease: [0.23, 1, 0.32, 1] }}>
          <NmcTag id={rec.nmc_id} />
          <h1 className="mt-3 text-[clamp(1.5rem,3vw,2.1rem)] font-bold tracking-[-0.015em] leading-tight">
            {rec.item_name}
          </h1>
          <p className="mono mt-1.5 text-[14px] text-[var(--color-text-2)]">{rec.canonical_text}</p>
        </motion.div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* canonical attributes */}
        <section aria-labelledby="attrs">
          <SectionTitle><span id="attrs">Canonical attributes</span></SectionTitle>
          <Card className="overflow-hidden">
            <dl className="m-0">
              {rec.attributes.map((a, i) => (
                <motion.div key={a.code}
                  initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.28, delay: 0.04 * i, ease: [0.23, 1, 0.32, 1] }}
                  className="row grid grid-cols-[10rem_1fr] gap-4 px-4 py-3 border-b border-[var(--color-line)] last:border-0">
                  <dt className="text-[13px] text-[var(--color-text-3)]">{a.label}</dt>
                  <dd className="mono m-0 text-[13.5px] font-medium">{a.value}</dd>
                </motion.div>
              ))}
            </dl>
          </Card>
        </section>

        {/* source traceability */}
        <section aria-labelledby="trace">
          <SectionTitle hint={`${rec.source_count} records · ${rec.org_count} organisations`}>
            <span id="trace">Source traceability</span>
          </SectionTitle>
          <Card className="overflow-hidden">
            <ul className="list-none m-0 p-0">
              {rec.sources.map((s, i) => (
                <motion.li key={s.record_id}
                  initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.28, delay: 0.04 * i, ease: [0.23, 1, 0.32, 1] }}
                  className="row px-4 py-3 border-b border-[var(--color-line)] last:border-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Buildings size={13} weight="fill" aria-hidden="true" style={{ color: 'var(--color-text-3)' }} />
                    <OrgChip org={s.org} />
                    <span className="mono text-[12.5px] font-semibold" style={{ color: 'var(--color-info)' }}>
                      {s.org_code}
                    </span>
                  </div>
                  <p className="mono text-[12.5px] text-[var(--color-text-2)] pl-[1.35rem]">{s.description}</p>
                </motion.li>
              ))}
            </ul>
          </Card>
          <p className="mt-2.5 text-[12.5px] text-[var(--color-text-2)]">
            Every organisation keeps its own code. The canonical identity is an additional layer,
            never a replacement, and the mapping is reversible.
          </p>
        </section>
      </div>

      <DemoNote>
        Records are synthetic surface descriptions generated over a real catalogue structure.
        Organisation names and codes are invented for demonstration.
      </DemoNote>
    </div>
  )
}
