import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { clientsApi } from '../services/api'
import { formatDateTime, formatDate, IntentBadge, StatusBadge } from '../components/badges'
import { EmptyState, ErrorState, Skeleton, SkeletonTable } from '../components/states'

export default function ClientDetailPage() {
  const { id } = useParams()
  const clientId = Number(id)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => clientsApi.get(clientId),
    enabled: Number.isFinite(clientId) && clientId > 0,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 rounded-xl" />
        <SkeletonTable rows={5} cols={4} />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Не удалось загрузить клиента'}
        onRetry={refetch}
      />
    )
  }

  const { client, requests } = data

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/clients" className="text-sm text-slate-500 hover:text-slate-700">
          ← К списку
        </Link>
        <h1 className="text-2xl font-semibold text-slate-900">{client.name}</h1>
      </div>

      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-900">Информация</h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <dt className="text-slate-500">Телефон</dt>
          <dd className="text-slate-900">{client.phone ?? '—'}</dd>
          <dt className="text-slate-500">Email</dt>
          <dd className="text-slate-900">{client.email ?? '—'}</dd>
          <dt className="text-slate-500">Telegram ID</dt>
          <dd className="text-slate-900">{client.telegram_user_id ?? '—'}</dd>
          <dt className="text-slate-500">Добавлен</dt>
          <dd className="text-slate-900">{formatDate(client.created_at)}</dd>
          {client.notes && (
            <>
              <dt className="text-slate-500">Заметки</dt>
              <dd className="text-slate-900">{client.notes}</dd>
            </>
          )}
        </dl>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">
            История обращений ({requests.length})
          </h2>
        </div>
        {requests.length === 0 ? (
          <div className="p-5">
            <EmptyState title="Обращений пока нет" />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {requests.map((request) => (
              <li key={request.id}>
                <Link
                  to={`/requests/${request.id}`}
                  className="flex flex-wrap items-center gap-3 px-5 py-3 hover:bg-slate-50"
                >
                  <span className="text-sm text-slate-500">№{request.id}</span>
                  {request.latest_ai && <IntentBadge intent={request.latest_ai.intent} />}
                  <span className="text-sm text-slate-600">
                    {request.service_name ?? 'Услуга не определена'}
                  </span>
                  <span className="ml-auto flex items-center gap-3">
                    <span className="text-xs text-slate-500">
                      {formatDateTime(request.created_at)}
                    </span>
                    <StatusBadge status={request.status} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
