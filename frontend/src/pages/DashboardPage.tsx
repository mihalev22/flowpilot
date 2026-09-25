import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { dashboardApi } from '../services/api'
import { formatDateTime, IntentBadge, StatusBadge } from '../components/badges'
import { EmptyState, ErrorState, Skeleton, SkeletonCards } from '../components/states'

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['stats'],
    queryFn: dashboardApi.stats,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-slate-900">Дашборд</h1>
        <SkeletonCards count={5} />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Не удалось загрузить статистику'}
        onRetry={refetch}
      />
    )
  }

  const cards = [
    { label: 'Требуют проверки', value: data.requires_review, accent: 'text-amber-600' },
    { label: 'Новые', value: data.status_counts.new, accent: 'text-blue-600' },
    { label: 'В работе', value: data.status_counts.in_progress, accent: 'text-amber-600' },
    { label: 'Подтверждено', value: data.status_counts.confirmed, accent: 'text-indigo-600' },
    { label: 'Завершено', value: data.status_counts.completed, accent: 'text-emerald-600' },
    { label: 'Всего', value: data.total, accent: 'text-slate-900' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Дашборд</h1>
        <Link
          to="/requests"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Все заявки
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className={`mt-1 text-3xl font-semibold ${card.accent}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">Последние обращения</h2>
        </div>
        {data.recent_requests.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="Обращений пока нет"
              description="Заявки появятся здесь после подключения Telegram-бота или веб-формы"
            />
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {data.recent_requests.map((request) => (
              <li key={request.id}>
                <Link
                  to={`/requests/${request.id}`}
                  className="flex flex-wrap items-center gap-3 px-5 py-3 hover:bg-slate-50"
                >
                  <span className="text-sm text-slate-500">№{request.id}</span>
                  <span className="text-sm font-medium text-slate-900">
                    {request.client?.name ?? 'Клиент'}
                  </span>
                  {request.latest_ai && <IntentBadge intent={request.latest_ai.intent} />}
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
