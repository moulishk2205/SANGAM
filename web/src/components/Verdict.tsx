import { Check, X, Question } from '@phosphor-icons/react'
import type { Verdict as V } from '../lib/content'

/**
 * A verdict mark.
 *
 * Three signals, always: a glyph, a word, and a colour. Colour is the third
 * signal and never the only one, so the table stays readable without colour
 * vision and in a printed or screen-read context.
 */
export function VerdictMark({ verdict, showWord = true }: { verdict: V; showWord?: boolean }) {
  const map = {
    agree:    { Icon: Check,    word: 'AGREE',    cls: 'text-live' },
    disagree: { Icon: X,        word: 'DISAGREE', cls: 'text-cut' },
    unknown:  { Icon: Question, word: 'UNKNOWN',  cls: 'text-mist' },
  } as const
  const { Icon, word, cls } = map[verdict]
  return (
    <span className={`inline-flex items-center gap-2 ${cls}`}>
      <Icon size={15} weight="bold" aria-hidden="true" />
      {showWord && <span className="t-label">{word}</span>}
      <span className="visually-hidden">{word}</span>
    </span>
  )
}
