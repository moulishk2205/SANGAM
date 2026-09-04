import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowLeft, Buildings } from '@phosphor-icons/react'
import {
  api, readableError, standardise,
  type CanonicalDetail, type EquivalenceReport,
} from '../api'
import { Card, SectionTitle, NmcTag, OrgChip, DemoNote } from '../components/ui'
import { DetailSkeleton } from '../components/Skeleton'

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
  const [equiv, setEquiv] = useState<EquivalenceReport | null>(null)
  const [svc, setSvc] = useState('GENERAL')
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!nmc) return
    setRec(null); setErr(null)
    api.canonical(nmc).then(setRec).catch((e) => setErr(readableError(e)))
  }, [nmc])

  // Equivalence is fetched separately and is allowed to fail quietly: it is
  // additional context, and a material page that 500s because a substitution
  // scan timed out would be worse than one without the panel.
  useEffect(() => {
    if (!nmc) return
    setEquiv(null)
    standardise.equivalents(nmc, svc).then(setEquiv).catch(() => setEquiv(null))
  }, [nmc, svc])

  if (err) return (
    <p role="alert" className="rounded-lg border px-4 py-3 text-[13px]"
       style={{ background: 'var(--color-distinct-soft)', borderColor: 'var(--color-distinct-line)', color: 'var(--color-distinct)' }}>
      {err}
    </p>
  )
  if (!rec) return <DetailSkeleton />

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
          {/* The generated national description leads; the indexed canonical
              text follows as provenance. Before this, the description shown here
              was whichever member record sorted first — one CPSE's house style
              promoted to national status by accident. */}
          <p className="mt-3 text-[15px] font-semibold text-[var(--color-text)] leading-snug">
            {rec.standard_description || rec.canonical_text}
          </p>
          <p className="text-[11px] uppercase tracking-[0.06em] text-[var(--color-text-3)] mt-1">
            Standard description — generated from the canonical attributes
          </p>
          {rec.standard_description && rec.standard_description !== rec.canonical_text && (
            <p className="mono mt-2.5 text-[12.5px] text-[var(--color-text-3)]">
              indexed as: {rec.canonical_text}
            </p>
          )}
        </motion.div>
      </div>

      {rec.code_breakdown && !rec.code_breakdown.legacy && (
        <section aria-labelledby="code-h">
          <SectionTitle hint={rec.code_breakdown.valid ? 'check character verified' : 'invalid'}>
            <span id="code-h">What the national code says</span>
          </SectionTitle>
          <Card className="p-4 md:p-5">
            <div className="flex flex-wrap gap-2.5">
              {rec.code_breakdown.segments.map((sg) => (
                <div key={sg.label}
                     className="rounded-[var(--radius-control)] bg-[var(--color-surface-2)] px-3 py-2.5 min-w-[8rem]">
                  <p className="text-[10.5px] uppercase tracking-[0.06em] text-[var(--color-text-3)]">
                    {sg.label}
                  </p>
                  <p className="mono text-[15px] font-bold text-[var(--color-text)] mt-0.5">{sg.value}</p>
                  <p className="text-[11.5px] text-[var(--color-text-2)] mt-1 max-w-[16rem]">{sg.meaning}</p>
                  {sg.note && (
                    <p className="text-[10.5px] text-[var(--color-text-3)] mt-0.5">{sg.note}</p>
                  )}
                </div>
              ))}
            </div>
            <p className="text-[12px] text-[var(--color-text-3)] mt-3 max-w-[72ch] leading-relaxed">
              Readable without a database lookup, which is what a code on a printed
              indent has to be. The FSC segment is a real NATO Federal Supply
              Classification — the same class spine India's National Codification
              Bureau already uses for defence items.
            </p>
          </Card>
        </section>
      )}

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
                  <dd className="mono m-0 text-[13px] font-medium">{a.value}</dd>
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
                    <span className="mono text-[12px] font-semibold" style={{ color: 'var(--color-info)' }}>
                      {s.org_code}
                    </span>
                  </div>
                  <p className="mono text-[12px] text-[var(--color-text-2)] pl-[1.35rem]">{s.description}</p>
                </motion.li>
              ))}
            </ul>
          </Card>
          <p className="mt-2.5 text-[12px] text-[var(--color-text-2)]">
            Every organisation keeps its own code. The canonical identity is an additional layer,
            never a replacement, and the mapping is reversible.
          </p>
        </section>
      </div>

      {equiv && (
        <section aria-labelledby="equiv-h">
          <SectionTitle hint={`${equiv.scanned} in family scanned`}>
            <span id="equiv-h">Functional equivalence</span>
          </SectionTitle>

          <div className="flex flex-wrap gap-2 mb-3">
            {['GENERAL', 'PRESSURE', 'SOUR', 'FIRED'].map((c) => (
              <button key={c} onClick={() => setSvc(c)} aria-pressed={svc === c}
                      className="press rounded-[var(--radius-control)] border px-3 py-1.5 text-[12px] font-semibold cursor-pointer"
                      style={svc === c
                        ? { background: 'var(--color-brand)', color: 'var(--color-on-brand)', borderColor: 'transparent' }
                        : { background: 'var(--color-surface)', color: 'var(--color-text-2)', borderColor: 'var(--color-line-strong)' }}>
                {c}
              </button>
            ))}
          </div>

          {equiv.functionally_equivalent.length === 0 && equiv.undetermined.length === 0 && (
            <Card className="p-5">
              <p className="text-[13px] text-[var(--color-text-2)]">
                Nothing in this family can substitute for this material in {svc} service.
                That is a result, not a gap — equivalence is never inferred from
                dimensional similarity.
              </p>
            </Card>
          )}

          {equiv.functionally_equivalent.length > 0 && (
            <Card className="overflow-hidden">
              {equiv.functionally_equivalent.map((e) => (
                <div key={e.id} className="px-4 py-3.5 border-b border-[var(--color-line)] last:border-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <Link to={`/platform/material/${e.id}`} className="link mono text-[12.5px]">{e.id}</Link>
                      <p className="text-[13px] text-[var(--color-text)] mt-1">{e.description}</p>
                    </div>
                    <span className="shrink-0 rounded-full px-2.5 py-1 text-[10.5px] font-semibold"
                          style={{ background: 'var(--color-brand-soft)', color: 'var(--color-brand)' }}>
                      AGGREGATABLE
                    </span>
                  </div>
                  <p className="text-[12px] text-[var(--color-text-2)] mt-2 leading-relaxed">{e.summary}</p>
                  {e.deltas.filter((d) => d.kind === 'substitutable').map((d) => (
                    <p key={d.code} className="mono text-[11.5px] text-[var(--color-text-3)] mt-1">
                      {d.code}: {d.left} vs {d.right} — {d.reason}
                    </p>
                  ))}
                </div>
              ))}
            </Card>
          )}

          {equiv.undetermined.length > 0 && (
            <Card className="p-4 mt-3" style={{ background: 'var(--color-unknown-soft)' }}>
              <p className="text-[12.5px] font-semibold" style={{ color: 'var(--color-unknown)' }}>
                {equiv.undetermined.length} candidate{equiv.undetermined.length === 1 ? '' : 's'} not ruled on
              </p>
              <p className="text-[12px] mt-1 leading-relaxed" style={{ color: 'var(--color-unknown)' }}>
                {equiv.undetermined[0].summary}
              </p>
            </Card>
          )}

          <p className="text-[12px] text-[var(--color-text-3)] mt-3 max-w-[72ch] leading-relaxed">
            {equiv.note}
          </p>
        </section>
      )}

      <DemoNote>
        Records are synthetic surface descriptions generated over a real catalogue structure.
        Organisation names and codes are invented for demonstration.
      </DemoNote>
    </div>
  )
}
