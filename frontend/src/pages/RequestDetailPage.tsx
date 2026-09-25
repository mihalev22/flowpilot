import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { requestsApi, servicesApi } from '../services/api'
import type { RequestStatus } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import {
  confidenceLabel,
  formatDateTime,
  IntentBadge,
  SOURCE_LABELS,
  STATUS_LABELS,
  StatusBadge,
} from '../components/badges'
import { ErrorState, Skeleton, SkeletonTable } from '../components/states'

const selectClass =
  'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'

export default function RequestDetailPage() {
  const { id } = useParams()
  const requestId = Number(id)
  const { show } = useToast()
  const queryClient = useQueryClient()

  const { data: request, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => requestsApi.get(requestId),
    enabled: Number.isFinite(requestId) && requestId > 0,
  })

  const { data: services } = useQuery({
    queryKey: ['services'],
    queryFn: servicesApi.list,
  })

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof requestsApi.update>[1]) =>
      requestsApi.update(requestId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', requestId] })
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      show('Изменения сохранены', 'success')
    },
    onError: (err) => {
      show(err instanceof Error ? err.message : 'Не удалось сохранить изменения', 'error')
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 rounded-xl" />
        <SkeletonTable rows={4} cols={3} />
      </div>
    )
  }

  if (isError || !request) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Не удалось загрузить заявку'}
        onRetry={refetch}
      />
    )
  }

  const ai = request.latest_ai

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/requests" className="text-sm text-slate-500 hover:text-slate-700">
          ← К списку
        </Link>
        <h1 className="text-2xl font-semibold text-slate-900">Заявка №{request.id}</h1>
        <StatusBadge status={request.status} />
        {request.requires_manual_review && (
          <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
            Требует ручной проверки
          </span>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">Обработка</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <label htmlFor="status" className="text-sm font-medium text-slate-700">
                  Статус
                </label>
                <select
                  id="status"
                  value={request.status}
                  disabled={updateMutation.isPending}
                  onChange={(event) =>
                    updateMutation.mutate({ status: event.target.value as RequestStatus })
                  }
                  className={`${selectClass} w-full`}
                >
                  {(Object.keys(STATUS_LABELS) as RequestStatus[]).map((value) => (
                    <option key={value} value={value}>
                      {STATUS_LABELS[value]}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label htmlFor="service" className="text-sm font-medium text-slate-700">
                  Услуга
                </label>
                <select
                  id="service"
                  value={request.service_id ?? 0}
                  disabled={updateMutation.isPending}
                  onChange={(event) =>
                    updateMutation.mutate({
                      service_id: Number(event.target.value) || null,
                    })
                  }
                  className={`${selectClass} w-full`}
                >
                  <option value={0}>Не определена</option>
                  {services?.map((service) => (
                    <option key={service.id} value={service.id}>
                      {service.name}
                      {service.price ? ` — ${service.price} ₽` : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {request.requires_manual_review && (
              <button
                type="button"
                disabled={updateMutation.isPending}
                onClick={() => updateMutation.mutate({ requires_manual_review: false })}
                className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100"
              >
                Снять флаг ручной проверки
              </button>
            )}
          </div>

          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">Клиент</h2>
            <Link
              to={`/clients/${request.client_id}`}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
              {request.client?.name ?? `Клиент №${request.client_id}`}
            </Link>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-slate-500">Телефон</dt>
              <dd className="text-slate-900">{request.client?.phone ?? '—'}</dd>
              <dt className="text-slate-500">Telegram ID</dt>
              <dd className="text-slate-900">{request.client?.telegram_user_id ?? '—'}</dd>
            </dl>
          </div>

          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">Детали</h2>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-slate-500">Источник</dt>
              <dd className="text-slate-900">{SOURCE_LABELS[request.source]}</dd>
              <dt className="text-slate-500">Создана</dt>
              <dd className="text-slate-900">{formatDateTime(request.created_at)}</dd>
              <dt className="text-slate-500">Желаемая дата</dt>
              <dd className="text-slate-900">{request.preferred_date ?? '—'}</dd>
              <dt className="text-slate-500">Желаемое время</dt>
              <dd className="text-slate-900">{request.preferred_time ?? '—'}</dd>
            </dl>
            {request.summary && (
              <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{request.summary}</p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">AI-анализ</h2>
            {ai ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <IntentBadge intent={ai.intent} />
                  <span className="text-sm text-slate-600">{confidenceLabel(ai.confidence)}</span>
                </div>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <dt className="text-slate-500">Услуга</dt>
                  <dd className="text-slate-900">{ai.service_name ?? '—'}</dd>
                  <dt className="text-slate-500">Дата</dt>
                  <dd className="text-slate-900">{ai.preferred_date ?? '—'}</dd>
                  <dt className="text-slate-500">Время</dt>
                  <dd className="text-slate-900">{ai.preferred_time ?? '—'}</dd>
                </dl>
                <p className="text-xs text-slate-400">
                  Confidence — внутренний сигнал качества модели, не калиброванная вероятность.
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Анализ ещё не выполнялся</p>
            )}
          </div>

          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">Сообщения</h2>
            <ul className="space-y-3">
              {request.messages.map((message) => (
                <li key={message.id} className="rounded-lg bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">
                    {SOURCE_LABELS[message.source]} · {formatDateTime(message.created_at)}
                  </p>
                  <p className="mt-1 text-sm text-slate-900">{message.text}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-semibold text-slate-900">История статусов</h2>
            {request.status_history.length === 0 ? (
              <p className="text-sm text-slate-500">Статус не менялся</p>
            ) : (
              <ul className="space-y-2">
                {request.status_history.map((record) => (
                  <li key={record.id} className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="text-slate-600">
                      {record.old_status ? STATUS_LABELS[record.old_status] : '—'}
                    </span>
                    <span className="text-slate-400">→</span>
                    <StatusBadge status={record.new_status} />
                    <span className="ml-auto text-xs text-slate-500">
                      {formatDateTime(record.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
