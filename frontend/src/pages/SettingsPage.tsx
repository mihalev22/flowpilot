import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '../services/api'
import { ErrorState, Skeleton } from '../components/states'

function StatusDot({ set }: { set: boolean }) {
  return (
    <span
      className={`inline-flex size-2.5 rounded-full ${set ? 'bg-emerald-500' : 'bg-slate-300'}`}
      aria-hidden="true"
    />
  )
}

export default function SettingsPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-slate-900">Настройки</h1>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Не удалось загрузить настройки'}
        onRetry={refetch}
      />
    )
  }

  const providerLabel =
    data.ai_provider === 'mock'
      ? 'Mock (демо-режим, без API-ключа)'
      : data.ai_provider === 'openai'
        ? 'OpenAI'
        : data.ai_provider === 'qwen'
          ? 'Qwen'
          : data.ai_provider

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Настройки</h1>

      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-900">Интеграции</h2>
        <dl className="divide-y divide-slate-100">
          <div className="flex items-center justify-between py-3">
            <div>
              <dt className="text-sm font-medium text-slate-900">AI-провайдер</dt>
              <dd className="text-sm text-slate-500">{providerLabel}</dd>
            </div>
          </div>
          <div className="flex items-center justify-between py-3">
            <dt className="text-sm font-medium text-slate-900">AI API-ключ</dt>
            <dd className="flex items-center gap-2 text-sm text-slate-600">
              <StatusDot set={data.ai_key_set} />
              {data.ai_key_set ? 'задан' : 'не задан'}
            </dd>
          </div>
          <div className="flex items-center justify-between py-3">
            <dt className="text-sm font-medium text-slate-900">Telegram-бот (токен)</dt>
            <dd className="flex items-center gap-2 text-sm text-slate-600">
              <StatusDot set={data.telegram_bot_token_set} />
              {data.telegram_bot_token_set ? 'задан' : 'не задан'}
            </dd>
          </div>
          <div className="flex items-center justify-between py-3">
            <dt className="text-sm font-medium text-slate-900">Секрет Telegram-вебхука</dt>
            <dd className="flex items-center gap-2 text-sm text-slate-600">
              <StatusDot set={data.telegram_webhook_secret_set} />
              {data.telegram_webhook_secret_set ? 'задан' : 'не задан'}
            </dd>
          </div>
        </dl>
      </div>

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
        <p>
          Значения ключей задаются в файле <code className="rounded bg-amber-100 px-1">.env</code>{' '}
          backend-сервера (переменные <code className="rounded bg-amber-100 px-1">AI_API_KEY</code>,{' '}
          <code className="rounded bg-amber-100 px-1">AI_PROVIDER</code>,{' '}
          <code className="rounded bg-amber-100 px-1">TELEGRAM_BOT_TOKEN</code>,{' '}
          <code className="rounded bg-amber-100 px-1">TELEGRAM_WEBHOOK_SECRET</code>). После
          изменения — перезапуск backend. Сами значения никогда не возвращаются API, только статус
          «задан / не задан».
        </p>
      </div>
    </div>
  )
}
