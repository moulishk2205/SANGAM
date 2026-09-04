import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowsMerge, Info, Download } from '@phosphor-icons/react'
import {
  procurement, integration, ApiError,
  type ProcurementSummary, type AggregationReport, type AggregationGroup,
} from '../api'
import { Card, SectionTitle, DemoNote, StatTile, OrgChip, NmcTag } from '../components/ui'
import { StatRowSkeleton, ListSkeleton } from '../components/Skeleton'

/* ══════════════════════════════════════════════════════════════════════════
   Procurement analytics.

   This is the screen where harmonisation stops being a data-quality exercise
   and turns into money. Everything above it proves two CPSEs hold the same or
   interchangeable material; this counts what that is worth.

   THE NUMBER ON THIS SCREEN IS DELIBERATELY CONSERVATIVE

   "Estimated procurement opportunity" is arithmetic over observed facts only:
   for each buyer in an equivalence group, quantity x (what they paid - the
   lowest unit price anyone in the group actually paid). No discount is assumed,
   no saving is promised, and the basis is printed next to the figure so it can
   be checked. A modelled percentage would be a larger number and an indefensible
   one.

   The service-class selector is not a filter for convenience. Changing it
   changes which substitutions the equivalence layer will allow, and SOUR and
   FIRED return nothing at all — the layer refuses to rule there. That an
   analytics screen can return "no opportunities" for a safety class is the
   point, not a gap.
   ══════════════════════════════════════════════════════════════════════════ */

const SERVICE_CLASSES = ['GENERAL', 'PRESSURE', 'SOUR', 'FIRED'] as const

const inr = (n: number) =>
  n >= 1e7 ? `₹${(n / 1e7).toFixed(2)} cr`
    : n >= 1e5 ? `₹${(n / 1e5).toFixed(2)} L`
      : `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

const inrExact = (n: number) =>
  `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`

export function Procurement() {
  const [sum, setSum] = useState<ProcurementSummary | null>(null)
  const [agg, setAgg] = useState<AggregationReport | null>(null)
  const [svc, setSvc] = useState<string>('GENERAL')
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)
  const [open, setOpen] = useState<string | null>(null)

  const load = useCallback((serviceClass: string) => {
    setLoading(true)
    Promise.all([procurement.summary(), procurement.aggregation(serviceClass, 25)])
      .then(([s, a]) => { setSum(s); setAgg(a); setErr(null) })
      .catch((e) => setErr(e instanceof ApiError ? e.message : String(e)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load(svc) }, [load, svc])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: [0.23, 1, 0.32, 1] }}
      className="grid gap-6"
    >
      <section aria-labelledby="proc-h">
        <h1 id="proc-h" className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-[-0.02em] leading-tight">
          Procurement analytics
        </h1>
        <p className="mt-2 text-[14px] text-[var(--color-text-2)] max-w-[68ch] leading-relaxed">
          Historical purchase lines, grouped by canonical identity and then widened
          by functional equivalence. Two CPSEs holding interchangeable materials can
          be served by one tender — this counts how much of that exists and what it
          is worth at prices already paid.
        </p>
      </section>

      {err && (
        <Card className="p-4">
          <p role="alert" className="text-[13.5px]" style={{ color: 'var(--color-distinct)' }}>{err}</p>
        </Card>
      )}

      {loading && !sum && <StatRowSkeleton />}

      {sum && (
        <section aria-label="Procurement figures">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatTile value={sum.lines.toLocaleString('en-IN')} label="Purchase lines"
                      note={sum.window.from
                        ? `${sum.window.from.slice(0, 7)} to ${sum.window.to?.slice(0, 7)}`
                        : 'no history'} />
            <StatTile value={inr(sum.spend)} label="Historical spend"
                      note="sum of line values" />
            <StatTile value={String(sum.materials_with_history)} label="Materials with history"
                      note="canonical identities purchased" />
            <StatTile value={String(sum.materials_bought_by_multiple_cpses)}
                      label="Bought by 2+ CPSEs"
                      note="already-identical demand" />
          </div>
        </section>
      )}

      {/* ── service class ─────────────────────────────────────────────── */}
      <section aria-labelledby="svc-h">
        <SectionTitle hint={agg ? `${agg.groups_examined} groups examined` : undefined}>
          <span id="svc-h">Service class</span>
        </SectionTitle>
        <div className="flex flex-wrap gap-2">
          {SERVICE_CLASSES.map((s) => (
            <button
              key={s}
              onClick={() => setSvc(s)}
              aria-pressed={svc === s}
              className="press rounded-[var(--radius-control)] border px-3.5 py-2 text-[12.5px] font-semibold cursor-pointer"
              style={svc === s
                ? { background: 'var(--color-brand)', color: 'var(--color-on-brand)',
                    borderColor: 'transparent' }
                : { background: 'var(--color-surface)', color: 'var(--color-text-2)',
                    borderColor: 'var(--color-line-strong)' }}
            >
              {s}
            </button>
          ))}
        </div>
        <p className="mt-2.5 text-[12.5px] text-[var(--color-text-3)] max-w-[70ch] leading-relaxed">
          The class decides which substitutions are permitted, not merely which rows
          are shown. In SOUR service NACE MR0175 constrains materials by hardness and
          composition, and in FIRED service OISD-STD-150 governs — the equivalence
          layer refuses to rule on either, so no group widens and no opportunity is
          claimed.
        </p>
      </section>

      {loading && <ListSkeleton rows={4} />}

      {/* ── the headline ──────────────────────────────────────────────── */}
      {!loading && agg && (
        <Card className="p-5" style={{
          background: agg.aggregation_opportunities
            ? 'var(--color-brand-ambient)' : 'var(--color-neutral-ambient)',
        }}>
          <div className="flex items-start gap-3">
            <ArrowsMerge size={18} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0"
                         style={{ color: agg.aggregation_opportunities
                           ? 'var(--color-brand)' : 'var(--color-text-3)' }} />
            <div className="min-w-0">
              {agg.aggregation_opportunities ? (
                <>
                  <p className="text-[15px] font-semibold" style={{ color: 'var(--color-brand)' }}>
                    {agg.aggregation_opportunities} aggregation {agg.aggregation_opportunities === 1
                      ? 'opportunity' : 'opportunities'} in {agg.service_class} service
                  </p>
                  <p className="text-[13px] text-[var(--color-text-2)] mt-1.5">
                    {agg.total_aggregatable_quantity.toLocaleString('en-IN')} units of
                    combinable demand · estimated procurement opportunity{' '}
                    <strong className="font-semibold text-[var(--color-text)]">
                      {inrExact(agg.total_estimated_opportunity)}
                    </strong>
                  </p>
                </>
              ) : (
                <>
                  <p className="text-[15px] font-semibold text-[var(--color-text)]">
                    No aggregation opportunity in {agg.service_class} service
                  </p>
                  <p className="text-[13px] text-[var(--color-text-2)] mt-1.5">
                    {agg.note}
                  </p>
                </>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* ── the groups ────────────────────────────────────────────────── */}
      {!loading && agg && agg.groups.length > 0 && (
        <section aria-labelledby="grp-h">
          <SectionTitle hint="highest opportunity first">
            <span id="grp-h">Aggregation groups</span>
          </SectionTitle>
          <div className="grid gap-3">
            {agg.groups.map((g) => (
              <GroupCard key={g.key} g={g}
                         open={open === g.key}
                         onToggle={() => setOpen(open === g.key ? null : g.key)} />
            ))}
          </div>
        </section>
      )}

      {/* ── export ────────────────────────────────────────────────────── */}
      <section aria-labelledby="exp-h">
        <SectionTitle><span id="exp-h">Export</span></SectionTitle>
        <Card className="p-5">
          <p className="text-[13px] text-[var(--color-text-2)] max-w-[66ch] leading-relaxed">
            The unified material master in the declared export schema. Every row keeps
            the CPSE's original code, so it loads as a cross-reference rather than as a
            replacement.
          </p>
          <a href={integration.exportUnifiedUrl()}
             className="press mt-3.5 inline-flex items-center gap-2 rounded-[var(--radius-control)]
                        border border-[var(--color-line-strong)] bg-[var(--color-surface)]
                        px-3.5 py-2 text-[13px] font-medium text-[var(--color-text)]
                        hover:bg-[var(--color-surface-2)]">
            <Download size={14} weight="bold" aria-hidden="true" />
            Download unified master (CSV)
          </a>
        </Card>
      </section>

      <DemoNote>
        {sum?.provenance ?? 'Demonstration data.'} Prices are indicative demonstration
        figures. "Estimated procurement opportunity" is the sum over buyers of quantity ×
        (price paid − lowest price observed in the same equivalence group). It assumes no
        discount and promises no saving.
      </DemoNote>
    </motion.div>
  )
}

function GroupCard({ g, open, onToggle }:
                   { g: AggregationGroup; open: boolean; onToggle: () => void }) {
  return (
    <Card spotlight className="p-4 md:p-5">
      <button onClick={onToggle}
              aria-expanded={open}
              className="press w-full text-left cursor-pointer">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              {g.organisations.map((o) => <OrgChip key={o} org={o} />)}
              <span className="text-[11px] text-[var(--color-text-3)]">
                {g.identities} distinct identities
              </span>
            </div>
            <p className="text-[13.5px] font-medium text-[var(--color-text)] mt-2">
              {g.members[0]?.standard_description}
            </p>
            <p className="text-[12px] text-[var(--color-text-3)] mt-1">
              covering material <NmcTag id={g.covering_material} size="sm" />
            </p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-[17px] font-bold tabular-nums" style={{ color: 'var(--color-brand)' }}>
              {inrExact(g.estimated_opportunity)}
            </p>
            <p className="text-[10.5px] text-[var(--color-text-3)]">estimated opportunity</p>
            <p className="text-[11.5px] text-[var(--color-text-2)] mt-1.5 tabular-nums">
              {g.aggregatable_quantity.toLocaleString('en-IN')} units · {inr(g.combined_spend)}
            </p>
          </div>
        </div>
      </button>

      {open && (
        <div className="mt-4 pt-4 border-t border-[var(--color-line)] grid gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-2">
              Identities in this group
            </p>
            <div className="grid gap-2">
              {g.members.map((m) => (
                <div key={m.canonical_id}
                     className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-control)]
                                bg-[var(--color-surface-2)] px-3 py-2.5">
                  <div className="min-w-0">
                    <Link to={`/platform/material/${m.canonical_id}`} className="link mono text-[12px]">
                      {m.canonical_id}
                    </Link>
                    <p className="text-[12.5px] text-[var(--color-text-2)] mt-0.5">
                      {m.standard_description}
                    </p>
                  </div>
                  <p className="mono text-[12px] text-[var(--color-text-2)] shrink-0 tabular-nums">
                    {m.quantity.toLocaleString('en-IN')} {m.uom} @ ₹{m.avg_unit_price.toLocaleString('en-IN')}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {g.rationale.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-text-3)] mb-2">
                Why these may be combined
              </p>
              {g.rationale.map((r, i) => (
                <p key={i} className="text-[12.5px] text-[var(--color-text-2)] leading-relaxed">
                  {r.summary}
                </p>
              ))}
            </div>
          )}

          <p className="flex items-start gap-2 text-[11.5px] text-[var(--color-text-3)] leading-relaxed">
            <Info size={12} weight="fill" aria-hidden="true" className="mt-0.5 shrink-0" />
            {g.basis} Best observed unit price in this group: ₹{g.best_observed_unit_price.toLocaleString('en-IN')}.
          </p>
        </div>
      )}
    </Card>
  )
}
