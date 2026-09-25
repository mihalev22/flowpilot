import type { Intent, MessageSource, RequestStatus } from '../services/api'

export const STATUS_LABELS: Record<RequestStatus, string> = {
  NEW: 'Новая',
  IN_PROGRESS: 'В работе',
  CONFIRMED: 'Подтверждена',
  COMPLETED: 'Завершена',
  CANCELLED: 'Отменена',
}

const STATUS_STYLES: Record<RequestStatus, string> = {
  NEW: 'bg-blue-50 text-blue-700 ring-blue-200',
  IN_PROGRESS: 'bg-amber-50 text-amber-700 ring-amber-200',
  CONFIRMED: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
  COMPLETED: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  CANCELLED: 'bg-slate-100 text-slate-600 ring-slate-300',
}

export function StatusBadge({ status }: { status: RequestStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}

export const INTENT_LABELS: Record<Intent, string> = {
  booking: 'Запись',
  question: 'Вопрос',
  complaint: 'Жалоба',
  price_request: 'Запрос цены',
  cancel_booking: 'Отмена записи',
  reschedule: 'Перенос',
  other: 'Другое',
}

const INTENT_STYLES: Record<Intent, string> = {
  booking: 'bg-blue-50 text-blue-700 ring-blue-200',
  question: 'bg-slate-100 text-slate-700 ring-slate-300',
  complaint: 'bg-red-50 text-red-700 ring-red-200',
  price_request: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  cancel_booking: 'bg-slate-100 text-slate-600 ring-slate-300',
  reschedule: 'bg-amber-50 text-amber-700 ring-amber-200',
  other: 'bg-slate-100 text-slate-500 ring-slate-300',
}

export function IntentBadge({ intent }: { intent: Intent }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${INTENT_STYLES[intent]}`}
    >
      {INTENT_LABELS[intent]}
    </span>
  )
}

export const SOURCE_LABELS: Record<MessageSource, string> = {
  telegram: 'Telegram',
  web: 'Веб-форма',
  manual: 'Вручную',
}

export function formatDateTime(value: string): string {
  const date = new Date(value)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDate(value: string): string {
  const date = new Date(value)
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function confidenceLabel(confidence: number): string {
  if (confidence >= 0.85) {
    return `Высокая (${Math.round(confidence * 100)}%)`
  }
  if (confidence >= 0.6) {
    return `Средняя (${Math.round(confidence * 100)}%)`
  }
  return `Низкая (${Math.round(confidence * 100)}%)`
}
