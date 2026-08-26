import { Check, X, Question, Prohibit } from '@phosphor-icons/react'
import type { Candidate, EvidenceRow, Verdict } from './api'

/**
 * The evidence table.
 *
 * Every value here is computed by the engine. Nothing is narrated, nothing is
 * rounded for effect, and the detail string ("differs by 25.0 mm, tolerance
 * 0.5 mm") is the engine's own words.
 *
 * Verdicts carry a glyph, a word and a colour. Colour is the third signal and
 * never the only one, so the table survives colour-blindness, a projector with
 * poor colour, and a screen reader.
 */

const VERDICT = {
  AGREE:    { Icon: Check,    word: 'Agree',    cls: 'text-live' },
  DISAGREE: { Icon: X,        word: 'Disagree', cls: 'text-cut' },
  UNKNOWN:  { Icon: Question, word: 'Unknown',  cls: 'text-mist' },
} as const

function Mark({ verdict }: { verdict: Verdict }) {
  const { Icon, word, cls } = VERDICT[verdict]
  return (
    <span className={`inline-flex items-center gap-1.5 ${cls}`}>
      <Icon size={13} weight="bold" aria-hidden="true" />
      <span className="t-datum text-[11px]">{word}</span>
    </span>
  )
}

export function EvidenceTable({ rows }: { rows: EvidenceRow[] }) {
  return (
    <div className="overflow-x-auto">
    <table className="w-full border-collapse text-left min-w-[30rem]">
      <caption className="visually-hidden">
        Attribute by attribute comparison between the queried material and this candidate.
      </caption>
      <thead>
        <tr>
          {['Attribute', 'Query', 'Candidate', 'Result'].map((h, i) => (
            <th
              key={h}
              scope="col"
              className={`t-datum text-[10px] uppercase tracking-[0.12em] text-graphite
                          pb-2 font-normal ${i === 3 ? 'text-right' : ''}`}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr
            key={r.code}
            className={`border-t border-[var(--color-line-soft)] align-top
                        ${r.vetoed ? 'bg-cut/[0.07]' : ''}`}
          >
            <th scope="row" className="t-datum text-[12px] text-mist py-2.5 pr-4 font-normal whitespace-nowrap">
              {r.attribute}
              {r.criticality === 'CRITICAL' && (
                <span className="ml-2 text-[9px] tracking-[0.1em] text-graphite align-middle">CRIT</span>
              )}
            </th>
            <td className="t-datum text-[12px] text-paper py-2.5 pr-4">{r.source}</td>
            <td className={`t-datum text-[12px] py-2.5 pr-4 ${r.vetoed ? 'text-cut' : 'text-paper'}`}>
              {r.candidate}
            </td>
            <td className="py-2.5 text-right whitespace-nowrap">
              <Mark verdict={r.verdict} />
              {r.detail && r.verdict !== 'AGREE' && (
                <span className="block t-datum text-[10px] text-graphite mt-0.5">{r.detail}</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  )
}

/**
 * The verdict block.
 *
 * A vetoed candidate states its score as 0.000 and names the attribute that
 * killed it. Showing the rejection with its reason is more persuasive than
 * hiding it, which is why vetoed candidates are returned and rendered rather
 * than filtered out.
 */
export function VerdictSummary({ c }: { c: Candidate }) {
  const vetoed = c.critical_veto
  return (
    <div className="grid sm:grid-cols-[1fr_auto] gap-6 items-end pt-4">
      <div>
        <p className={`t-datum text-[11px] uppercase tracking-[0.14em] mb-2
                       ${vetoed ? 'text-cut' : 'text-live'}`}>
          {vetoed ? (
            <span className="inline-flex items-center gap-2">
              <Prohibit size={13} weight="bold" aria-hidden="true" />
              Vetoed on a critical attribute
            </span>
          ) : (
            'Decision'
          )}
        </p>
        <p className={`t-headline text-[clamp(1.5rem,3vw,2rem)] ${vetoed ? 'text-cut' : 'text-paper'}`}>
          {c.decision.replace('_', ' ')}
        </p>
        {c.veto_reason && (
          <p className="t-datum text-[12px] text-mist mt-2 max-w-[52ch]">{c.veto_reason}</p>
        )}
      </div>

      <dl className="grid grid-cols-3 gap-x-8 gap-y-1 m-0 text-right">
        {[
          ['Score', c.confidence.toFixed(3)],
          ['Semantic', c.semantic_score.toFixed(3)],
          ['Attributes', `${c.counts.agree}/${c.counts.agree + c.counts.disagree}`],
        ].map(([k, v]) => (
          <div key={k}>
            <dt className="t-datum text-[10px] uppercase tracking-[0.12em] text-graphite">{k}</dt>
            <dd className="t-datum tabular text-[15px] text-paper m-0 mt-0.5">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
